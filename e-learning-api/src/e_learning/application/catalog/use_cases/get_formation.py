"""Use case : récupérer une formation complète."""

from __future__ import annotations

from e_learning.application.catalog.dto import FormationDTO
from e_learning.application.catalog.use_cases.list_formations import ListFormations
from e_learning.domain.catalog.repository import (
    ChapterRepository,
    DocumentRepository,
    FormationRepository,
    JobRepository,
    VideoRepository,
)
from e_learning.domain.catalog.value_objects import FormationId


class GetFormation:
    def __init__(
        self,
        formations: FormationRepository,
        chapters: ChapterRepository,
        videos: VideoRepository,
        documents: DocumentRepository,
        jobs: JobRepository,
    ) -> None:
        self._list = ListFormations(formations, chapters, videos, documents, jobs)
        self._formations = formations

    async def execute(self, formation_id: str) -> FormationDTO:
        formation = await self._formations.get(FormationId.from_string(formation_id))
        return await self._list._build(formation)
