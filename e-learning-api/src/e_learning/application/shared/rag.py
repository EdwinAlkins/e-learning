"""Ports RAG — embeddings, store vectoriel, chat contextuel."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RagChunk:
    id: str
    formation_id: str
    chapter_id: str
    video_id: str
    title: str
    source: str  # transcription | summary
    chunk_index: int
    text: str
    vector: list[float]


@dataclass(frozen=True, slots=True)
class RagHit:
    formation_id: str
    chapter_id: str
    video_id: str
    title: str
    source: str
    chunk_index: int
    text: str
    score: float


class EmbeddingPort(ABC):
    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]: ...


class VectorStorePort(ABC):
    @abstractmethod
    async def ensure_collection(self) -> None: ...

    @abstractmethod
    async def upsert_chunks(self, chunks: list[RagChunk]) -> None: ...

    @abstractmethod
    async def delete_by_video(self, video_id: str) -> None: ...

    @abstractmethod
    async def search(
        self, formation_id: str, vector: list[float], *, top_k: int
    ) -> list[RagHit]: ...

    @abstractmethod
    async def count_by_formation(self, formation_id: str) -> int: ...


class ChatPort(ABC):
    @abstractmethod
    async def answer(self, *, question: str, context: str) -> str: ...
