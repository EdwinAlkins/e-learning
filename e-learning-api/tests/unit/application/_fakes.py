"""Fakes in-memory pour tests application."""

from __future__ import annotations

from e_learning.application.jobs.dto import ComputeJobMessage
from e_learning.application.shared.messaging import JobPublisherPort
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
from e_learning.domain.learning.entities import Note, Progress
from e_learning.domain.learning.exceptions import NoteNotFound
from e_learning.domain.learning.repository import NoteRepository, ProgressRepository
from e_learning.domain.learning.value_objects import NoteId, ProgressId
from e_learning.domain.user.entities import User
from e_learning.domain.user.exceptions import UserNotFound
from e_learning.domain.user.repository import UserRepository
from e_learning.domain.user.value_objects import UserId


class RecordingPublisher(JobPublisherPort):
    """Enregistre les publications sans broker."""

    def __init__(self) -> None:
        self.published: list[ComputeJobMessage] = []

    async def publish(self, message: ComputeJobMessage) -> None:
        self.published.append(message)


class FakeUserRepository(UserRepository):
    def __init__(self) -> None:
        self.items: dict[str, User] = {}

    async def save(self, user: User) -> None:
        self.items[str(user.id)] = user

    async def get(self, user_id: UserId) -> User:
        try:
            return self.items[str(user_id)]
        except KeyError as exc:
            raise UserNotFound(str(user_id)) from exc

    async def exists(self, user_id: UserId) -> bool:
        return str(user_id) in self.items


class FakeFormationRepository(FormationRepository):
    def __init__(self) -> None:
        self.items: dict[str, Formation] = {}

    async def save(self, formation: Formation) -> None:
        self.items[str(formation.id)] = formation

    async def get(self, formation_id: FormationId) -> Formation:
        try:
            return self.items[str(formation_id)]
        except KeyError as exc:
            raise FormationNotFound(str(formation_id)) from exc

    async def exists(self, formation_id: FormationId) -> bool:
        return str(formation_id) in self.items

    async def find_by_name(self, name: str) -> Formation | None:
        return next((f for f in self.items.values() if str(f.name) == name), None)

    async def find_by_slug(self, slug: str) -> Formation | None:
        return next((f for f in self.items.values() if str(f.slug) == slug), None)

    async def list_all(self) -> list[Formation]:
        return list(self.items.values())

    async def upsert_many(self, formations: list[Formation]) -> None:
        for formation in formations:
            await self.save(formation)

    async def delete(self, formation_id: FormationId) -> None:
        self.items.pop(str(formation_id), None)


class FakeChapterRepository(ChapterRepository):
    def __init__(self) -> None:
        self.items: dict[str, Chapter] = {}

    async def save(self, chapter: Chapter) -> None:
        self.items[str(chapter.id)] = chapter

    async def get(self, chapter_id: ChapterId) -> Chapter:
        try:
            return self.items[str(chapter_id)]
        except KeyError as exc:
            raise ChapterNotFound(str(chapter_id)) from exc

    async def exists(self, chapter_id: ChapterId) -> bool:
        return str(chapter_id) in self.items

    async def list_by_formation(self, formation_id: FormationId) -> list[Chapter]:
        chapters = [c for c in self.items.values() if c.formation_id == formation_id]
        return sorted(chapters, key=lambda c: c.position.value)

    async def list_all(self) -> list[Chapter]:
        return sorted(self.items.values(), key=lambda c: (str(c.formation_id), c.position.value))

    async def upsert_many(self, chapters: list[Chapter]) -> None:
        for chapter in chapters:
            await self.save(chapter)

    async def next_position(self, formation_id: FormationId) -> int:
        chapters = await self.list_by_formation(formation_id)
        return (max((c.position.value for c in chapters), default=-1)) + 1

    async def delete(self, chapter_id: ChapterId) -> None:
        self.items.pop(str(chapter_id), None)

    async def save_ordered(self, chapters: list[Chapter]) -> None:
        for chapter in chapters:
            await self.save(chapter)


class FakeVideoRepository(VideoRepository):
    def __init__(self) -> None:
        self.items: dict[str, Video] = {}

    async def save(self, video: Video) -> None:
        self.items[str(video.id)] = video

    async def get(self, video_id: VideoId) -> Video:
        try:
            return self.items[str(video_id)]
        except KeyError as exc:
            raise VideoNotFound(str(video_id)) from exc

    async def exists(self, video_id: VideoId) -> bool:
        return str(video_id) in self.items

    async def find_by_relative_path(self, path: RelativePath) -> Video | None:
        return next((v for v in self.items.values() if str(v.relative_path) == str(path)), None)

    async def list_by_chapter(self, chapter_id: ChapterId) -> list[Video]:
        videos = [v for v in self.items.values() if v.chapter_id == chapter_id]
        return sorted(videos, key=lambda v: v.position.value)

    async def list_by_formation(self, formation_id: FormationId) -> list[Video]:
        return list(self.items.values())

    async def list_all(self) -> list[Video]:
        return list(self.items.values())

    async def list_media_processing(self) -> list[Video]:
        return [v for v in self.items.values() if v.processing_status == Video.STATUS_PROCESSING]

    async def list_ai_processing(self) -> list[Video]:
        return [
            v
            for v in self.items.values()
            if v.transcription_status == Video.AI_PROCESSING
            or v.summary_status == Video.AI_PROCESSING
        ]

    async def upsert_many(self, videos: list[Video]) -> None:
        for video in videos:
            await self.save(video)

    async def next_position(self, chapter_id: ChapterId) -> int:
        videos = await self.list_by_chapter(chapter_id)
        return (max((v.position.value for v in videos), default=-1)) + 1

    async def delete(self, video_id: VideoId) -> None:
        self.items.pop(str(video_id), None)

    async def save_ordered(self, videos: list[Video]) -> None:
        for video in videos:
            await self.save(video)


class FakeDocumentRepository(DocumentRepository):
    def __init__(self) -> None:
        self.items: dict[str, Document] = {}

    async def save(self, document: Document) -> None:
        self.items[str(document.id)] = document

    async def upsert_many(self, documents: list[Document]) -> None:
        for document in documents:
            await self.save(document)

    async def get(self, document_id: DocumentId) -> Document:
        try:
            return self.items[str(document_id)]
        except KeyError as exc:
            raise DocumentNotFound(str(document_id)) from exc

    async def find_by_relative_path(self, path: RelativePath) -> Document | None:
        return next((d for d in self.items.values() if str(d.relative_path) == str(path)), None)

    async def list_by_chapter(self, chapter_id: ChapterId) -> list[Document]:
        docs = [d for d in self.items.values() if d.chapter_id == chapter_id]
        return sorted(docs, key=lambda d: d.position.value)

    async def next_position(self, chapter_id: ChapterId) -> int:
        docs = await self.list_by_chapter(chapter_id)
        return (max((d.position.value for d in docs), default=-1)) + 1

    async def delete(self, document_id: DocumentId) -> None:
        self.items.pop(str(document_id), None)

    async def list_all(self) -> list[Document]:
        return list(self.items.values())


class FakeJobRepository(JobRepository):
    def __init__(self) -> None:
        self.items: dict[str, Job] = {}

    async def save(self, job: Job) -> None:
        self.items[str(job.id)] = job

    async def get(self, job_id: JobId) -> Job:
        try:
            return self.items[str(job_id)]
        except KeyError as exc:
            raise JobNotFound(str(job_id)) from exc

    async def list_active(self) -> list[Job]:
        return [j for j in self.items.values() if j.is_active]

    async def list_active_by_video(self, video_id: VideoId) -> list[Job]:
        return [
            j
            for j in self.items.values()
            if j.is_active and j.video_id is not None and j.video_id == video_id
        ]

    async def find_active(
        self,
        *,
        kind: str,
        video_id: VideoId | None = None,
        formation_id: FormationId | None = None,
    ) -> Job | None:
        for job in self.items.values():
            if not job.is_active or job.kind != kind:
                continue
            if video_id is not None and job.video_id != video_id:
                continue
            if formation_id is not None and job.formation_id != formation_id:
                continue
            return job
        return None


class FakeNoteRepository(NoteRepository):
    def __init__(self) -> None:
        self.items: dict[str, Note] = {}

    async def save(self, note: Note) -> None:
        self.items[str(note.id)] = note

    async def get(self, note_id: NoteId) -> Note:
        try:
            return self.items[str(note_id)]
        except KeyError as exc:
            raise NoteNotFound(str(note_id)) from exc

    async def list_by_user_and_video(self, user_id: UserId, video_id: VideoId) -> list[Note]:
        return [n for n in self.items.values() if n.user_id == user_id and n.video_id == video_id]

    async def delete(self, note_id: NoteId) -> None:
        self.items.pop(str(note_id), None)


class FakeProgressRepository(ProgressRepository):
    def __init__(self) -> None:
        self.items: dict[str, Progress] = {}

    async def save(self, progress: Progress) -> None:
        self.items[str(progress.id)] = progress

    async def get(self, progress_id: ProgressId) -> Progress:
        return self.items[str(progress_id)]

    async def find_by_user_and_video(self, user_id: UserId, video_id: VideoId) -> Progress | None:
        return next(
            (p for p in self.items.values() if p.user_id == user_id and p.video_id == video_id),
            None,
        )

    async def list_by_user_and_videos(
        self, user_id: UserId, video_ids: list[VideoId]
    ) -> list[Progress]:
        ids = set(video_ids)
        return [p for p in self.items.values() if p.user_id == user_id and p.video_id in ids]
