"""Câblage port → adaptateur (repositories)."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from e_learning.domain.catalog.repository import (
    ChapterRepository,
    DocumentRepository,
    FormationRepository,
    JobRepository,
    VideoRepository,
)
from e_learning.domain.learning.repository import NoteRepository, ProgressRepository
from e_learning.domain.user.repository import UserRepository
from e_learning.infrastructure.persistence.catalog.repository import (
    SqlAlchemyChapterRepository,
    SqlAlchemyDocumentRepository,
    SqlAlchemyFormationRepository,
    SqlAlchemyJobRepository,
    SqlAlchemyVideoRepository,
)
from e_learning.infrastructure.persistence.learning.repository import (
    SqlAlchemyNoteRepository,
    SqlAlchemyProgressRepository,
)
from e_learning.infrastructure.persistence.user.repository import SqlAlchemyUserRepository
from e_learning.presentation.api.dependencies.session import SessionDep


def get_user_repository(session: SessionDep) -> UserRepository:
    return SqlAlchemyUserRepository(session)


def get_formation_repository(session: SessionDep) -> FormationRepository:
    return SqlAlchemyFormationRepository(session)


def get_chapter_repository(session: SessionDep) -> ChapterRepository:
    return SqlAlchemyChapterRepository(session)


def get_video_repository(session: SessionDep) -> VideoRepository:
    return SqlAlchemyVideoRepository(session)


def get_document_repository(session: SessionDep) -> DocumentRepository:
    return SqlAlchemyDocumentRepository(session)


def get_job_repository(session: SessionDep) -> JobRepository:
    return SqlAlchemyJobRepository(session)


def get_note_repository(session: SessionDep) -> NoteRepository:
    return SqlAlchemyNoteRepository(session)


def get_progress_repository(session: SessionDep) -> ProgressRepository:
    return SqlAlchemyProgressRepository(session)


UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]
FormationRepositoryDep = Annotated[FormationRepository, Depends(get_formation_repository)]
ChapterRepositoryDep = Annotated[ChapterRepository, Depends(get_chapter_repository)]
VideoRepositoryDep = Annotated[VideoRepository, Depends(get_video_repository)]
DocumentRepositoryDep = Annotated[DocumentRepository, Depends(get_document_repository)]
JobRepositoryDep = Annotated[JobRepository, Depends(get_job_repository)]
NoteRepositoryDep = Annotated[NoteRepository, Depends(get_note_repository)]
ProgressRepositoryDep = Annotated[ProgressRepository, Depends(get_progress_repository)]
