"""Use case : supprimer un document annexe."""

from __future__ import annotations

import logging

from e_learning.application.shared.errors import RagError
from e_learning.application.shared.rag import VectorStorePort
from e_learning.application.shared.storage import CatalogStoragePort
from e_learning.domain.catalog.repository import DocumentRepository
from e_learning.domain.catalog.value_objects import DocumentId

logger = logging.getLogger("e_learning")


class DeleteDocument:
    def __init__(
        self,
        documents: DocumentRepository,
        storage: CatalogStoragePort,
        vectors: VectorStorePort | None = None,
    ) -> None:
        self._documents = documents
        self._storage = storage
        self._vectors = vectors

    async def execute(self, document_id: str) -> None:
        document = await self._documents.get(DocumentId.from_string(document_id))
        relative_path = str(document.relative_path)
        await self._documents.delete(document.id)
        try:
            self._storage.delete_file(relative_path)
        except Exception:
            logger.exception(
                "Suppression FS échouée après delete DB (document %s, path=%s)",
                document_id,
                relative_path,
            )
        if self._vectors is not None:
            try:
                await self._vectors.delete_by_document(document_id)
            except RagError:
                logger.exception(
                    "Purge RAG échouée après delete document %s (best-effort)",
                    document_id,
                )
