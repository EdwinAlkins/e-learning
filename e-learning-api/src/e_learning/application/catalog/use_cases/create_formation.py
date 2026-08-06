"""Use case : créer une formation.

Ordre FS puis DB : si la persistance échoue, compensation best-effort
(suppression du répertoire orphelin).
"""

from __future__ import annotations

from e_learning.application.catalog.dto import CreateFormationCommand, FormationDTO
from e_learning.application.shared.storage import CatalogStoragePort
from e_learning.domain.catalog.entities import Formation
from e_learning.domain.catalog.exceptions import FormationNameAlreadyUsed, FormationSlugAlreadyUsed
from e_learning.domain.catalog.repository import FormationRepository
from e_learning.domain.catalog.value_objects import FormationName, Slug


class CreateFormation:
    def __init__(self, formations: FormationRepository, storage: CatalogStoragePort) -> None:
        self._formations = formations
        self._storage = storage

    async def execute(self, command: CreateFormationCommand) -> FormationDTO:
        name = FormationName(command.name)
        if await self._formations.find_by_name(str(name)) is not None:
            raise FormationNameAlreadyUsed(str(name))
        slug = Slug.from_name(str(name))
        if await self._formations.find_by_slug(str(slug)) is not None:
            raise FormationSlugAlreadyUsed(str(slug))
        formation = Formation.create(name=name, slug=slug)
        self._storage.ensure_formation_dir(str(slug))
        try:
            await self._formations.save(formation)
        except Exception:
            self._storage.delete_formation_dir(str(slug))
            raise
        return FormationDTO.from_parts(formation, [])
