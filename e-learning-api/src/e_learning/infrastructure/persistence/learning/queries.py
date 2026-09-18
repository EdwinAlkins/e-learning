"""Projections SQLAlchemy read-only pour les écrans d'apprentissage."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Sequence
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.engine import RowMapping
from sqlalchemy.ext.asyncio import AsyncSession

from e_learning.application.learning.dto import (
    ChapterProgressDTO,
    FormationProgressDTO,
    NoteDTO,
    ProgressDTO,
    VideoProgressDTO,
)
from e_learning.application.learning.queries import LearningQueryPort
from e_learning.domain.catalog.exceptions import (
    FormationNotFound,
    InvalidFormationId,
    InvalidVideoId,
)
from e_learning.domain.user.exceptions import InvalidUserId
from e_learning.infrastructure.persistence.catalog.models import (
    ChapterModel,
    FormationModel,
    VideoModel,
)
from e_learning.infrastructure.persistence.learning.models import NoteModel, ProgressModel


def _uuid(raw: str, error: Callable[[str], Exception]) -> UUID:
    try:
        return UUID(raw)
    except ValueError as exc:
        raise error(raw) from exc


class SqlAlchemyLearningQueryService(LearningQueryPort):
    """Lectures SQL directes ; les agrégats sont calculés par PostgreSQL."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_notes(self, *, user_id: str, video_id: str) -> list[NoteDTO]:
        uid = _uuid(user_id, InvalidUserId)
        vid = _uuid(video_id, InvalidVideoId)
        rows = (
            await self._session.execute(
                select(
                    NoteModel.id,
                    NoteModel.video_id,
                    NoteModel.timecode_seconds,
                    NoteModel.content,
                    NoteModel.created_at,
                )
                .where(NoteModel.user_id == uid, NoteModel.video_id == vid)
                .order_by(NoteModel.timecode_seconds)
            )
        ).all()
        return [
            NoteDTO(
                id=str(row.id),
                video_id=str(row.video_id),
                timecode=row.timecode_seconds,
                content=row.content,
                created_at=row.created_at,
            )
            for row in rows
        ]

    async def get_progress(self, *, user_id: str, video_id: str) -> ProgressDTO:
        uid = _uuid(user_id, InvalidUserId)
        vid = _uuid(video_id, InvalidVideoId)
        value = await self._session.scalar(
            select(ProgressModel.last_position_seconds).where(
                ProgressModel.user_id == uid,
                ProgressModel.video_id == vid,
            )
        )
        return ProgressDTO(last_position=float(value or 0.0))

    async def get_formation_progress(
        self, *, user_id: str, formation_id: str
    ) -> FormationProgressDTO:
        identifier = _uuid(formation_id, InvalidFormationId)
        rows = await self._progress_rows(user_id=user_id, formation_id=identifier)
        if not rows:
            raise FormationNotFound(formation_id)
        return self._assemble(rows)[str(identifier)]

    async def list_formations_progress(
        self, *, user_id: str
    ) -> dict[str, FormationProgressDTO]:
        return self._assemble(await self._progress_rows(user_id=user_id))

    async def _progress_rows(
        self, *, user_id: str, formation_id: UUID | None = None
    ) -> Sequence[RowMapping]:
        uid = _uuid(user_id, InvalidUserId)
        percentage = case(
            (
                VideoModel.duration_seconds > 0,
                func.least(
                    100.0,
                    func.greatest(
                        0.0,
                        func.coalesce(ProgressModel.last_position_seconds, 0.0)
                        / VideoModel.duration_seconds
                        * 100.0,
                    ),
                ),
            ),
            else_=0.0,
        ).label("video_percentage")

        video_progress = (
            select(
                ChapterModel.formation_id.label("formation_id"),
                ChapterModel.id.label("chapter_id"),
                VideoModel.id.label("video_id"),
                VideoModel.title.label("video_title"),
                VideoModel.position.label("video_position"),
                percentage,
            )
            .join(VideoModel, VideoModel.chapter_id == ChapterModel.id)
            .outerjoin(
                ProgressModel,
                (ProgressModel.video_id == VideoModel.id) & (ProgressModel.user_id == uid),
            )
            .cte("video_progress")
        )

        chapter_stats = (
            select(
                ChapterModel.id.label("chapter_id"),
                func.coalesce(func.avg(video_progress.c.video_percentage), 0.0).label(
                    "chapter_percentage"
                ),
            )
            .outerjoin(video_progress, video_progress.c.chapter_id == ChapterModel.id)
            .group_by(ChapterModel.id)
            .cte("chapter_stats")
        )

        formation_stats = (
            select(
                FormationModel.id.label("formation_id"),
                func.coalesce(func.avg(chapter_stats.c.chapter_percentage), 0.0).label(
                    "formation_percentage"
                ),
            )
            .outerjoin(ChapterModel, ChapterModel.formation_id == FormationModel.id)
            .outerjoin(chapter_stats, chapter_stats.c.chapter_id == ChapterModel.id)
            .group_by(FormationModel.id)
            .cte("formation_stats")
        )

        statement = (
            select(
                FormationModel.id.label("formation_id"),
                FormationModel.name.label("formation_name"),
                ChapterModel.id.label("chapter_id"),
                ChapterModel.name.label("chapter_name"),
                ChapterModel.position.label("chapter_position"),
                video_progress.c.video_id,
                video_progress.c.video_title,
                video_progress.c.video_position,
                video_progress.c.video_percentage,
                chapter_stats.c.chapter_percentage,
                formation_stats.c.formation_percentage,
            )
            .outerjoin(ChapterModel, ChapterModel.formation_id == FormationModel.id)
            .outerjoin(video_progress, video_progress.c.chapter_id == ChapterModel.id)
            .outerjoin(chapter_stats, chapter_stats.c.chapter_id == ChapterModel.id)
            .join(formation_stats, formation_stats.c.formation_id == FormationModel.id)
            .order_by(FormationModel.name, ChapterModel.position, video_progress.c.video_position)
        )
        if formation_id is not None:
            statement = statement.where(FormationModel.id == formation_id)
        return (await self._session.execute(statement)).mappings().all()

    @staticmethod
    def _assemble(rows: Sequence[RowMapping]) -> dict[str, FormationProgressDTO]:
        formation_rows: dict[str, RowMapping] = {}
        chapter_rows: dict[str, RowMapping] = {}
        videos_by_chapter: dict[str, list[VideoProgressDTO]] = defaultdict(list)

        for row in rows:
            formation_id = str(row["formation_id"])
            formation_rows.setdefault(formation_id, row)
            if row["chapter_id"] is None:
                continue
            chapter_id = str(row["chapter_id"])
            chapter_rows.setdefault(chapter_id, row)
            if row["video_id"] is not None:
                videos_by_chapter[chapter_id].append(
                    VideoProgressDTO(
                        id=str(row["video_id"]),
                        title=row["video_title"],
                        progress_percentage=float(row["video_percentage"]),
                    )
                )

        chapters_by_formation: dict[str, list[ChapterProgressDTO]] = defaultdict(list)
        for chapter_id, row in chapter_rows.items():
            chapters_by_formation[str(row["formation_id"])].append(
                ChapterProgressDTO(
                    name=row["chapter_name"],
                    videos=videos_by_chapter[chapter_id],
                    progress_percentage=float(row["chapter_percentage"]),
                )
            )

        return {
            formation_id: FormationProgressDTO(
                name=row["formation_name"],
                chapters=chapters_by_formation[formation_id],
                progress_percentage=float(row["formation_percentage"]),
            )
            for formation_id, row in formation_rows.items()
        }
