"""Use case : indexer le texte extractible d'un document catalogue dans Qdrant."""

from __future__ import annotations

import logging

from e_learning.application.content.chunker import chunk_point_id, chunk_text
from e_learning.application.content.dto import IndexDocumentCommand
from e_learning.application.jobs.progress import NullProgressReporter, ProgressReporter
from e_learning.application.shared.document_text import DocumentTextExtractor
from e_learning.application.shared.rag import EmbeddingPort, RagChunk, VectorStorePort
from e_learning.application.shared.storage import CatalogStoragePort
from e_learning.domain.catalog.repository import (
    ChapterRepository,
    DocumentRepository,
    FormationRepository,
)
from e_learning.domain.catalog.value_objects import DocumentId

logger = logging.getLogger("e_learning")


class IndexDocumentContent:
    def __init__(
        self,
        documents: DocumentRepository,
        chapters: ChapterRepository,
        formations: FormationRepository,
        storage: CatalogStoragePort,
        extractor: DocumentTextExtractor,
        embeddings: EmbeddingPort,
        vectors: VectorStorePort,
        *,
        chunk_size: int,
        chunk_overlap: int,
    ) -> None:
        self._documents = documents
        self._chapters = chapters
        self._formations = formations
        self._storage = storage
        self._extractor = extractor
        self._embeddings = embeddings
        self._vectors = vectors
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    async def execute(
        self,
        command: IndexDocumentCommand,
        *,
        progress: ProgressReporter | None = None,
    ) -> int:
        reporter = progress or NullProgressReporter()
        document = await self._documents.get(DocumentId.from_string(command.document_id))
        chapter = await self._chapters.get(document.chapter_id)
        await self._formations.get(chapter.formation_id)

        await reporter.set(5, "Extraction du document…")
        path = self._storage.absolute_path(str(document.relative_path))
        if not path.is_file():
            await self._vectors.delete_by_document(str(document.id))
            await reporter.set(100, "Fichier document introuvable")
            logger.warning(
                "Document %s : fichier manquant (%s) — purge index",
                document.id,
                document.relative_path,
            )
            return 0

        text = self._extractor.extract(
            path.read_bytes(),
            filename=document.filename,
            mime_type=document.mime_type,
        )
        await self._vectors.delete_by_document(str(document.id))
        if not text:
            await reporter.set(100, "Rien à indexer (format non extractible)")
            return 0

        pieces = chunk_text(text, chunk_size=self._chunk_size, overlap=self._chunk_overlap)
        if not pieces:
            await reporter.set(100, "Rien à indexer")
            return 0

        total = len(pieces)
        await reporter.set(20, f"Embeddings 0/{total}")
        vectors = await self._embeddings.embed(pieces)
        await reporter.set(60, f"Embeddings {total}/{total}")

        linked_video = str(document.video_id) if document.video_id is not None else None
        chunks: list[RagChunk] = [
            RagChunk(
                id=chunk_point_id(str(document.id), "document", idx, kind="document"),
                formation_id=str(chapter.formation_id),
                chapter_id=str(chapter.id),
                title=str(document.title),
                source="document",
                chunk_index=idx,
                text=piece,
                vector=vector,
                video_id=linked_video,
                document_id=str(document.id),
            )
            for idx, (piece, vector) in enumerate(zip(pieces, vectors, strict=True))
        ]
        await reporter.set(80, f"Indexation {total} chunk(s)…")
        await self._vectors.upsert_chunks(chunks)
        await reporter.set(100, f"{total} chunk(s) indexés")
        return len(chunks)
