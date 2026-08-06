"""Use case : supprimer un chapitre."""

from __future__ import annotations

import logging

from e_learning.application.shared.storage import CatalogStoragePort
from e_learning.domain.catalog.repository import ChapterRepository, FormationRepository
from e_learning.domain.catalog.value_objects import ChapterId

logger = logging.getLogger("e_learning")


class DeleteChapter:
    def __init__(
        self,
        formations: FormationRepository,
        chapters: ChapterRepository,
        storage: CatalogStoragePort,
    ) -> None:
        self._formations = formations
        self._chapters = chapters
        self._storage = storage

    async def execute(self, chapter_id: str) -> None:
        chapter = await self._chapters.get(ChapterId.from_string(chapter_id))
        formation = await self._formations.get(chapter.formation_id)
        formation_slug = str(formation.slug)
        chapter_slug = str(chapter.slug)
        # DB d'abord (CASCADE vidéos/docs) ; FS best-effort ensuite.
        await self._chapters.delete(chapter.id)
        try:
            self._storage.delete_chapter_dir(formation_slug, chapter_slug)
        except Exception:
            logger.exception(
                "Suppression FS échouée après delete DB (chapitre %s, %s/%s)",
                chapter_id,
                formation_slug,
                chapter_slug,
            )
