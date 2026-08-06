"""DTO / commands — contexte ``catalog``."""

from __future__ import annotations

from dataclasses import dataclass

from e_learning.domain.catalog.entities import Document, Formation, Video
from e_learning.domain.catalog.job import Job


@dataclass(frozen=True, slots=True)
class JobDTO:
    id: str
    kind: str
    status: str
    progress: int
    message: str

    @classmethod
    def from_entity(cls, job: Job) -> JobDTO:
        return cls(
            id=str(job.id),
            kind=job.kind,
            status=job.status,
            progress=job.progress,
            message=job.message,
        )


@dataclass(frozen=True, slots=True)
class VideoDTO:
    id: str
    title: str
    duration: float
    position: int
    relative_path: str
    kind: str = "video"
    processing_status: str = "ready"
    transcription_status: str = "none"
    summary_status: str = "none"
    active_jobs: tuple[JobDTO, ...] = ()

    @classmethod
    def from_entity(cls, video: Video, *, active_jobs: tuple[JobDTO, ...] = ()) -> VideoDTO:
        return cls(
            id=str(video.id),
            title=str(video.title),
            duration=video.duration.value,
            position=video.position.value,
            relative_path=str(video.relative_path),
            kind=video.kind,
            processing_status=video.processing_status,
            transcription_status=video.transcription_status,
            summary_status=video.summary_status,
            active_jobs=active_jobs,
        )


@dataclass(frozen=True, slots=True)
class MediaConversionJob:
    video_id: str
    source_relative_path: str
    target_relative_path: str
    kind: str
    job_id: str | None = None


@dataclass(frozen=True, slots=True)
class CreateVideoResult:
    video: VideoDTO
    conversion: MediaConversionJob | None = None


@dataclass(frozen=True, slots=True)
class RenameVideoResult:
    video: VideoDTO
    conversion: MediaConversionJob | None = None


@dataclass(frozen=True, slots=True)
class DocumentDTO:
    id: str
    title: str
    position: int
    relative_path: str
    filename: str
    mime_type: str | None
    video_id: str | None

    @classmethod
    def from_entity(cls, document: Document) -> DocumentDTO:
        return cls(
            id=str(document.id),
            title=str(document.title),
            position=document.position.value,
            relative_path=str(document.relative_path),
            filename=document.filename,
            mime_type=document.mime_type,
            video_id=str(document.video_id) if document.video_id else None,
        )


@dataclass(frozen=True, slots=True)
class ChapterDTO:
    id: str
    name: str
    slug: str
    position: int
    videos: list[VideoDTO]
    documents: list[DocumentDTO]


@dataclass(frozen=True, slots=True)
class FormationDTO:
    id: str
    name: str
    slug: str
    chapters: list[ChapterDTO]

    @classmethod
    def from_parts(
        cls,
        formation: Formation,
        chapters: list[ChapterDTO],
    ) -> FormationDTO:
        return cls(
            id=str(formation.id),
            name=str(formation.name),
            slug=str(formation.slug),
            chapters=chapters,
        )


@dataclass(frozen=True, slots=True)
class CreateFormationCommand:
    name: str


@dataclass(frozen=True, slots=True)
class RenameFormationCommand:
    formation_id: str
    name: str


@dataclass(frozen=True, slots=True)
class CreateChapterCommand:
    formation_id: str
    name: str


@dataclass(frozen=True, slots=True)
class RenameChapterCommand:
    chapter_id: str
    name: str


@dataclass(frozen=True, slots=True)
class CreateVideoCommand:
    chapter_id: str
    title: str
    file_bytes: bytes
    filename: str


@dataclass(frozen=True, slots=True)
class RenameVideoCommand:
    video_id: str
    title: str | None = None
    file_bytes: bytes | None = None
    filename: str | None = None


@dataclass(frozen=True, slots=True)
class ReorderVideosCommand:
    chapter_id: str
    video_ids: list[str]


@dataclass(frozen=True, slots=True)
class MoveVideoCommand:
    video_id: str
    source_chapter_id: str
    target_chapter_id: str
    position: int | None = None
    after_video_id: str | None = None


@dataclass(frozen=True, slots=True)
class CreateDocumentCommand:
    chapter_id: str
    title: str
    file_bytes: bytes
    filename: str
    video_id: str | None = None


@dataclass(frozen=True, slots=True)
class UpdateDocumentCommand:
    document_id: str
    title: str | None = None
    video_id: str | None = None
    update_video_id: bool = False
