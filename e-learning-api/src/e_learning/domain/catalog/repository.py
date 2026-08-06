"""Ports de persistance du bounded context ``catalog``."""

from __future__ import annotations

from abc import ABC, abstractmethod

from e_learning.domain.catalog.entities import Chapter, Document, Formation, Video
from e_learning.domain.catalog.job import Job
from e_learning.domain.catalog.value_objects import (
    ChapterId,
    DocumentId,
    FormationId,
    JobId,
    RelativePath,
    VideoId,
)


class FormationRepository(ABC):
    @abstractmethod
    async def save(self, formation: Formation) -> None: ...

    @abstractmethod
    async def upsert_many(self, formations: list[Formation]) -> None: ...

    @abstractmethod
    async def get(self, formation_id: FormationId) -> Formation: ...

    @abstractmethod
    async def exists(self, formation_id: FormationId) -> bool: ...

    @abstractmethod
    async def find_by_name(self, name: str) -> Formation | None: ...

    @abstractmethod
    async def find_by_slug(self, slug: str) -> Formation | None: ...

    @abstractmethod
    async def list_all(self) -> list[Formation]: ...

    @abstractmethod
    async def delete(self, formation_id: FormationId) -> None: ...


class ChapterRepository(ABC):
    @abstractmethod
    async def save(self, chapter: Chapter) -> None: ...

    @abstractmethod
    async def upsert_many(self, chapters: list[Chapter]) -> None: ...

    @abstractmethod
    async def get(self, chapter_id: ChapterId) -> Chapter: ...

    @abstractmethod
    async def exists(self, chapter_id: ChapterId) -> bool: ...

    @abstractmethod
    async def list_by_formation(self, formation_id: FormationId) -> list[Chapter]: ...

    @abstractmethod
    async def list_all(self) -> list[Chapter]: ...

    @abstractmethod
    async def next_position(self, formation_id: FormationId) -> int: ...

    @abstractmethod
    async def delete(self, chapter_id: ChapterId) -> None: ...


class VideoRepository(ABC):
    @abstractmethod
    async def save(self, video: Video) -> None: ...

    @abstractmethod
    async def upsert_many(self, videos: list[Video]) -> None: ...

    @abstractmethod
    async def get(self, video_id: VideoId) -> Video: ...

    @abstractmethod
    async def exists(self, video_id: VideoId) -> bool: ...

    @abstractmethod
    async def find_by_relative_path(self, path: RelativePath) -> Video | None: ...

    @abstractmethod
    async def list_by_chapter(self, chapter_id: ChapterId) -> list[Video]: ...

    @abstractmethod
    async def list_by_formation(self, formation_id: FormationId) -> list[Video]: ...

    @abstractmethod
    async def list_all(self) -> list[Video]: ...

    @abstractmethod
    async def list_media_processing(self) -> list[Video]:
        """Vidéos dont ``processing_status`` est ``processing``."""

    @abstractmethod
    async def list_ai_processing(self) -> list[Video]:
        """Vidéos avec transcription ou résumé en ``processing``."""

    @abstractmethod
    async def next_position(self, chapter_id: ChapterId) -> int: ...

    @abstractmethod
    async def delete(self, video_id: VideoId) -> None: ...

    @abstractmethod
    async def save_ordered(self, videos: list[Video]) -> None:
        """Persiste un nouvel ordre (contrainte UNIQUE position différée en PG)."""


class DocumentRepository(ABC):
    @abstractmethod
    async def save(self, document: Document) -> None: ...

    @abstractmethod
    async def upsert_many(self, documents: list[Document]) -> None: ...

    @abstractmethod
    async def get(self, document_id: DocumentId) -> Document: ...

    @abstractmethod
    async def find_by_relative_path(self, path: RelativePath) -> Document | None: ...

    @abstractmethod
    async def list_by_chapter(self, chapter_id: ChapterId) -> list[Document]: ...

    @abstractmethod
    async def next_position(self, chapter_id: ChapterId) -> int: ...

    @abstractmethod
    async def delete(self, document_id: DocumentId) -> None: ...

    @abstractmethod
    async def list_all(self) -> list[Document]: ...


class JobRepository(ABC):
    @abstractmethod
    async def save(self, job: Job) -> None: ...

    @abstractmethod
    async def get(self, job_id: JobId) -> Job: ...

    @abstractmethod
    async def list_active(self) -> list[Job]:
        """Jobs ``queued`` ou ``running``."""

    @abstractmethod
    async def list_active_by_video(self, video_id: VideoId) -> list[Job]: ...

    @abstractmethod
    async def find_active(
        self, *, kind: str, video_id: VideoId | None = None, formation_id: FormationId | None = None
    ) -> Job | None:
        """Au plus un job actif pour (kind, cible)."""
