"""Mappers catalog domaine ↔ ORM."""

from __future__ import annotations

from e_learning.domain.catalog.entities import Chapter, Document, Formation, Video
from e_learning.domain.catalog.job import Job
from e_learning.domain.catalog.value_objects import (
    ChapterId,
    ChapterName,
    DocumentId,
    DocumentTitle,
    DurationSeconds,
    FormationId,
    FormationName,
    JobId,
    Position,
    RelativePath,
    Slug,
    VideoId,
    VideoTitle,
)
from e_learning.infrastructure.persistence.catalog.models import (
    ChapterModel,
    DocumentModel,
    FormationModel,
    JobModel,
    VideoModel,
)
from e_learning.infrastructure.persistence.converters import as_utc


def formation_to_model(entity: Formation) -> FormationModel:
    return FormationModel(
        id=entity.id.value,
        name=str(entity.name),
        slug=str(entity.slug),
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def apply_formation(model: FormationModel, entity: Formation) -> None:
    model.name = str(entity.name)
    model.slug = str(entity.slug)
    model.updated_at = entity.updated_at


def formation_to_domain(model: FormationModel) -> Formation:
    return Formation(
        id=FormationId(model.id),
        name=FormationName(model.name),
        slug=Slug(model.slug),
        created_at=as_utc(model.created_at),
        updated_at=as_utc(model.updated_at),
    )


def chapter_to_model(entity: Chapter) -> ChapterModel:
    return ChapterModel(
        id=entity.id.value,
        formation_id=entity.formation_id.value,
        name=str(entity.name),
        slug=str(entity.slug),
        position=entity.position.value,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def apply_chapter(model: ChapterModel, entity: Chapter) -> None:
    model.formation_id = entity.formation_id.value
    model.name = str(entity.name)
    model.slug = str(entity.slug)
    model.position = entity.position.value
    model.updated_at = entity.updated_at


def chapter_to_domain(model: ChapterModel) -> Chapter:
    return Chapter(
        id=ChapterId(model.id),
        formation_id=FormationId(model.formation_id),
        name=ChapterName(model.name),
        slug=Slug(model.slug),
        position=Position(model.position),
        created_at=as_utc(model.created_at),
        updated_at=as_utc(model.updated_at),
    )


def video_to_model(entity: Video) -> VideoModel:
    return VideoModel(
        id=entity.id.value,
        chapter_id=entity.chapter_id.value,
        title=str(entity.title),
        filename=entity.filename,
        relative_path=str(entity.relative_path),
        position=entity.position.value,
        duration_seconds=entity.duration.value,
        kind=entity.kind,
        processing_status=entity.processing_status,
        transcription_status=entity.transcription_status,
        summary_status=entity.summary_status,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def apply_video(model: VideoModel, entity: Video) -> None:
    model.chapter_id = entity.chapter_id.value
    model.title = str(entity.title)
    model.filename = entity.filename
    model.relative_path = str(entity.relative_path)
    model.position = entity.position.value
    model.duration_seconds = entity.duration.value
    model.kind = entity.kind
    model.processing_status = entity.processing_status
    model.transcription_status = entity.transcription_status
    model.summary_status = entity.summary_status
    model.updated_at = entity.updated_at


def video_to_domain(model: VideoModel) -> Video:
    return Video(
        id=VideoId(model.id),
        chapter_id=ChapterId(model.chapter_id),
        title=VideoTitle(model.title),
        filename=model.filename,
        relative_path=RelativePath(model.relative_path),
        position=Position(model.position),
        duration=DurationSeconds(model.duration_seconds),
        kind=model.kind,
        processing_status=model.processing_status,
        transcription_status=model.transcription_status,
        summary_status=model.summary_status,
        created_at=as_utc(model.created_at),
        updated_at=as_utc(model.updated_at),
    )


def document_to_model(entity: Document) -> DocumentModel:
    return DocumentModel(
        id=entity.id.value,
        chapter_id=entity.chapter_id.value,
        video_id=entity.video_id.value if entity.video_id else None,
        title=str(entity.title),
        filename=entity.filename,
        relative_path=str(entity.relative_path),
        mime_type=entity.mime_type,
        position=entity.position.value,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def apply_document(model: DocumentModel, entity: Document) -> None:
    model.chapter_id = entity.chapter_id.value
    model.video_id = entity.video_id.value if entity.video_id else None
    model.title = str(entity.title)
    model.filename = entity.filename
    model.relative_path = str(entity.relative_path)
    model.mime_type = entity.mime_type
    model.position = entity.position.value
    model.updated_at = entity.updated_at


def document_to_domain(model: DocumentModel) -> Document:
    return Document(
        id=DocumentId(model.id),
        chapter_id=ChapterId(model.chapter_id),
        title=DocumentTitle(model.title),
        filename=model.filename,
        relative_path=RelativePath(model.relative_path),
        position=Position(model.position),
        mime_type=model.mime_type,
        video_id=VideoId(model.video_id) if model.video_id else None,
        created_at=as_utc(model.created_at),
        updated_at=as_utc(model.updated_at),
    )


def job_to_model(entity: Job) -> JobModel:
    return JobModel(
        id=entity.id.value,
        kind=entity.kind,
        status=entity.status,
        progress=entity.progress,
        message=entity.message,
        error=entity.error,
        video_id=entity.video_id.value if entity.video_id else None,
        formation_id=entity.formation_id.value if entity.formation_id else None,
        created_at=entity.created_at,
        started_at=entity.started_at,
        finished_at=entity.finished_at,
        updated_at=entity.updated_at,
    )


def apply_job(model: JobModel, entity: Job) -> None:
    model.kind = entity.kind
    model.status = entity.status
    model.progress = entity.progress
    model.message = entity.message
    model.error = entity.error
    model.video_id = entity.video_id.value if entity.video_id else None
    model.formation_id = entity.formation_id.value if entity.formation_id else None
    model.started_at = entity.started_at
    model.finished_at = entity.finished_at
    model.updated_at = entity.updated_at


def job_to_domain(model: JobModel) -> Job:
    return Job(
        id=JobId(model.id),
        kind=model.kind,
        status=model.status,
        progress=model.progress,
        message=model.message,
        error=model.error,
        video_id=VideoId(model.video_id) if model.video_id else None,
        formation_id=FormationId(model.formation_id) if model.formation_id else None,
        created_at=as_utc(model.created_at),
        started_at=as_utc(model.started_at) if model.started_at else None,
        finished_at=as_utc(model.finished_at) if model.finished_at else None,
        updated_at=as_utc(model.updated_at),
    )
