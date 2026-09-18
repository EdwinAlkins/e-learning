"""Ports de lecture du contexte d'apprentissage."""

from __future__ import annotations

from abc import ABC, abstractmethod

from e_learning.application.learning.dto import FormationProgressDTO, NoteDTO, ProgressDTO


class LearningQueryPort(ABC):
    """Projections utilisateur en lecture seule, sans reconstruction d'agrégats."""

    @abstractmethod
    async def list_notes(self, *, user_id: str, video_id: str) -> list[NoteDTO]: ...

    @abstractmethod
    async def get_progress(self, *, user_id: str, video_id: str) -> ProgressDTO: ...

    @abstractmethod
    async def get_formation_progress(
        self, *, user_id: str, formation_id: str
    ) -> FormationProgressDTO: ...

    @abstractmethod
    async def list_formations_progress(
        self, *, user_id: str
    ) -> dict[str, FormationProgressDTO]: ...
