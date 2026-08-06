"""Use case : résoudre le chemin absolu d'un document."""

from __future__ import annotations

from pathlib import Path

from e_learning.application.shared.storage import CatalogStoragePort
from e_learning.domain.catalog.exceptions import DocumentNotFound
from e_learning.domain.catalog.repository import DocumentRepository
from e_learning.domain.catalog.value_objects import DocumentId


class GetDocumentPath:
    def __init__(self, documents: DocumentRepository, storage: CatalogStoragePort) -> None:
        self._documents = documents
        self._storage = storage

    async def execute(self, document_id: str) -> Path:
        document = await self._documents.get(DocumentId.from_string(document_id))
        path = self._storage.absolute_path(str(document.relative_path))
        if not path.is_file():
            raise DocumentNotFound(document_id)
        return path
