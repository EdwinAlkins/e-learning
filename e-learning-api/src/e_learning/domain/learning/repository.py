"""Ports de persistance du bounded context ``learning``."""

from __future__ import annotations

from abc import ABC, abstractmethod

from e_learning.domain.catalog.value_objects import VideoId
from e_learning.domain.learning.entities import Note, Progress
from e_learning.domain.learning.value_objects import NoteId, ProgressId
from e_learning.domain.user.value_objects import UserId


class NoteRepository(ABC):
    @abstractmethod
    async def save(self, note: Note) -> None: ...

    @abstractmethod
    async def get(self, note_id: NoteId) -> Note: ...

    @abstractmethod
    async def list_by_user_and_video(self, user_id: UserId, video_id: VideoId) -> list[Note]: ...

    @abstractmethod
    async def delete(self, note_id: NoteId) -> None: ...


class ProgressRepository(ABC):
    @abstractmethod
    async def save(self, progress: Progress) -> None: ...

    @abstractmethod
    async def get(self, progress_id: ProgressId) -> Progress: ...

    @abstractmethod
    async def find_by_user_and_video(
        self, user_id: UserId, video_id: VideoId
    ) -> Progress | None: ...

    @abstractmethod
    async def list_by_user_and_videos(
        self, user_id: UserId, video_ids: list[VideoId]
    ) -> list[Progress]: ...
