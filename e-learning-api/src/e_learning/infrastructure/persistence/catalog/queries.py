"""Projections SQLAlchemy read-only du catalogue."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.engine import RowMapping
from sqlalchemy.ext.asyncio import AsyncSession

from e_learning.application.catalog.dto import (
    ChapterDTO,
    DocumentDTO,
    FormationDTO,
    JobDTO,
    VideoDTO,
)
from e_learning.application.catalog.queries import CatalogQueryPort, CatalogVideoRow
from e_learning.domain.catalog.exceptions import (
    ChapterNotFound,
    FormationNotFound,
    InvalidChapterId,
    InvalidFormationId,
)
from e_learning.infrastructure.persistence.catalog.models import (
    ChapterModel,
    DocumentModel,
    FormationModel,
    JobModel,
    VideoModel,
)

_ACTIVE_JOB_STATUSES = ("queued", "running")


def _as_uuid(raw: str, *, kind: str) -> UUID:
    try:
        return UUID(raw)
    except ValueError as exc:
        if kind == "formation":
            raise InvalidFormationId(raw) from exc
        raise InvalidChapterId(raw) from exc


class SqlAlchemyCatalogQueryService(CatalogQueryPort):
    """SQL ciblé vers DTO simples ; aucune entité métier n'est construite."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_formations(self) -> list[FormationDTO]:
        formations = (
            (
                await self._session.execute(
                    select(
                        FormationModel.id,
                        FormationModel.name,
                        FormationModel.slug,
                    ).order_by(FormationModel.name)
                )
            )
            .mappings()
            .all()
        )
        if not formations:
            return []
        return await self._load_catalog(formations)

    async def get_formation(self, formation_id: str) -> FormationDTO:
        identifier = _as_uuid(formation_id, kind="formation")
        formation = (
            (
                await self._session.execute(
                    select(
                        FormationModel.id,
                        FormationModel.name,
                        FormationModel.slug,
                    ).where(FormationModel.id == identifier)
                )
            )
            .mappings()
            .one_or_none()
        )
        if formation is None:
            raise FormationNotFound(formation_id)
        return (await self._load_catalog([formation]))[0]

    async def list_chapter_documents(self, chapter_id: str) -> list[DocumentDTO]:
        identifier = _as_uuid(chapter_id, kind="chapter")
        rows = (
            (
                await self._session.execute(
                    select(
                        ChapterModel.id.label("chapter_id"),
                        DocumentModel.id,
                        DocumentModel.title,
                        DocumentModel.position,
                        DocumentModel.relative_path,
                        DocumentModel.filename,
                        DocumentModel.mime_type,
                        DocumentModel.video_id,
                    )
                    .outerjoin(DocumentModel, DocumentModel.chapter_id == ChapterModel.id)
                    .where(ChapterModel.id == identifier)
                    .order_by(DocumentModel.position)
                )
            )
            .mappings()
            .all()
        )
        if not rows:
            raise ChapterNotFound(chapter_id)
        return [self._document(row) for row in rows if row["id"] is not None]

    async def list_videos(self, *, formation_filter: str | None = None) -> list[CatalogVideoRow]:
        statement = (
            select(
                FormationModel.id.label("formation_id"),
                FormationModel.name.label("formation_name"),
                FormationModel.slug.label("formation_slug"),
                ChapterModel.id.label("chapter_id"),
                ChapterModel.name.label("chapter_name"),
                VideoModel.id.label("video_id"),
                VideoModel.title.label("video_title"),
                VideoModel.relative_path,
            )
            .join(ChapterModel, ChapterModel.formation_id == FormationModel.id)
            .join(VideoModel, VideoModel.chapter_id == ChapterModel.id)
            .order_by(FormationModel.name, ChapterModel.position, VideoModel.position)
        )
        if formation_filter:
            pattern = f"%{formation_filter}%"
            statement = statement.where(
                or_(FormationModel.name.ilike(pattern), FormationModel.slug.ilike(pattern))
            )
        rows = (await self._session.execute(statement)).mappings().all()
        return [
            CatalogVideoRow(
                formation_id=str(row["formation_id"]),
                formation_name=row["formation_name"],
                formation_slug=row["formation_slug"],
                chapter_id=str(row["chapter_id"]),
                chapter_name=row["chapter_name"],
                video_id=str(row["video_id"]),
                video_title=row["video_title"],
                relative_path=row["relative_path"],
            )
            for row in rows
        ]

    async def _load_catalog(self, formation_rows: Sequence[RowMapping]) -> list[FormationDTO]:
        formation_ids = [row["id"] for row in formation_rows]

        chapter_rows = (
            (
                await self._session.execute(
                    select(
                        ChapterModel.id,
                        ChapterModel.formation_id,
                        ChapterModel.name,
                        ChapterModel.slug,
                        ChapterModel.position,
                    )
                    .where(ChapterModel.formation_id.in_(formation_ids))
                    .order_by(ChapterModel.formation_id, ChapterModel.position)
                )
            )
            .mappings()
            .all()
        )

        video_rows = (
            (
                await self._session.execute(
                    select(
                        VideoModel.id,
                        VideoModel.chapter_id,
                        VideoModel.title,
                        VideoModel.duration_seconds,
                        VideoModel.position,
                        VideoModel.relative_path,
                        VideoModel.kind,
                        VideoModel.processing_status,
                        VideoModel.transcription_status,
                        VideoModel.summary_status,
                        JobModel.id.label("job_id"),
                        JobModel.kind.label("job_kind"),
                        JobModel.status.label("job_status"),
                        JobModel.progress.label("job_progress"),
                        JobModel.message.label("job_message"),
                        JobModel.formation_id.label("job_formation_id"),
                    )
                    .join(ChapterModel, VideoModel.chapter_id == ChapterModel.id)
                    .outerjoin(
                        JobModel,
                        (JobModel.video_id == VideoModel.id)
                        & JobModel.status.in_(_ACTIVE_JOB_STATUSES),
                    )
                    .where(ChapterModel.formation_id.in_(formation_ids))
                    .order_by(ChapterModel.position, VideoModel.position, JobModel.created_at)
                )
            )
            .mappings()
            .all()
        )

        document_rows = (
            (
                await self._session.execute(
                    select(
                        DocumentModel.id,
                        DocumentModel.chapter_id,
                        DocumentModel.title,
                        DocumentModel.position,
                        DocumentModel.relative_path,
                        DocumentModel.filename,
                        DocumentModel.mime_type,
                        DocumentModel.video_id,
                    )
                    .join(ChapterModel, DocumentModel.chapter_id == ChapterModel.id)
                    .where(ChapterModel.formation_id.in_(formation_ids))
                    .order_by(ChapterModel.position, DocumentModel.position)
                )
            )
            .mappings()
            .all()
        )

        jobs_by_video: dict[str, list[JobDTO]] = defaultdict(list)
        video_data: dict[str, RowMapping] = {}
        for row in video_rows:
            video_id = str(row["id"])
            video_data.setdefault(video_id, row)
            if row["job_id"] is not None:
                jobs_by_video[video_id].append(
                    JobDTO(
                        id=str(row["job_id"]),
                        kind=row["job_kind"],
                        status=row["job_status"],
                        progress=row["job_progress"],
                        message=row["job_message"],
                        video_id=video_id,
                        formation_id=(
                            str(row["job_formation_id"])
                            if row["job_formation_id"] is not None
                            else None
                        ),
                    )
                )

        videos_by_chapter: dict[str, list[VideoDTO]] = defaultdict(list)
        for video_id, row in video_data.items():
            videos_by_chapter[str(row["chapter_id"])].append(
                VideoDTO(
                    id=video_id,
                    title=row["title"],
                    duration=row["duration_seconds"],
                    position=row["position"],
                    relative_path=row["relative_path"],
                    kind=row["kind"],
                    processing_status=row["processing_status"],
                    transcription_status=row["transcription_status"],
                    summary_status=row["summary_status"],
                    active_jobs=tuple(jobs_by_video[video_id]),
                )
            )

        documents_by_chapter: dict[str, list[DocumentDTO]] = defaultdict(list)
        for row in document_rows:
            documents_by_chapter[str(row["chapter_id"])].append(self._document(row))

        chapters_by_formation: dict[str, list[ChapterDTO]] = defaultdict(list)
        for row in chapter_rows:
            chapter_id = str(row["id"])
            chapters_by_formation[str(row["formation_id"])].append(
                ChapterDTO(
                    id=chapter_id,
                    name=row["name"],
                    slug=row["slug"],
                    position=row["position"],
                    videos=videos_by_chapter[chapter_id],
                    documents=documents_by_chapter[chapter_id],
                )
            )

        return [
            FormationDTO(
                id=str(row["id"]),
                name=row["name"],
                slug=row["slug"],
                chapters=chapters_by_formation[str(row["id"])],
            )
            for row in formation_rows
        ]

    @staticmethod
    def _document(row: RowMapping) -> DocumentDTO:
        return DocumentDTO(
            id=str(row["id"]),
            title=row["title"],
            position=row["position"],
            relative_path=row["relative_path"],
            filename=row["filename"],
            mime_type=row["mime_type"],
            video_id=str(row["video_id"]) if row["video_id"] is not None else None,
        )
