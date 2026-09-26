"""Ports de lecture du contexte ``usage``."""

from __future__ import annotations

from abc import ABC, abstractmethod

from e_learning.application.usage.dto import UserTokenUsageDTO


class UsageQueryPort(ABC):
    @abstractmethod
    async def get_user_usage(self, *, user_id: str, days: int) -> UserTokenUsageDTO:
        """Agrégats sur les ``days`` derniers jours (jour courant inclus) + cumul global.

        ``daily`` contient une entrée par jour de la fenêtre, y compris à zéro.
        """
