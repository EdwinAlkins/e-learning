"""Câblage use cases — catalog."""

from __future__ import annotations

from e_learning.application.catalog.use_cases.create_chapter import CreateChapter
from e_learning.application.catalog.use_cases.create_document import CreateDocument
from e_learning.application.catalog.use_cases.create_formation import CreateFormation
from e_learning.application.catalog.use_cases.create_video import CreateVideo
from e_learning.application.catalog.use_cases.delete_chapter import DeleteChapter
from e_learning.application.catalog.use_cases.delete_document import DeleteDocument
from e_learning.application.catalog.use_cases.delete_formation import DeleteFormation
from e_learning.application.catalog.use_cases.delete_video import DeleteVideo
from e_learning.application.catalog.use_cases.get_document_path import GetDocumentPath
from e_learning.application.catalog.use_cases.get_formation import GetFormation
from e_learning.application.catalog.use_cases.get_video_path import GetVideoPath
from e_learning.application.catalog.use_cases.list_chapter_documents import ListChapterDocuments
from e_learning.application.catalog.use_cases.list_formations import ListFormations
from e_learning.application.catalog.use_cases.move_video import MoveVideo
from e_learning.application.catalog.use_cases.reconcile_catalog import ReconcileCatalog
from e_learning.application.catalog.use_cases.rename_chapter import RenameChapter
from e_learning.application.catalog.use_cases.rename_formation import RenameFormation
from e_learning.application.catalog.use_cases.rename_video import RenameVideo
from e_learning.application.catalog.use_cases.reorder_chapters import ReorderChapters
from e_learning.application.catalog.use_cases.reorder_videos import ReorderVideos
from e_learning.application.catalog.use_cases.start_media_conversion import StartMediaConversion
from e_learning.application.catalog.use_cases.update_document import UpdateDocument
from e_learning.presentation.api.dependencies.messaging import JobPublisherDep
from e_learning.presentation.api.dependencies.repositories import (
    ChapterRepositoryDep,
    DocumentRepositoryDep,
    FormationRepositoryDep,
    JobRepositoryDep,
    VideoRepositoryDep,
)
from e_learning.presentation.api.dependencies.storage import CatalogStorageDep, VectorStoreDep


def get_list_formations(
    formations: FormationRepositoryDep,
    chapters: ChapterRepositoryDep,
    videos: VideoRepositoryDep,
    documents: DocumentRepositoryDep,
    jobs: JobRepositoryDep,
) -> ListFormations:
    return ListFormations(formations, chapters, videos, documents, jobs)


def get_get_formation(
    formations: FormationRepositoryDep,
    chapters: ChapterRepositoryDep,
    videos: VideoRepositoryDep,
    documents: DocumentRepositoryDep,
    jobs: JobRepositoryDep,
) -> GetFormation:
    return GetFormation(formations, chapters, videos, documents, jobs)


def get_create_formation(
    formations: FormationRepositoryDep, storage: CatalogStorageDep
) -> CreateFormation:
    return CreateFormation(formations, storage)


def get_rename_formation(
    formations: FormationRepositoryDep,
    chapters: ChapterRepositoryDep,
    videos: VideoRepositoryDep,
    documents: DocumentRepositoryDep,
    storage: CatalogStorageDep,
    jobs: JobRepositoryDep,
) -> RenameFormation:
    return RenameFormation(formations, chapters, videos, documents, storage, jobs)


def get_delete_formation(
    formations: FormationRepositoryDep, storage: CatalogStorageDep
) -> DeleteFormation:
    return DeleteFormation(formations, storage)


def get_create_chapter(
    formations: FormationRepositoryDep,
    chapters: ChapterRepositoryDep,
    storage: CatalogStorageDep,
) -> CreateChapter:
    return CreateChapter(formations, chapters, storage)


def get_rename_chapter(
    formations: FormationRepositoryDep,
    chapters: ChapterRepositoryDep,
    videos: VideoRepositoryDep,
    documents: DocumentRepositoryDep,
    storage: CatalogStorageDep,
) -> RenameChapter:
    return RenameChapter(formations, chapters, videos, documents, storage)


def get_delete_chapter(
    formations: FormationRepositoryDep,
    chapters: ChapterRepositoryDep,
    storage: CatalogStorageDep,
) -> DeleteChapter:
    return DeleteChapter(formations, chapters, storage)


def get_create_video(
    formations: FormationRepositoryDep,
    chapters: ChapterRepositoryDep,
    videos: VideoRepositoryDep,
    storage: CatalogStorageDep,
    jobs: JobRepositoryDep,
    publisher: JobPublisherDep,
) -> CreateVideo:
    return CreateVideo(formations, chapters, videos, storage, jobs, publisher)


def get_rename_video(
    formations: FormationRepositoryDep,
    chapters: ChapterRepositoryDep,
    videos: VideoRepositoryDep,
    storage: CatalogStorageDep,
    jobs: JobRepositoryDep,
    publisher: JobPublisherDep,
) -> RenameVideo:
    return RenameVideo(formations, chapters, videos, storage, jobs, publisher)


def get_delete_video(videos: VideoRepositoryDep, storage: CatalogStorageDep) -> DeleteVideo:
    return DeleteVideo(videos, storage)


def get_reorder_videos(
    chapters: ChapterRepositoryDep,
    videos: VideoRepositoryDep,
    documents: DocumentRepositoryDep,
) -> ReorderVideos:
    return ReorderVideos(chapters, videos, documents)


def get_reorder_chapters(
    formations: FormationRepositoryDep,
    chapters: ChapterRepositoryDep,
    videos: VideoRepositoryDep,
    documents: DocumentRepositoryDep,
    jobs: JobRepositoryDep,
) -> ReorderChapters:
    return ReorderChapters(formations, chapters, videos, documents, jobs)


def get_move_video(
    formations: FormationRepositoryDep,
    chapters: ChapterRepositoryDep,
    videos: VideoRepositoryDep,
    documents: DocumentRepositoryDep,
    storage: CatalogStorageDep,
    jobs: JobRepositoryDep,
) -> MoveVideo:
    return MoveVideo(formations, chapters, videos, documents, storage, jobs)


def get_list_chapter_documents(
    chapters: ChapterRepositoryDep, documents: DocumentRepositoryDep
) -> ListChapterDocuments:
    return ListChapterDocuments(chapters, documents)


def get_create_document(
    formations: FormationRepositoryDep,
    chapters: ChapterRepositoryDep,
    videos: VideoRepositoryDep,
    documents: DocumentRepositoryDep,
    storage: CatalogStorageDep,
) -> CreateDocument:
    return CreateDocument(formations, chapters, videos, documents, storage)


def get_update_document(
    documents: DocumentRepositoryDep, videos: VideoRepositoryDep
) -> UpdateDocument:
    return UpdateDocument(documents, videos)


def get_delete_document(
    documents: DocumentRepositoryDep,
    storage: CatalogStorageDep,
    vectors: VectorStoreDep,
) -> DeleteDocument:
    return DeleteDocument(documents, storage, vectors)


def get_get_video_path(videos: VideoRepositoryDep, storage: CatalogStorageDep) -> GetVideoPath:
    return GetVideoPath(videos, storage)


def get_get_document_path(
    documents: DocumentRepositoryDep, storage: CatalogStorageDep
) -> GetDocumentPath:
    return GetDocumentPath(documents, storage)


def get_reconcile_catalog(
    formations: FormationRepositoryDep,
    chapters: ChapterRepositoryDep,
    videos: VideoRepositoryDep,
    documents: DocumentRepositoryDep,
    storage: CatalogStorageDep,
) -> ReconcileCatalog:
    return ReconcileCatalog(formations, chapters, videos, documents, storage)


def get_start_media_conversion(
    videos: VideoRepositoryDep,
    storage: CatalogStorageDep,
    jobs: JobRepositoryDep,
    publisher: JobPublisherDep,
) -> StartMediaConversion:
    return StartMediaConversion(videos, storage, jobs, publisher)
