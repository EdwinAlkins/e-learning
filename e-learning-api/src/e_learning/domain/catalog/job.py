"""Entité Job — tâches de fond (conversion, IA, RAG)."""

from __future__ import annotations

from datetime import UTC, datetime

from e_learning.domain.catalog.value_objects import FormationId, JobId, VideoId


def _now() -> datetime:
    return datetime.now(UTC)


class Job:
    KIND_MEDIA_CONVERSION = "media_conversion"
    KIND_TRANSCRIPTION = "transcription"
    KIND_SUMMARY = "summary"
    KIND_RAG_INDEX_VIDEO = "rag_index_video"
    KIND_RAG_INDEX_FORMATION = "rag_index_formation"

    STATUS_QUEUED = "queued"
    STATUS_RUNNING = "running"
    STATUS_SUCCEEDED = "succeeded"
    STATUS_FAILED = "failed"
    STATUS_CANCELLED = "cancelled"

    ACTIVE_STATUSES = frozenset({STATUS_QUEUED, STATUS_RUNNING})

    def __init__(
        self,
        *,
        id: JobId,
        kind: str,
        status: str,
        progress: int,
        message: str,
        error: str | None,
        video_id: VideoId | None,
        formation_id: FormationId | None,
        created_at: datetime,
        started_at: datetime | None,
        finished_at: datetime | None,
        updated_at: datetime,
    ) -> None:
        self.id = id
        self.kind = kind
        self.status = status
        self.progress = progress
        self.message = message
        self.error = error
        self.video_id = video_id
        self.formation_id = formation_id
        self.created_at = created_at
        self.started_at = started_at
        self.finished_at = finished_at
        self.updated_at = updated_at

    @classmethod
    def create(
        cls,
        *,
        kind: str,
        video_id: VideoId | None = None,
        formation_id: FormationId | None = None,
        message: str = "",
    ) -> Job:
        now = _now()
        return cls(
            id=JobId.generate(),
            kind=kind,
            status=cls.STATUS_QUEUED,
            progress=0,
            message=message,
            error=None,
            video_id=video_id,
            formation_id=formation_id,
            created_at=now,
            started_at=None,
            finished_at=None,
            updated_at=now,
        )

    @property
    def is_active(self) -> bool:
        return self.status in self.ACTIVE_STATUSES

    def mark_running(self, *, message: str = "") -> None:
        now = _now()
        self.status = self.STATUS_RUNNING
        self.started_at = now
        if message:
            self.message = message
        self.updated_at = now

    def update_progress(self, progress: int, message: str | None = None) -> None:
        self.progress = max(0, min(100, int(progress)))
        if message is not None:
            self.message = message
        self.updated_at = _now()

    def mark_succeeded(self, *, message: str = "Terminé") -> None:
        now = _now()
        self.status = self.STATUS_SUCCEEDED
        self.progress = 100
        self.message = message
        self.error = None
        self.finished_at = now
        self.updated_at = now

    def mark_failed(self, error: str, *, message: str = "Échec") -> None:
        now = _now()
        self.status = self.STATUS_FAILED
        self.message = message
        self.error = error[:2000] if error else None
        self.finished_at = now
        self.updated_at = now

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Job) and other.id == self.id

    def __hash__(self) -> int:
        return hash(self.id)
