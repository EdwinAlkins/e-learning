"""Tests — chunker + AskFormation RAG."""

from __future__ import annotations

import pytest

from e_learning.application.content.chunker import chunk_point_id, chunk_text
from e_learning.application.content.dto import AskFormationCommand
from e_learning.application.content.use_cases.ask_formation import AskFormation
from e_learning.application.shared.errors import RagEmptyIndexError
from e_learning.application.shared.rag import ChatPort, EmbeddingPort, RagHit, VectorStorePort
from e_learning.domain.catalog.entities import Formation
from e_learning.domain.catalog.value_objects import FormationName
from tests.unit.application._fakes import FakeFormationRepository


def test_chunk_text_respects_size_and_overlap() -> None:
    text = "a" * 50
    chunks = chunk_text(text, chunk_size=20, overlap=5)
    assert len(chunks) >= 3
    assert all(len(c) <= 20 for c in chunks)
    # Chevauchement : fin d'un chunk = début du suivant
    assert chunks[0][-5:] == chunks[1][:5]


def test_chunk_text_short_returns_single() -> None:
    assert chunk_text("hello world", chunk_size=100, overlap=10) == ["hello world"]


def test_chunk_text_rejects_bad_params() -> None:
    with pytest.raises(ValueError):
        chunk_text("x", chunk_size=10, overlap=10)


def test_chunk_point_id_stable() -> None:
    a = chunk_point_id("vid-1", "transcription", 0)
    b = chunk_point_id("vid-1", "transcription", 0)
    c = chunk_point_id("vid-1", "transcription", 1)
    assert a == b
    assert a != c


class FakeEmbeddings(EmbeddingPort):
    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[float(len(t))] + [0.0] * 2 for t in texts]


class FakeVectors(VectorStorePort):
    def __init__(self, hits: list[RagHit] | None = None, count: int = 0) -> None:
        self._hits = hits or []
        self._count = count

    async def ensure_collection(self) -> None:
        return None

    async def upsert_chunks(self, chunks: list) -> None:
        return None

    async def delete_by_video(self, video_id: str) -> None:
        return None

    async def search(self, formation_id: str, vector: list[float], *, top_k: int) -> list[RagHit]:
        return [h for h in self._hits if h.formation_id == formation_id][:top_k]

    async def count_by_formation(self, formation_id: str) -> int:
        return self._count


class FakeChat(ChatPort):
    async def answer(self, *, question: str, context: str) -> str:
        return f"Réponse à « {question} » avec {len(context)} chars de contexte"


async def test_ask_formation_returns_citations_filtered() -> None:
    formations = FakeFormationRepository()
    formation = Formation.create(name=FormationName("Algo"))
    await formations.save(formation)
    fid = str(formation.id)

    hits = [
        RagHit(
            formation_id=fid,
            chapter_id="ch-1",
            video_id="vid-1",
            title="Intro",
            source="transcription",
            chunk_index=0,
            text="Les bases de l'algorithme.",
            score=0.9,
        ),
        RagHit(
            formation_id="other",
            chapter_id="ch-x",
            video_id="vid-x",
            title="Autre",
            source="transcription",
            chunk_index=0,
            text="Hors scope",
            score=0.99,
        ),
    ]
    use_case = AskFormation(
        formations,
        FakeEmbeddings(),
        FakeVectors(hits=hits, count=2),
        FakeChat(),
        top_k=6,
    )
    result = await use_case.execute(
        AskFormationCommand(formation_id=fid, question="Qu'est-ce que l'algo ?")
    )
    assert "Réponse" in result.answer
    assert len(result.citations) == 1
    assert result.citations[0].video_id == "vid-1"
    assert result.citations[0].title == "Intro"


async def test_ask_formation_empty_index_raises() -> None:
    formations = FakeFormationRepository()
    formation = Formation.create(name=FormationName("Vide"))
    await formations.save(formation)
    use_case = AskFormation(
        formations,
        FakeEmbeddings(),
        FakeVectors(count=0),
        FakeChat(),
        top_k=6,
    )
    with pytest.raises(RagEmptyIndexError, match="Aucun contenu indexé"):
        await use_case.execute(
            AskFormationCommand(formation_id=str(formation.id), question="Hello ?")
        )
