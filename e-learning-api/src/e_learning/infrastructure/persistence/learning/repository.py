"""Adaptateurs SQLAlchemy — learning."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from e_learning.domain.catalog.value_objects import VideoId
from e_learning.domain.learning.entities import Note, Progress
from e_learning.domain.learning.exceptions import NoteNotFound, ProgressNotFound
from e_learning.domain.learning.repository import NoteRepository, ProgressRepository
from e_learning.domain.learning.value_objects import NoteId, ProgressId
from e_learning.domain.user.value_objects import UserId
from e_learning.infrastructure.persistence.learning import mappers
from e_learning.infrastructure.persistence.learning.models import NoteModel, ProgressModel


class SqlAlchemyNoteRepository(NoteRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, note: Note) -> None:
        existing = await self._session.get(NoteModel, note.id.value)
        if existing is None:
            self._session.add(mappers.note_to_model(note))
        else:
            mappers.apply_note(existing, note)

    async def get(self, note_id: NoteId) -> Note:
        model = await self._session.get(NoteModel, note_id.value)
        if model is None:
            raise NoteNotFound(str(note_id))
        return mappers.note_to_domain(model)

    async def list_by_user_and_video(self, user_id: UserId, video_id: VideoId) -> list[Note]:
        result = await self._session.execute(
            select(NoteModel)
            .where(NoteModel.user_id == user_id.value, NoteModel.video_id == video_id.value)
            .order_by(NoteModel.timecode_seconds)
        )
        return [mappers.note_to_domain(m) for m in result.scalars().all()]

    async def delete(self, note_id: NoteId) -> None:
        model = await self._session.get(NoteModel, note_id.value)
        if model is None:
            raise NoteNotFound(str(note_id))
        await self._session.delete(model)


class SqlAlchemyProgressRepository(ProgressRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, progress: Progress) -> None:
        existing = await self._session.get(ProgressModel, progress.id.value)
        if existing is None:
            self._session.add(mappers.progress_to_model(progress))
        else:
            mappers.apply_progress(existing, progress)

    async def get(self, progress_id: ProgressId) -> Progress:
        model = await self._session.get(ProgressModel, progress_id.value)
        if model is None:
            raise ProgressNotFound(str(progress_id))
        return mappers.progress_to_domain(model)

    async def find_by_user_and_video(self, user_id: UserId, video_id: VideoId) -> Progress | None:
        result = await self._session.execute(
            select(ProgressModel).where(
                ProgressModel.user_id == user_id.value,
                ProgressModel.video_id == video_id.value,
            )
        )
        model = result.scalar_one_or_none()
        return mappers.progress_to_domain(model) if model else None

    async def list_by_user_and_videos(
        self, user_id: UserId, video_ids: list[VideoId]
    ) -> list[Progress]:
        if not video_ids:
            return []
        ids = [v.value for v in video_ids]
        result = await self._session.execute(
            select(ProgressModel).where(
                ProgressModel.user_id == user_id.value,
                ProgressModel.video_id.in_(ids),
            )
        )
        return [mappers.progress_to_domain(m) for m in result.scalars().all()]
