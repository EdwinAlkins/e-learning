"""Câblage use cases — content."""

from __future__ import annotations

from fastapi import Request

from e_learning.application.content.use_cases.ask_formation import AskFormation
from e_learning.application.content.use_cases.generate_summary import GenerateSummary
from e_learning.application.content.use_cases.get_summary import GetSummary
from e_learning.application.content.use_cases.get_transcription import GetTranscription
from e_learning.application.content.use_cases.index_formation import IndexFormation
from e_learning.application.content.use_cases.index_video_content import IndexVideoContent
from e_learning.application.content.use_cases.start_summary_generation import (
    StartSummaryGeneration,
)
from e_learning.application.content.use_cases.start_transcription import StartTranscription
from e_learning.application.content.use_cases.transcribe_video import TranscribeVideo
from e_learning.application.content.use_cases.update_summary import UpdateSummary
from e_learning.presentation.api.dependencies.repositories import (
    ChapterRepositoryDep,
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
    videos: VideoRepositoryDep, media_files: MediaFilesDep, jobs: JobRepositoryDep
) -> StartTranscription:
    return StartTranscription(videos, media_files, jobs)


def get_start_summary_generation(
    videos: VideoRepositoryDep, media_files: MediaFilesDep, jobs: JobRepositoryDep
) -> StartSummaryGeneration:
    return StartSummaryGeneration(videos, media_files, jobs)


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


def get_index_formation(
    request: Request,
    formations: FormationRepositoryDep,
    videos: VideoRepositoryDep,
    chapters: ChapterRepositoryDep,
    media_files: MediaFilesDep,
    embeddings: EmbeddingPortDep,
    vectors: VectorStoreDep,
) -> IndexFormation:
    index_video = get_index_video_content(
        request, videos, chapters, formations, media_files, embeddings, vectors
    )
    return IndexFormation(formations, videos, index_video)


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
