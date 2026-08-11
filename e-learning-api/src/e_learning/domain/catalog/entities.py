"""Entités du bounded context ``catalog``."""

from __future__ import annotations

from datetime import UTC, datetime

from e_learning.domain.catalog.value_objects import (
    ChapterId,
    ChapterName,
    DocumentId,
    DocumentTitle,
    DurationSeconds,
    FormationId,
    FormationName,
    Position,
    RelativePath,
    Slug,
    VideoId,
    VideoTitle,
)


def _now() -> datetime:
    return datetime.now(UTC)


class Formation:
    def __init__(
        self,
        *,
        id: FormationId,
        name: FormationName,
        slug: Slug,
        created_at: datetime,
        updated_at: datetime,
    ) -> None:
        self.id = id
        self.name = name
        self.slug = slug
        self.created_at = created_at
        self.updated_at = updated_at

    @classmethod
    def create(cls, *, name: FormationName, slug: Slug | None = None) -> Formation:
        now = _now()
        return cls(
            id=FormationId.generate(),
            name=name,
            slug=slug or Slug.from_name(str(name)),
            created_at=now,
            updated_at=now,
        )

    def rename(self, name: FormationName, *, slug: Slug | None = None) -> None:
        self.name = name
        if slug is not None:
            self.slug = slug
        self.updated_at = _now()

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Formation) and other.id == self.id

    def __hash__(self) -> int:
        return hash(self.id)


class Chapter:
    def __init__(
        self,
        *,
        id: ChapterId,
        formation_id: FormationId,
        name: ChapterName,
        slug: Slug,
        position: Position,
        created_at: datetime,
        updated_at: datetime,
    ) -> None:
        self.id = id
        self.formation_id = formation_id
        self.name = name
        self.slug = slug
        self.position = position
        self.created_at = created_at
        self.updated_at = updated_at

    @classmethod
    def create(
        cls,
        *,
        formation_id: FormationId,
        name: ChapterName,
        position: Position,
        slug: Slug | None = None,
    ) -> Chapter:
        now = _now()
        return cls(
            id=ChapterId.generate(),
            formation_id=formation_id,
            name=name,
            slug=slug or Slug.from_name(str(name)),
            position=position,
            created_at=now,
            updated_at=now,
        )

    def rename(self, name: ChapterName, *, slug: Slug | None = None) -> None:
        self.name = name
        if slug is not None:
            self.slug = slug
        self.updated_at = _now()

    def move_to(self, position: Position) -> None:
        self.position = position
        self.updated_at = _now()

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Chapter) and other.id == self.id

    def __hash__(self) -> int:
        return hash(self.id)


class Video:
    KIND_VIDEO = "video"
    KIND_AUDIO = "audio"
    STATUS_READY = "ready"
    STATUS_PROCESSING = "processing"
    STATUS_FAILED = "failed"
    AI_NONE = "none"
    AI_PROCESSING = "processing"
    AI_READY = "ready"
    AI_FAILED = "failed"

    def __init__(
        self,
        *,
        id: VideoId,
        chapter_id: ChapterId,
        title: VideoTitle,
        filename: str,
        relative_path: RelativePath,
        position: Position,
        duration: DurationSeconds,
        created_at: datetime,
        updated_at: datetime,
        kind: str = KIND_VIDEO,
        processing_status: str = STATUS_READY,
        transcription_status: str = AI_NONE,
        summary_status: str = AI_NONE,
    ) -> None:
        self.id = id
        self.chapter_id = chapter_id
        self.title = title
        self.filename = filename
        self.relative_path = relative_path
        self.position = position
        self.duration = duration
        self.kind = kind
        self.processing_status = processing_status
        self.transcription_status = transcription_status
        self.summary_status = summary_status
        self.created_at = created_at
        self.updated_at = updated_at

    @classmethod
    def create(
        cls,
        *,
        chapter_id: ChapterId,
        title: VideoTitle,
        filename: str,
        relative_path: RelativePath,
        position: Position,
        duration: DurationSeconds,
        kind: str = KIND_VIDEO,
        processing_status: str = STATUS_READY,
        transcription_status: str = AI_NONE,
        summary_status: str = AI_NONE,
    ) -> Video:
        now = _now()
        return cls(
            id=VideoId.generate(),
            chapter_id=chapter_id,
            title=title,
            filename=filename,
            relative_path=relative_path,
            position=position,
            duration=duration,
            kind=kind,
            processing_status=processing_status,
            transcription_status=transcription_status,
            summary_status=summary_status,
            created_at=now,
            updated_at=now,
        )

    def rename(self, title: VideoTitle, *, filename: str | None = None) -> None:
        self.title = title
        if filename is not None:
            self.filename = filename
        self.updated_at = _now()

    def relocate(
        self,
        *,
        chapter_id: ChapterId,
        position: Position,
        relative_path: RelativePath,
        filename: str | None = None,
    ) -> None:
        self.chapter_id = chapter_id
        self.position = position
        self.relative_path = relative_path
        if filename is not None:
            self.filename = filename
        self.updated_at = _now()

    def update_relative_path(self, relative_path: RelativePath) -> None:
        self.relative_path = relative_path
        self.updated_at = _now()

    def move_to(self, position: Position) -> None:
        self.position = position
        self.updated_at = _now()

    def update_duration(self, duration: DurationSeconds) -> None:
        self.duration = duration
        self.updated_at = _now()

    def set_kind(self, kind: str) -> None:
        self.kind = kind
        self.updated_at = _now()

    def mark_processing(self) -> None:
        self.processing_status = self.STATUS_PROCESSING
        self.updated_at = _now()

    def mark_ready(self) -> None:
        self.processing_status = self.STATUS_READY
        self.updated_at = _now()

    def mark_failed(self) -> None:
        self.processing_status = self.STATUS_FAILED
        self.updated_at = _now()

    def finalize_file(
        self,
        *,
        filename: str,
        relative_path: RelativePath,
        duration: DurationSeconds,
    ) -> None:
        self.filename = filename
        self.relative_path = relative_path
        self.duration = duration
        self.processing_status = self.STATUS_READY
        self.updated_at = _now()

    def set_transcription_status(self, status: str) -> None:
        self.transcription_status = status
        self.updated_at = _now()

    def set_summary_status(self, status: str) -> None:
        self.summary_status = status
        self.updated_at = _now()

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Video) and other.id == self.id

    def __hash__(self) -> int:
        return hash(self.id)


class Document:
    def __init__(
        self,
        *,
        id: DocumentId,
        chapter_id: ChapterId,
        title: DocumentTitle,
        filename: str,
        relative_path: RelativePath,
        position: Position,
        mime_type: str | None,
        video_id: VideoId | None,
        created_at: datetime,
        updated_at: datetime,
    ) -> None:
        self.id = id
        self.chapter_id = chapter_id
        self.title = title
        self.filename = filename
        self.relative_path = relative_path
        self.position = position
        self.mime_type = mime_type
        self.video_id = video_id
        self.created_at = created_at
        self.updated_at = updated_at

    @classmethod
    def create(
        cls,
        *,
        chapter_id: ChapterId,
        title: DocumentTitle,
        filename: str,
        relative_path: RelativePath,
        position: Position,
        mime_type: str | None = None,
        video_id: VideoId | None = None,
    ) -> Document:
        now = _now()
        return cls(
            id=DocumentId.generate(),
            chapter_id=chapter_id,
            title=title,
            filename=filename,
            relative_path=relative_path,
            position=position,
            mime_type=mime_type,
            video_id=video_id,
            created_at=now,
            updated_at=now,
        )

    def rename(self, title: DocumentTitle) -> None:
        self.title = title
        self.updated_at = _now()

    def update_relative_path(self, relative_path: RelativePath) -> None:
        self.relative_path = relative_path
        self.updated_at = _now()

    def relocate(
        self,
        *,
        chapter_id: ChapterId,
        position: Position,
        relative_path: RelativePath,
        filename: str | None = None,
    ) -> None:
        self.chapter_id = chapter_id
        self.position = position
        self.relative_path = relative_path
        if filename is not None:
            self.filename = filename
        self.updated_at = _now()

    def attach_video(self, video_id: VideoId | None) -> None:
        self.video_id = video_id
        self.updated_at = _now()

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Document) and other.id == self.id

    def __hash__(self) -> int:
        return hash(self.id)
