"""Port de progression pour les jobs de fond (pas d'infra SQLAlchemy ici)."""

from __future__ import annotations

from typing import Protocol


class ProgressReporter(Protocol):
    async def set(self, progress: int, message: str | None = None) -> None: ...


class NullProgressReporter:
    async def set(self, progress: int, message: str | None = None) -> None:
        return None
