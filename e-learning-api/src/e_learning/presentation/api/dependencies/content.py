"""Câblage use cases — content."""

from __future__ import annotations

from fastapi import Request

from e_learning.application.content.use_cases.ask_formation import AskFormation
from e_learning.application.content.use_cases.generate_summary import GenerateSummary
from e_learning.application.content.use_cases.get_summary import GetSummary
from e_learning.application.content.use_cases.get_transcription import GetTranscription
from e_learning.application.content.use_cases.index_document_content import IndexDocumentContent
from e_learning.application.content.use_cases.index_formation import IndexFormation
from e_learning.application.content.use_cases.index_video_content import IndexVideoContent
from e_learning.application.content.use_cases.start_formation_index import StartFormationIndex
from e_learning.application.content.use_cases.start_summary_generation import (
    StartSummaryGeneration,
)
from e_learning.application.content.use_cases.start_transcription import StartTranscription
from e_learning.application.content.use_cases.transcribe_video import TranscribeVideo
from e_learning.application.content.use_cases.update_summary import UpdateSummary
from e_learning.infrastructure.ai.document_text import FilesystemDocumentTextExtractor
from e_learning.presentation.api.dependencies.messaging import JobPublisherDep
from e_learning.presentation.api.dependencies.repositories import (
    ChapterRepositoryDep,
    DocumentRepositoryDep,
    FormationRepositoryDep,
    JobRepositoryDep,
    VideoRepositoryDep,
)
from e_learning.presentation.api.dependencies.storage import (
    CatalogStorageDep,
    ChatPortDep,
    EmbeddingPortDep,
    MediaFilesDep,
    SummaryPortDep,
    TranscriptionPortDep,
    VectorStoreDep,
)


def get_get_summary(videos: VideoRepositoryDep, media_files: MediaFilesDep) -> GetSummary:
    return GetSummary(videos, media_files)


def get_update_summary(videos: VideoRepositoryDep, media_files: MediaFilesDep) -> UpdateSummary:
    return UpdateSummary(videos, media_files)


def get_generate_summary(
    videos: VideoRepositoryDep, media_files: MediaFilesDep, summary: SummaryPortDep
) -> GenerateSummary:
    return GenerateSummary(videos, media_files, summary)


def get_transcribe_video(
    videos: VideoRepositoryDep,
    storage: CatalogStorageDep,
    media_files: MediaFilesDep,
    transcription: TranscriptionPortDep,
) -> TranscribeVideo:
    return TranscribeVideo(videos, storage, media_files, transcription)


def get_start_transcription(
    videos: VideoRepositoryDep,
    media_files: MediaFilesDep,
    jobs: JobRepositoryDep,
    publisher: JobPublisherDep,
) -> StartTranscription:
    return StartTranscription(videos, media_files, jobs, publisher)


def get_start_summary_generation(
    videos: VideoRepositoryDep,
    media_files: MediaFilesDep,
    jobs: JobRepositoryDep,
    publisher: JobPublisherDep,
) -> StartSummaryGeneration:
    return StartSummaryGeneration(videos, media_files, jobs, publisher)


def get_start_formation_index(
    formations: FormationRepositoryDep,
    jobs: JobRepositoryDep,
    publisher: JobPublisherDep,
) -> StartFormationIndex:
    return StartFormationIndex(formations, jobs, publisher)


def get_get_transcription(
    videos: VideoRepositoryDep, media_files: MediaFilesDep
) -> GetTranscription:
    return GetTranscription(videos, media_files)


def get_index_video_content(
    request: Request,
    videos: VideoRepositoryDep,
    chapters: ChapterRepositoryDep,
    formations: FormationRepositoryDep,
    media_files: MediaFilesDep,
    embeddings: EmbeddingPortDep,
    vectors: VectorStoreDep,
) -> IndexVideoContent:
    settings = request.app.state.settings
    return IndexVideoContent(
        videos,
        chapters,
        formations,
        media_files,
        embeddings,
        vectors,
        chunk_size=settings.rag_chunk_size,
        chunk_overlap=settings.rag_chunk_overlap,
    )


def get_index_document_content(
    request: Request,
    documents: DocumentRepositoryDep,
    chapters: ChapterRepositoryDep,
    formations: FormationRepositoryDep,
    storage: CatalogStorageDep,
    embeddings: EmbeddingPortDep,
    vectors: VectorStoreDep,
) -> IndexDocumentContent:
    settings = request.app.state.settings
    return IndexDocumentContent(
        documents,
        chapters,
        formations,
        storage,
        FilesystemDocumentTextExtractor(),
        embeddings,
        vectors,
        chunk_size=settings.rag_chunk_size,
        chunk_overlap=settings.rag_chunk_overlap,
    )


def get_index_formation(
    request: Request,
    formations: FormationRepositoryDep,
    videos: VideoRepositoryDep,
    chapters: ChapterRepositoryDep,
    documents: DocumentRepositoryDep,
    media_files: MediaFilesDep,
    storage: CatalogStorageDep,
    embeddings: EmbeddingPortDep,
    vectors: VectorStoreDep,
) -> IndexFormation:
    index_video = get_index_video_content(
        request, videos, chapters, formations, media_files, embeddings, vectors
    )
    index_document = get_index_document_content(
        request, documents, chapters, formations, storage, embeddings, vectors
    )
    return IndexFormation(
        formations, videos, chapters, documents, index_video, index_document
    )


def get_ask_formation(
    request: Request,
    formations: FormationRepositoryDep,
    embeddings: EmbeddingPortDep,
    vectors: VectorStoreDep,
    chat: ChatPortDep,
) -> AskFormation:
    return AskFormation(
        formations,
        embeddings,
        vectors,
        chat,
        top_k=request.app.state.settings.rag_top_k,
    )
