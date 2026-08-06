"""Use case : supprimer une formation."""

from __future__ import annotations

from e_learning.application.shared.storage import CatalogStoragePort
from e_learning.domain.catalog.repository import FormationRepository
from e_learning.domain.catalog.value_objects import FormationId


class DeleteFormation:
    def __init__(self, formations: FormationRepository, storage: CatalogStoragePort) -> None:
        self._formations = formations
        self._storage = storage

    async def execute(self, formation_id: str) -> None:
        formation = await self._formations.get(FormationId.from_string(formation_id))
        self._storage.delete_formation_dir(str(formation.slug))
        await self._formations.delete(formation.id)
