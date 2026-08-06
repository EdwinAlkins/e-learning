"""Use case : lister les documents d'un chapitre."""

from __future__ import annotations

from e_learning.application.catalog.dto import DocumentDTO
from e_learning.domain.catalog.repository import ChapterRepository, DocumentRepository
from e_learning.domain.catalog.value_objects import ChapterId


class ListChapterDocuments:
    def __init__(self, chapters: ChapterRepository, documents: DocumentRepository) -> None:
        self._chapters = chapters
        self._documents = documents

    async def execute(self, chapter_id: str) -> list[DocumentDTO]:
        chapter = await self._chapters.get(ChapterId.from_string(chapter_id))
        return [
            DocumentDTO.from_entity(d) for d in await self._documents.list_by_chapter(chapter.id)
        ]
