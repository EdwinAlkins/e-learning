"""Use case : créer un chapitre.

Ordre FS puis DB : si la persistance échoue, compensation best-effort
(suppression du répertoire orphelin).
"""

from __future__ import annotations

from e_learning.application.catalog.dto import ChapterDTO, CreateChapterCommand
from e_learning.application.shared.storage import CatalogStoragePort
from e_learning.domain.catalog.entities import Chapter
from e_learning.domain.catalog.repository import ChapterRepository, FormationRepository
from e_learning.domain.catalog.value_objects import ChapterName, FormationId, Position, Slug


class CreateChapter:
    def __init__(
        self,
        formations: FormationRepository,
        chapters: ChapterRepository,
        storage: CatalogStoragePort,
    ) -> None:
        self._formations = formations
        self._chapters = chapters
        self._storage = storage

    async def execute(self, command: CreateChapterCommand) -> ChapterDTO:
        formation = await self._formations.get(FormationId.from_string(command.formation_id))
        name = ChapterName(command.name)
        position = Position(await self._chapters.next_position(formation.id))
        slug = Slug.from_name(f"{position.value}-{name}")
        chapter = Chapter.create(formation_id=formation.id, name=name, position=position, slug=slug)
        self._storage.ensure_chapter_dir(str(formation.slug), str(chapter.slug))
        try:
            await self._chapters.save(chapter)
        except Exception:
            self._storage.delete_chapter_dir(str(formation.slug), str(chapter.slug))
            raise
        return ChapterDTO(
            id=str(chapter.id),
            name=str(chapter.name),
            slug=str(chapter.slug),
            position=chapter.position.value,
            videos=[],
            documents=[],
        )
