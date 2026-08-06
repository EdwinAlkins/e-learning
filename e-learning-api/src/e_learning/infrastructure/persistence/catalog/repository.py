"""Adaptateurs SQLAlchemy — repositories catalog."""

from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from e_learning.domain.catalog.entities import Chapter, Document, Formation, Video
from e_learning.domain.catalog.exceptions import (
    ChapterNotFound,
    DocumentNotFound,
    FormationNotFound,
    JobNotFound,
    VideoNotFound,
)
from e_learning.domain.catalog.job import Job
from e_learning.domain.catalog.repository import (
    ChapterRepository,
    DocumentRepository,
    FormationRepository,
    JobRepository,
    VideoRepository,
)
from e_learning.domain.catalog.value_objects import (
    ChapterId,
    DocumentId,
    FormationId,
    JobId,
    RelativePath,
    VideoId,
)
from e_learning.infrastructure.persistence.catalog import mappers
from e_learning.infrastructure.persistence.catalog.models import (
    ChapterModel,
    DocumentModel,
    FormationModel,
    JobModel,
    VideoModel,
)


class SqlAlchemyFormationRepository(FormationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, formation: Formation) -> None:
        existing = await self._session.get(FormationModel, formation.id.value)
        if existing is None:
            self._session.add(mappers.formation_to_model(formation))
        else:
            mappers.apply_formation(existing, formation)

    async def upsert_many(self, formations: list[Formation]) -> None:
        if not formations:
            return
        rows = [
            {
                "id": f.id.value,
                "name": str(f.name),
                "slug": str(f.slug),
                "created_at": f.created_at,
                "updated_at": f.updated_at,
            }
            for f in formations
        ]
        stmt = pg_insert(FormationModel).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=[FormationModel.id],
            set_={
                "name": stmt.excluded.name,
                "slug": stmt.excluded.slug,
                "updated_at": stmt.excluded.updated_at,
            },
        )
        await self._session.execute(stmt)

    async def get(self, formation_id: FormationId) -> Formation:
        model = await self._session.get(FormationModel, formation_id.value)
        if model is None:
            raise FormationNotFound(str(formation_id))
        return mappers.formation_to_domain(model)

    async def exists(self, formation_id: FormationId) -> bool:
        stmt = select(FormationModel.id).where(FormationModel.id == formation_id.value).limit(1)
        return (await self._session.execute(stmt)).first() is not None

    async def find_by_name(self, name: str) -> Formation | None:
        result = await self._session.execute(
            select(FormationModel).where(FormationModel.name == name)
        )
        model = result.scalar_one_or_none()
        return mappers.formation_to_domain(model) if model else None

    async def find_by_slug(self, slug: str) -> Formation | None:
        result = await self._session.execute(
            select(FormationModel).where(FormationModel.slug == slug)
        )
        model = result.scalar_one_or_none()
        return mappers.formation_to_domain(model) if model else None

    async def list_all(self) -> list[Formation]:
        result = await self._session.execute(select(FormationModel).order_by(FormationModel.name))
        return [mappers.formation_to_domain(m) for m in result.scalars().all()]

    async def delete(self, formation_id: FormationId) -> None:
        model = await self._session.get(FormationModel, formation_id.value)
        if model is None:
            raise FormationNotFound(str(formation_id))
        await self._session.delete(model)


class SqlAlchemyChapterRepository(ChapterRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, chapter: Chapter) -> None:
        existing = await self._session.get(ChapterModel, chapter.id.value)
        if existing is None:
            self._session.add(mappers.chapter_to_model(chapter))
        else:
            mappers.apply_chapter(existing, chapter)

    async def upsert_many(self, chapters: list[Chapter]) -> None:
        if not chapters:
            return
        rows = [
            {
                "id": c.id.value,
                "formation_id": c.formation_id.value,
                "name": str(c.name),
                "slug": str(c.slug),
                "position": c.position.value,
                "created_at": c.created_at,
                "updated_at": c.updated_at,
            }
            for c in chapters
        ]
        stmt = pg_insert(ChapterModel).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=[ChapterModel.id],
            set_={
                "formation_id": stmt.excluded.formation_id,
                "name": stmt.excluded.name,
                "slug": stmt.excluded.slug,
                "position": stmt.excluded.position,
                "updated_at": stmt.excluded.updated_at,
            },
        )
        await self._session.execute(stmt)

    async def get(self, chapter_id: ChapterId) -> Chapter:
        model = await self._session.get(ChapterModel, chapter_id.value)
        if model is None:
            raise ChapterNotFound(str(chapter_id))
        return mappers.chapter_to_domain(model)

    async def exists(self, chapter_id: ChapterId) -> bool:
        stmt = select(ChapterModel.id).where(ChapterModel.id == chapter_id.value).limit(1)
        return (await self._session.execute(stmt)).first() is not None

    async def list_by_formation(self, formation_id: FormationId) -> list[Chapter]:
        result = await self._session.execute(
            select(ChapterModel)
            .where(ChapterModel.formation_id == formation_id.value)
            .order_by(ChapterModel.position)
        )
        return [mappers.chapter_to_domain(m) for m in result.scalars().all()]

    async def list_all(self) -> list[Chapter]:
        result = await self._session.execute(
            select(ChapterModel).order_by(ChapterModel.formation_id, ChapterModel.position)
        )
        return [mappers.chapter_to_domain(m) for m in result.scalars().all()]

    async def next_position(self, formation_id: FormationId) -> int:
        # Sérialise les inserts concurrentes (UNIQUE position) via verrou parent.
        await self._session.execute(
            select(FormationModel.id)
            .where(FormationModel.id == formation_id.value)
            .with_for_update()
        )
        result = await self._session.execute(
            select(func.coalesce(func.max(ChapterModel.position), -1)).where(
                ChapterModel.formation_id == formation_id.value
            )
        )
        return int(result.scalar_one()) + 1

    async def delete(self, chapter_id: ChapterId) -> None:
        model = await self._session.get(ChapterModel, chapter_id.value)
        if model is None:
            raise ChapterNotFound(str(chapter_id))
        await self._session.delete(model)


class SqlAlchemyVideoRepository(VideoRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, video: Video) -> None:
        existing = await self._session.get(VideoModel, video.id.value)
        if existing is None:
            self._session.add(mappers.video_to_model(video))
        else:
            mappers.apply_video(existing, video)

    async def upsert_many(self, videos: list[Video]) -> None:
        if not videos:
            return
        rows = [
            {
                "id": v.id.value,
                "chapter_id": v.chapter_id.value,
                "title": str(v.title),
                "filename": v.filename,
                "relative_path": str(v.relative_path),
                "position": v.position.value,
                "duration_seconds": v.duration.value,
                "kind": v.kind,
                "processing_status": v.processing_status,
                "transcription_status": v.transcription_status,
                "summary_status": v.summary_status,
                "created_at": v.created_at,
                "updated_at": v.updated_at,
            }
            for v in videos
        ]
        stmt = pg_insert(VideoModel).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=[VideoModel.id],
            set_={
                "chapter_id": stmt.excluded.chapter_id,
                "title": stmt.excluded.title,
                "filename": stmt.excluded.filename,
                "relative_path": stmt.excluded.relative_path,
                "position": stmt.excluded.position,
                "duration_seconds": stmt.excluded.duration_seconds,
                "kind": stmt.excluded.kind,
                "processing_status": stmt.excluded.processing_status,
                "transcription_status": stmt.excluded.transcription_status,
                "summary_status": stmt.excluded.summary_status,
                "updated_at": stmt.excluded.updated_at,
            },
        )
        await self._session.execute(stmt)

    async def get(self, video_id: VideoId) -> Video:
        model = await self._session.get(VideoModel, video_id.value)
        if model is None:
            raise VideoNotFound(str(video_id))
        return mappers.video_to_domain(model)

    async def exists(self, video_id: VideoId) -> bool:
        stmt = select(VideoModel.id).where(VideoModel.id == video_id.value).limit(1)
        return (await self._session.execute(stmt)).first() is not None

    async def find_by_relative_path(self, path: RelativePath) -> Video | None:
        result = await self._session.execute(
            select(VideoModel).where(VideoModel.relative_path == str(path))
        )
        model = result.scalar_one_or_none()
        return mappers.video_to_domain(model) if model else None

    async def list_by_chapter(self, chapter_id: ChapterId) -> list[Video]:
        result = await self._session.execute(
            select(VideoModel)
            .where(VideoModel.chapter_id == chapter_id.value)
            .order_by(VideoModel.position)
        )
        return [mappers.video_to_domain(m) for m in result.scalars().all()]

    async def list_by_formation(self, formation_id: FormationId) -> list[Video]:
        result = await self._session.execute(
            select(VideoModel)
            .join(ChapterModel, VideoModel.chapter_id == ChapterModel.id)
            .where(ChapterModel.formation_id == formation_id.value)
            .order_by(ChapterModel.position, VideoModel.position)
        )
        return [mappers.video_to_domain(m) for m in result.scalars().all()]

    async def list_all(self) -> list[Video]:
        result = await self._session.execute(select(VideoModel))
        return [mappers.video_to_domain(m) for m in result.scalars().all()]

    async def list_media_processing(self) -> list[Video]:
        result = await self._session.execute(
            select(VideoModel).where(VideoModel.processing_status == Video.STATUS_PROCESSING)
        )
        return [mappers.video_to_domain(m) for m in result.scalars().all()]

    async def list_ai_processing(self) -> list[Video]:
        result = await self._session.execute(
            select(VideoModel).where(
                or_(
                    VideoModel.transcription_status == Video.AI_PROCESSING,
                    VideoModel.summary_status == Video.AI_PROCESSING,
                )
            )
        )
        return [mappers.video_to_domain(m) for m in result.scalars().all()]

    async def next_position(self, chapter_id: ChapterId) -> int:
        # Sérialise les inserts concurrentes (UNIQUE position) via verrou parent.
        await self._session.execute(
            select(ChapterModel.id).where(ChapterModel.id == chapter_id.value).with_for_update()
        )
        result = await self._session.execute(
            select(func.coalesce(func.max(VideoModel.position), -1)).where(
                VideoModel.chapter_id == chapter_id.value
            )
        )
        return int(result.scalar_one()) + 1

    async def delete(self, video_id: VideoId) -> None:
        model = await self._session.get(VideoModel, video_id.value)
        if model is None:
            raise VideoNotFound(str(video_id))
        await self._session.delete(model)

    async def save_ordered(self, videos: list[Video]) -> None:
        """Persiste un nouvel ordre (UNIQUE position différé jusqu'au COMMIT)."""
        if not videos:
            return
        with self._session.no_autoflush:
            for video in videos:
                model = await self._session.get(VideoModel, video.id.value)
                if model is None:
                    raise VideoNotFound(str(video.id))
                mappers.apply_video(model, video)
            await self._session.flush()


class SqlAlchemyDocumentRepository(DocumentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, document: Document) -> None:
        existing = await self._session.get(DocumentModel, document.id.value)
        if existing is None:
            self._session.add(mappers.document_to_model(document))
        else:
            mappers.apply_document(existing, document)

    async def upsert_many(self, documents: list[Document]) -> None:
        if not documents:
            return
        rows = [
            {
                "id": d.id.value,
                "chapter_id": d.chapter_id.value,
                "video_id": d.video_id.value if d.video_id else None,
                "title": str(d.title),
                "filename": d.filename,
                "relative_path": str(d.relative_path),
                "mime_type": d.mime_type,
                "position": d.position.value,
                "created_at": d.created_at,
                "updated_at": d.updated_at,
            }
            for d in documents
        ]
        stmt = pg_insert(DocumentModel).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=[DocumentModel.id],
            set_={
                "chapter_id": stmt.excluded.chapter_id,
                "video_id": stmt.excluded.video_id,
                "title": stmt.excluded.title,
                "filename": stmt.excluded.filename,
                "relative_path": stmt.excluded.relative_path,
                "mime_type": stmt.excluded.mime_type,
                "position": stmt.excluded.position,
                "updated_at": stmt.excluded.updated_at,
            },
        )
        await self._session.execute(stmt)

    async def get(self, document_id: DocumentId) -> Document:
        model = await self._session.get(DocumentModel, document_id.value)
        if model is None:
            raise DocumentNotFound(str(document_id))
        return mappers.document_to_domain(model)

    async def find_by_relative_path(self, path: RelativePath) -> Document | None:
        result = await self._session.execute(
            select(DocumentModel).where(DocumentModel.relative_path == str(path))
        )
        model = result.scalar_one_or_none()
        return mappers.document_to_domain(model) if model else None

    async def list_by_chapter(self, chapter_id: ChapterId) -> list[Document]:
        result = await self._session.execute(
            select(DocumentModel)
            .where(DocumentModel.chapter_id == chapter_id.value)
            .order_by(DocumentModel.position)
        )
        return [mappers.document_to_domain(m) for m in result.scalars().all()]

    async def next_position(self, chapter_id: ChapterId) -> int:
        # Sérialise les inserts concurrentes (UNIQUE position) via verrou parent.
        await self._session.execute(
            select(ChapterModel.id).where(ChapterModel.id == chapter_id.value).with_for_update()
        )
        result = await self._session.execute(
            select(func.coalesce(func.max(DocumentModel.position), -1)).where(
                DocumentModel.chapter_id == chapter_id.value
            )
        )
        return int(result.scalar_one()) + 1

    async def delete(self, document_id: DocumentId) -> None:
        model = await self._session.get(DocumentModel, document_id.value)
        if model is None:
            raise DocumentNotFound(str(document_id))
        await self._session.delete(model)

    async def list_all(self) -> list[Document]:
        result = await self._session.execute(select(DocumentModel))
        return [mappers.document_to_domain(m) for m in result.scalars().all()]


class SqlAlchemyJobRepository(JobRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, job: Job) -> None:
        existing = await self._session.get(JobModel, job.id.value)
        if existing is None:
            self._session.add(mappers.job_to_model(job))
        else:
            mappers.apply_job(existing, job)

    async def get(self, job_id: JobId) -> Job:
        model = await self._session.get(JobModel, job_id.value)
        if model is None:
            raise JobNotFound(str(job_id))
        return mappers.job_to_domain(model)

    async def list_active(self) -> list[Job]:
        result = await self._session.execute(
            select(JobModel)
            .where(JobModel.status.in_(tuple(Job.ACTIVE_STATUSES)))
            .order_by(JobModel.created_at)
        )
        return [mappers.job_to_domain(m) for m in result.scalars().all()]

    async def list_active_by_video(self, video_id: VideoId) -> list[Job]:
        result = await self._session.execute(
            select(JobModel)
            .where(
                JobModel.video_id == video_id.value,
                JobModel.status.in_(tuple(Job.ACTIVE_STATUSES)),
            )
            .order_by(JobModel.created_at)
        )
        return [mappers.job_to_domain(m) for m in result.scalars().all()]

    async def find_active(
        self,
        *,
        kind: str,
        video_id: VideoId | None = None,
        formation_id: FormationId | None = None,
    ) -> Job | None:
        stmt = select(JobModel).where(
            JobModel.kind == kind,
            JobModel.status.in_(tuple(Job.ACTIVE_STATUSES)),
        )
        if video_id is not None:
            stmt = stmt.where(JobModel.video_id == video_id.value)
        if formation_id is not None:
            stmt = stmt.where(JobModel.formation_id == formation_id.value)
        result = await self._session.execute(stmt.limit(1))
        model = result.scalar_one_or_none()
        return mappers.job_to_domain(model) if model else None
