"""Use case : réordonner les chapitres d'une formation (positions DB)."""

from __future__ import annotations

from e_learning.application.catalog.dto import FormationDTO, ReorderChaptersCommand
from e_learning.application.catalog.use_cases.get_formation import GetFormation
from e_learning.domain.catalog.exceptions import ReorderInvalid
from e_learning.domain.catalog.repository import (
    ChapterRepository,
    DocumentRepository,
    FormationRepository,
    JobRepository,
    VideoRepository,
)
from e_learning.domain.catalog.value_objects import FormationId, Position


class ReorderChapters:
    def __init__(
        self,
        formations: FormationRepository,
        chapters: ChapterRepository,
        videos: VideoRepository,
        documents: DocumentRepository,
        jobs: JobRepository,
    ) -> None:
        self._formations = formations
        self._chapters = chapters
        self._get_formation = GetFormation(formations, chapters, videos, documents, jobs)

    async def execute(self, command: ReorderChaptersCommand) -> FormationDTO:
        formation = await self._formations.get(FormationId.from_string(command.formation_id))
        current = await self._chapters.list_by_formation(formation.id)
        current_ids = {str(c.id) for c in current}
        if len(command.chapter_ids) != len(current_ids):
            raise ReorderInvalid(
                "La liste doit contenir exactement tous les chapitres de la formation."
            )
        if len(set(command.chapter_ids)) != len(command.chapter_ids):
            raise ReorderInvalid("La liste contient des doublons.")
        if set(command.chapter_ids) != current_ids:
            raise ReorderInvalid("La liste contient des identifiants inconnus ou hors formation.")

        by_id = {str(c.id): c for c in current}
        ordered = []
        for index, chapter_id in enumerate(command.chapter_ids):
            chapter = by_id[chapter_id]
            chapter.move_to(Position(index))
            ordered.append(chapter)
        await self._chapters.save_ordered(ordered)
        return await self._get_formation.execute(command.formation_id)
