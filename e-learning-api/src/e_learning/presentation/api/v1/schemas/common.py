"""Schémas Pydantic — transport HTTP."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from e_learning.application.catalog.dto import (
    ChapterDTO,
    DocumentDTO,
    FormationDTO,
    JobDTO,
    VideoDTO,
)
from e_learning.application.learning.dto import (
    FormationProgressDTO,
    NoteDTO,
)
from e_learning.application.user.dto import UserDTO


class UIDResponse(BaseModel):
    uid: str

    @classmethod
    def from_dto(cls, dto: UserDTO) -> UIDResponse:
        return cls(uid=dto.id)


class RestoreRequest(BaseModel):
    uid: str


class JobResponse(BaseModel):
    id: str
    kind: str
    status: str
    progress: int
    message: str = ""

    @classmethod
    def from_dto(cls, dto: JobDTO) -> JobResponse:
        return cls(
            id=dto.id,
            kind=dto.kind,
            status=dto.status,
            progress=dto.progress,
            message=dto.message,
        )


class VideoResponse(BaseModel):
    id: str
    title: str
    duration: float
    position: int = 0
    kind: str = "video"
    processing_status: str = "ready"
    transcription_status: str = "none"
    summary_status: str = "none"
    active_jobs: list[JobResponse] = Field(default_factory=list)

    @classmethod
    def from_dto(cls, dto: VideoDTO) -> VideoResponse:
        return cls(
            id=dto.id,
            title=dto.title,
            duration=dto.duration,
            position=dto.position,
            kind=dto.kind,
            processing_status=dto.processing_status,
            transcription_status=dto.transcription_status,
            summary_status=dto.summary_status,
            active_jobs=[JobResponse.from_dto(j) for j in dto.active_jobs],
        )


class DocumentResponse(BaseModel):
    id: str
    title: str
    position: int
    filename: str = ""
    mime_type: str | None = None
    video_id: str | None = None

    @classmethod
    def from_dto(cls, dto: DocumentDTO) -> DocumentResponse:
        return cls(
            id=dto.id,
            title=dto.title,
            position=dto.position,
            filename=dto.filename,
            mime_type=dto.mime_type,
            video_id=dto.video_id,
        )


class ChapterResponse(BaseModel):
    id: str
    name: str
    slug: str = ""
    position: int = 0
    videos: list[VideoResponse] = Field(default_factory=list)
    documents: list[DocumentResponse] = Field(default_factory=list)

    @classmethod
    def from_dto(cls, dto: ChapterDTO) -> ChapterResponse:
        return cls(
            id=dto.id,
            name=dto.name,
            slug=dto.slug,
            position=dto.position,
            videos=[VideoResponse.from_dto(v) for v in dto.videos],
            documents=[DocumentResponse.from_dto(d) for d in dto.documents],
        )


class FormationResponse(BaseModel):
    id: str
    name: str
    slug: str = ""
    chapters: list[ChapterResponse] = Field(default_factory=list)

    @classmethod
    def from_dto(cls, dto: FormationDTO) -> FormationResponse:
        return cls(
            id=dto.id,
            name=dto.name,
            slug=dto.slug,
            chapters=[ChapterResponse.from_dto(c) for c in dto.chapters],
        )


class CatalogResponse(BaseModel):
    formations: list[FormationResponse]


class NameRequest(BaseModel):
    name: str


class VideoTitleRequest(BaseModel):
    """Rename vidéo — le front envoie ``title`` (``name`` accepté en compat)."""

    title: str | None = None
    name: str | None = None

    def resolved_title(self) -> str:
        value = self.title if self.title is not None else self.name
        if value is None or not value.strip():
            raise ValueError("Fournir title (ou name).")
        return value


class ReorderVideosRequest(BaseModel):
    video_ids: list[str]


class ReorderChaptersRequest(BaseModel):
    chapter_ids: list[str]


class MoveVideoRequest(BaseModel):
    position: int | None = None
    after_video_id: str | None = None


class DocumentUpdateRequest(BaseModel):
    """PATCH document — ``video_id: null`` détache la vidéo si le champ est présent."""

    title: str | None = None
    video_id: str | None = None


class ProgressUpdateRequest(BaseModel):
    last_position: float


class ProgressResponse(BaseModel):
    last_position: float


class NoteCreateRequest(BaseModel):
    timecode: float
    content: str


class NoteUpdateRequest(BaseModel):
    content: str


class NoteResponse(BaseModel):
    id: str
    video_id: str
    timecode: float
    content: str
    created_at: datetime

    @classmethod
    def from_dto(cls, dto: NoteDTO) -> NoteResponse:
        return cls(
            id=dto.id,
            video_id=dto.video_id,
            timecode=dto.timecode,
            content=dto.content,
            created_at=dto.created_at,
        )


class SummaryResponse(BaseModel):
    summary: str


class SummaryUpdateRequest(BaseModel):
    summary: str


class TranscriptionResponse(BaseModel):
    content: str


class FormationProgressResponse(BaseModel):
    name: str
    chapters: list[dict]
    progress_percentage: float

    @classmethod
    def from_dto(cls, dto: FormationProgressDTO) -> FormationProgressResponse:
        return cls(
            name=dto.name,
            chapters=[
                {
                    "name": c.name,
                    "videos": [
                        {
                            "id": v.id,
                            "title": v.title,
                            "progress_percentage": v.progress_percentage,
                        }
                        for v in c.videos
                    ],
                    "progress_percentage": c.progress_percentage,
                }
                for c in dto.chapters
            ],
            progress_percentage=dto.progress_percentage,
        )


class FormationsProgressResponse(BaseModel):
    progress: dict[str, FormationProgressResponse]


class AskFormationRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)


class RagCitationResponse(BaseModel):
    title: str
    source: str
    excerpt: str
    video_id: str | None = None
    document_id: str | None = None


class AskFormationResponse(BaseModel):
    answer: str
    citations: list[RagCitationResponse]


class IndexFormationAcceptedResponse(BaseModel):
    detail: str = "Indexation RAG démarrée"
