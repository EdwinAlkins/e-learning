"""DTO / commands — contexte ``learning``."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from e_learning.domain.learning.entities import Note, Progress


@dataclass(frozen=True, slots=True)
class CreateNoteCommand:
    user_id: str
    video_id: str
    timecode: float
    content: str


@dataclass(frozen=True, slots=True)
class UpdateNoteCommand:
    note_id: str
    user_id: str
    content: str


@dataclass(frozen=True, slots=True)
class NoteDTO:
    id: str
    video_id: str
    timecode: float
    content: str
    created_at: datetime

    @classmethod
    def from_entity(cls, note: Note) -> NoteDTO:
        return cls(
            id=str(note.id),
            video_id=str(note.video_id),
            timecode=note.timecode.value,
            content=str(note.content),
            created_at=note.created_at,
        )


@dataclass(frozen=True, slots=True)
class UpsertProgressCommand:
    user_id: str
    video_id: str
    last_position: float


@dataclass(frozen=True, slots=True)
class ProgressDTO:
    last_position: float

    @classmethod
    def from_entity(cls, progress: Progress) -> ProgressDTO:
        return cls(last_position=progress.last_position.value)


@dataclass(frozen=True, slots=True)
class VideoProgressDTO:
    id: str
    title: str
    progress_percentage: float


@dataclass(frozen=True, slots=True)
class ChapterProgressDTO:
    name: str
    videos: list[VideoProgressDTO]
    progress_percentage: float


@dataclass(frozen=True, slots=True)
class FormationProgressDTO:
    name: str
    chapters: list[ChapterProgressDTO]
    progress_percentage: float
