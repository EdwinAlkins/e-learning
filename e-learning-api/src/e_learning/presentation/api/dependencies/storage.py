"""Câblage des ports techniques (storage, AI, media)."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from e_learning.application.shared.media import (
    MediaConvertPort,
    MediaFilePort,
    SummaryPort,
    TranscriptionPort,
)
from e_learning.application.shared.rag import ChatPort, EmbeddingPort, VectorStorePort
from e_learning.application.shared.storage import CatalogStoragePort
from e_learning.infrastructure.ai.summary import GeminiSummaryAdapter, OpenAPISummaryAdapter
from e_learning.infrastructure.ai.whisper_transcription import WhisperTranscriptionAdapter
from e_learning.infrastructure.config import SummaryStrategyName


def get_catalog_storage(request: Request) -> CatalogStoragePort:
    return request.app.state.catalog_storage


def get_media_files(request: Request) -> MediaFilePort:
    return request.app.state.media_files


def get_media_converter(request: Request) -> MediaConvertPort:
    return request.app.state.media_converter


def get_transcription_port() -> TranscriptionPort:
    return WhisperTranscriptionAdapter()


def get_summary_port(request: Request) -> SummaryPort:
    settings = request.app.state.settings
    if settings.summary_strategy is SummaryStrategyName.GEMINI:
        return GeminiSummaryAdapter()
    return OpenAPISummaryAdapter(settings)


def get_embedding_port(request: Request) -> EmbeddingPort:
    return request.app.state.embeddings


def get_vector_store(request: Request) -> VectorStorePort:
    return request.app.state.vector_store


def get_chat_port(request: Request) -> ChatPort:
    return request.app.state.chat


CatalogStorageDep = Annotated[CatalogStoragePort, Depends(get_catalog_storage)]
MediaFilesDep = Annotated[MediaFilePort, Depends(get_media_files)]
MediaConvertDep = Annotated[MediaConvertPort, Depends(get_media_converter)]
TranscriptionPortDep = Annotated[TranscriptionPort, Depends(get_transcription_port)]
SummaryPortDep = Annotated[SummaryPort, Depends(get_summary_port)]
EmbeddingPortDep = Annotated[EmbeddingPort, Depends(get_embedding_port)]
VectorStoreDep = Annotated[VectorStorePort, Depends(get_vector_store)]
ChatPortDep = Annotated[ChatPort, Depends(get_chat_port)]
