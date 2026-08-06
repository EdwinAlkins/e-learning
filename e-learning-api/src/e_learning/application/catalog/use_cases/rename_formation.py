"""Use case : renommer une formation."""

from __future__ import annotations

from e_learning.application.catalog.dto import FormationDTO, RenameFormationCommand
from e_learning.application.catalog.use_cases.get_formation import GetFormation
from e_learning.application.shared.storage import CatalogStoragePort
from e_learning.domain.catalog.exceptions import FormationNameAlreadyUsed, FormationSlugAlreadyUsed
from e_learning.domain.catalog.repository import (
    ChapterRepository,
    DocumentRepository,
    FormationRepository,
    JobRepository,
    VideoRepository,
)
from e_learning.domain.catalog.value_objects import FormationId, FormationName, Slug


class RenameFormation:
    def __init__(
        self,
        formations: FormationRepository,
        chapters: ChapterRepository,
        videos: VideoRepository,
        documents: DocumentRepository,
        storage: CatalogStoragePort,
        jobs: JobRepository,
    ) -> None:
        self._formations = formations
        self._storage = storage
        self._get = GetFormation(formations, chapters, videos, documents, jobs)

    async def execute(self, command: RenameFormationCommand) -> FormationDTO:
        formation = await self._formations.get(FormationId.from_string(command.formation_id))
        name = FormationName(command.name)
        existing = await self._formations.find_by_name(str(name))
        if existing is not None and existing.id != formation.id:
            raise FormationNameAlreadyUsed(str(name))
        new_slug = Slug.from_name(str(name))
        slug_owner = await self._formations.find_by_slug(str(new_slug))
        if slug_owner is not None and slug_owner.id != formation.id:
            raise FormationSlugAlreadyUsed(str(new_slug))
        old_slug = str(formation.slug)
        if old_slug != str(new_slug):
            self._storage.rename_formation_dir(old_slug, str(new_slug))
        formation.rename(name, slug=new_slug)
        await self._formations.save(formation)
        return await self._get.execute(str(formation.id))
