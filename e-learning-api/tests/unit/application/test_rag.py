"""Tests — chunker + AskFormation RAG + documents."""

from __future__ import annotations

from pathlib import Path

import pytest

from e_learning.application.content.chunker import chunk_point_id, chunk_text
from e_learning.application.content.dto import (
    AskFormationCommand,
    IndexDocumentCommand,
    IndexFormationCommand,
)
from e_learning.application.content.use_cases.ask_formation import AskFormation
from e_learning.application.content.use_cases.index_document_content import IndexDocumentContent
from e_learning.application.content.use_cases.index_formation import IndexFormation
from e_learning.application.content.use_cases.index_video_content import IndexVideoContent
from e_learning.application.shared.document_text import DocumentTextExtractor
from e_learning.application.shared.errors import RagEmptyIndexError
from e_learning.application.shared.media import MediaFilePort
from e_learning.application.shared.rag import (
    ChatPort,
    EmbeddingPort,
    RagChunk,
    RagHit,
    VectorStorePort,
)
from e_learning.domain.catalog.entities import Chapter, Document, Formation, Video
from e_learning.domain.catalog.value_objects import (
    ChapterName,
    DocumentTitle,
    DurationSeconds,
    FormationName,
    Position,
    RelativePath,
    VideoTitle,
)
from e_learning.infrastructure.ai.document_text import FilesystemDocumentTextExtractor
from tests.unit.application._fakes import (
    FakeChapterRepository,
    FakeDocumentRepository,
    FakeFormationRepository,
    FakeVideoRepository,
)
from tests.unit.application.test_use_cases import FakeCatalogStorage


def test_chunk_text_respects_size_and_overlap() -> None:
    text = "a" * 50
    chunks = chunk_text(text, chunk_size=20, overlap=5)
    assert len(chunks) >= 3
    assert all(len(c) <= 20 for c in chunks)
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


def test_chunk_point_id_document_differs_from_video() -> None:
    video = chunk_point_id("same-id", "document", 0, kind="video")
    document = chunk_point_id("same-id", "document", 0, kind="document")
    assert video != document


class FakeEmbeddings(EmbeddingPort):
    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[float(len(t))] + [0.0] * 2 for t in texts]


class FakeVectors(VectorStorePort):
    def __init__(self, hits: list[RagHit] | None = None, count: int = 0) -> None:
        self._hits = hits or []
        self._count = count
        self.upserted: list[RagChunk] = []
        self.deleted_videos: list[str] = []
        self.deleted_documents: list[str] = []

    async def ensure_collection(self) -> None:
        return None

    async def upsert_chunks(self, chunks: list[RagChunk]) -> None:
        self.upserted.extend(chunks)

    async def delete_by_video(self, video_id: str) -> None:
        self.deleted_videos.append(video_id)

    async def delete_by_document(self, document_id: str) -> None:
        self.deleted_documents.append(document_id)

    async def search(self, formation_id: str, vector: list[float], *, top_k: int) -> list[RagHit]:
        return [h for h in self._hits if h.formation_id == formation_id][:top_k]

    async def count_by_formation(self, formation_id: str) -> int:
        return self._count


class FakeChat(ChatPort):
    async def answer(self, *, question: str, context: str) -> str:
        return f"Réponse à « {question} » avec {len(context)} chars de contexte"


class FakeMediaFiles(MediaFilePort):
    def __init__(self, root: Path) -> None:
        self.root = root

    def summary_path(self, video_relative_path: str) -> Path:
        return self.root / Path(video_relative_path).with_suffix(".md")

    def transcription_path(self, video_relative_path: str) -> Path:
        return self.root / Path(video_relative_path).with_suffix(".txt")

    def read_text(self, path: Path) -> str | None:
        if not path.is_file():
            return None
        return path.read_text(encoding="utf-8")

    def write_text(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


class PassthroughExtractor(DocumentTextExtractor):
    def extract(
        self,
        data: bytes,
        *,
        filename: str,
        mime_type: str | None = None,
    ) -> str | None:
        if not data:
            return None
        try:
            text = data.decode("utf-8").strip()
        except UnicodeDecodeError:
            return None
        return text or None


def test_document_text_extractor_md_and_skip_image() -> None:
    extractor = FilesystemDocumentTextExtractor()
    assert extractor.extract(b"# Titre\n\nContenu", filename="notes.md") == "# Titre Contenu"
    assert extractor.extract(b"\x89PNG", filename="slide.png") is None


async def test_ask_formation_returns_citations_filtered() -> None:
    formations = FakeFormationRepository()
    formation = Formation.create(name=FormationName("Algo"))
    await formations.save(formation)
    fid = str(formation.id)

    hits = [
        RagHit(
            formation_id=fid,
            chapter_id="ch-1",
            title="Intro",
            source="transcription",
            chunk_index=0,
            text="Les bases de l'algorithme.",
            score=0.9,
            video_id="vid-1",
        ),
        RagHit(
            formation_id="other",
            chapter_id="ch-x",
            title="Autre",
            source="transcription",
            chunk_index=0,
            text="Hors scope",
            score=0.99,
            video_id="vid-x",
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


async def test_ask_formation_mixed_video_and_document_citations() -> None:
    formations = FakeFormationRepository()
    formation = Formation.create(name=FormationName("Mixte"))
    await formations.save(formation)
    fid = str(formation.id)
    hits = [
        RagHit(
            formation_id=fid,
            chapter_id="ch-1",
            title="Vidéo A",
            source="summary",
            chunk_index=0,
            text="Résumé vidéo",
            score=0.95,
            video_id="vid-1",
        ),
        RagHit(
            formation_id=fid,
            chapter_id="ch-1",
            title="Support PDF",
            source="document",
            chunk_index=0,
            text="Contenu du document annexé.",
            score=0.9,
            document_id="doc-1",
        ),
    ]
    result = await AskFormation(
        formations,
        FakeEmbeddings(),
        FakeVectors(hits=hits, count=2),
        FakeChat(),
        top_k=6,
    ).execute(AskFormationCommand(formation_id=fid, question="Explique"))
    assert len(result.citations) == 2
    sources = {(c.video_id, c.document_id, c.source) for c in result.citations}
    assert ("vid-1", None, "summary") in sources
    assert ((None, "doc-1", "document") in sources)


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


async def test_index_document_content_upserts_and_deletes(tmp_path: Path) -> None:
    formations = FakeFormationRepository()
    chapters = FakeChapterRepository()
    documents = FakeDocumentRepository()
    storage = FakeCatalogStorage(tmp_path)
    vectors = FakeVectors()

    formation = Formation.create(name=FormationName("F"))
    await formations.save(formation)
    chapter = Chapter.create(
        formation_id=formation.id,
        name=ChapterName("C1"),
        position=Position(0),
    )
    await chapters.save(chapter)
    relative = "f/c/notes.md"
    storage.write_document(relative, b"Contenu pedagogique important.")
    document = Document.create(
        chapter_id=chapter.id,
        title=DocumentTitle("Notes"),
        filename="notes.md",
        relative_path=RelativePath(relative),
        position=Position(0),
        mime_type="text/markdown",
    )
    await documents.save(document)

    n = await IndexDocumentContent(
        documents,
        chapters,
        formations,
        storage,
        PassthroughExtractor(),
        FakeEmbeddings(),
        vectors,
        chunk_size=800,
        chunk_overlap=120,
    ).execute(IndexDocumentCommand(document_id=str(document.id)))

    assert n == 1
    assert vectors.deleted_documents == [str(document.id)]
    assert len(vectors.upserted) == 1
    chunk = vectors.upserted[0]
    assert chunk.document_id == str(document.id)
    assert chunk.source == "document"
    assert chunk.video_id is None
    assert "Contenu" in chunk.text


async def test_index_formation_includes_documents(tmp_path: Path) -> None:
    formations = FakeFormationRepository()
    chapters = FakeChapterRepository()
    documents = FakeDocumentRepository()
    videos = FakeVideoRepository()
    storage = FakeCatalogStorage(tmp_path)
    media = FakeMediaFiles(tmp_path)
    vectors = FakeVectors()

    formation = Formation.create(name=FormationName("F"))
    await formations.save(formation)
    chapter = Chapter.create(
        formation_id=formation.id,
        name=ChapterName("C1"),
        position=Position(0),
    )
    await chapters.save(chapter)

    video_rel = "f/c/intro.mp4"
    media.write_text(media.transcription_path(video_rel), "Transcription vidéo longue assez.")
    video = Video.create(
        chapter_id=chapter.id,
        title=VideoTitle("Intro"),
        filename="intro.mp4",
        relative_path=RelativePath(video_rel),
        position=Position(0),
        duration=DurationSeconds(10),
        transcription_status=Video.AI_READY,
    )
    await videos.save(video)

    doc_rel = "f/c/annexe.txt"
    storage.write_document(doc_rel, b"Document annexe utile.")
    document = Document.create(
        chapter_id=chapter.id,
        title=DocumentTitle("Annexe"),
        filename="annexe.txt",
        relative_path=RelativePath(doc_rel),
        position=Position(0),
    )
    await documents.save(document)

    index_video = IndexVideoContent(
        videos,
        chapters,
        formations,
        media,
        FakeEmbeddings(),
        vectors,
        chunk_size=800,
        chunk_overlap=120,
    )
    index_document = IndexDocumentContent(
        documents,
        chapters,
        formations,
        storage,
        PassthroughExtractor(),
        FakeEmbeddings(),
        vectors,
        chunk_size=800,
        chunk_overlap=120,
    )
    result = await IndexFormation(
        formations, videos, chapters, documents, index_video, index_document
    ).execute(IndexFormationCommand(formation_id=str(formation.id)))

    assert result.indexed_videos == 1
    assert result.indexed_documents == 1
    assert result.indexed_chunks >= 2
    assert any(c.document_id == str(document.id) for c in vectors.upserted)
    assert any(c.video_id == str(video.id) for c in vectors.upserted)
