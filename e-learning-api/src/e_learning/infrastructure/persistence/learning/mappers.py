"""Mappers learning domaine ↔ ORM."""

from __future__ import annotations

from e_learning.domain.catalog.value_objects import VideoId
from e_learning.domain.learning.entities import Note, Progress
from e_learning.domain.learning.value_objects import (
    LastPositionSeconds,
    NoteContent,
    NoteId,
    ProgressId,
    TimecodeSeconds,
)
from e_learning.domain.user.value_objects import UserId
from e_learning.infrastructure.persistence.converters import as_utc
from e_learning.infrastructure.persistence.learning.models import NoteModel, ProgressModel


def note_to_model(note: Note) -> NoteModel:
    return NoteModel(
        id=note.id.value,
        user_id=note.user_id.value,
        video_id=note.video_id.value,
        timecode_seconds=note.timecode.value,
        content=str(note.content),
        created_at=note.created_at,
    )


def apply_note(model: NoteModel, note: Note) -> None:
    model.content = str(note.content)
    model.timecode_seconds = note.timecode.value


def note_to_domain(model: NoteModel) -> Note:
    return Note(
        id=NoteId(model.id),
        user_id=UserId(model.user_id),
        video_id=VideoId(model.video_id),
        timecode=TimecodeSeconds(model.timecode_seconds),
        content=NoteContent(model.content),
        created_at=as_utc(model.created_at),
    )


def progress_to_model(progress: Progress) -> ProgressModel:
    return ProgressModel(
        id=progress.id.value,
        user_id=progress.user_id.value,
        video_id=progress.video_id.value,
        last_position_seconds=progress.last_position.value,
        updated_at=progress.updated_at,
    )


def apply_progress(model: ProgressModel, progress: Progress) -> None:
    model.last_position_seconds = progress.last_position.value
    model.updated_at = progress.updated_at


def progress_to_domain(model: ProgressModel) -> Progress:
    return Progress(
        id=ProgressId(model.id),
        user_id=UserId(model.user_id),
        video_id=VideoId(model.video_id),
        last_position=LastPositionSeconds(model.last_position_seconds),
        updated_at=as_utc(model.updated_at),
    )
