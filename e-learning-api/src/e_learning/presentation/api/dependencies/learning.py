"""Câblage use cases — learning."""

from __future__ import annotations

from e_learning.application.learning.use_cases.create_note import CreateNote
from e_learning.application.learning.use_cases.delete_note import DeleteNote
from e_learning.application.learning.use_cases.get_formation_progress import GetFormationProgress
from e_learning.application.learning.use_cases.get_progress import GetProgress
from e_learning.application.learning.use_cases.list_formations_progress import (
    ListFormationsProgress,
)
from e_learning.application.learning.use_cases.list_notes import ListNotes
from e_learning.application.learning.use_cases.update_note import UpdateNote
from e_learning.application.learning.use_cases.upsert_progress import UpsertProgress
from e_learning.presentation.api.dependencies.repositories import (
    ChapterRepositoryDep,
    FormationRepositoryDep,
    NoteRepositoryDep,
    ProgressRepositoryDep,
    UserRepositoryDep,
    VideoRepositoryDep,
)


def get_create_note(
    notes: NoteRepositoryDep, users: UserRepositoryDep, videos: VideoRepositoryDep
) -> CreateNote:
    return CreateNote(notes, users, videos)


def get_list_notes(notes: NoteRepositoryDep) -> ListNotes:
    return ListNotes(notes)


def get_update_note(notes: NoteRepositoryDep) -> UpdateNote:
    return UpdateNote(notes)


def get_delete_note(notes: NoteRepositoryDep) -> DeleteNote:
    return DeleteNote(notes)


def get_get_progress(progress: ProgressRepositoryDep) -> GetProgress:
    return GetProgress(progress)


def get_upsert_progress(
    progress: ProgressRepositoryDep, users: UserRepositoryDep, videos: VideoRepositoryDep
) -> UpsertProgress:
    return UpsertProgress(progress, users, videos)


def get_get_formation_progress(
    formations: FormationRepositoryDep,
    chapters: ChapterRepositoryDep,
    videos: VideoRepositoryDep,
    progress: ProgressRepositoryDep,
) -> GetFormationProgress:
    return GetFormationProgress(formations, chapters, videos, progress)


def get_list_formations_progress(
    formations: FormationRepositoryDep,
    chapters: ChapterRepositoryDep,
    videos: VideoRepositoryDep,
    progress: ProgressRepositoryDep,
) -> ListFormationsProgress:
    return ListFormationsProgress(formations, chapters, videos, progress)
