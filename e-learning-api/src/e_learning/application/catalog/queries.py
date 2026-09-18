"""Ports de lecture du catalogue.

Ces ports construisent des projections de lecture et ne doivent jamais être
utilisés pour écrire. Ils court-circuitent volontairement les agrégats.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from e_learning.application.catalog.dto import DocumentDTO, FormationDTO


@dataclass(frozen=True, slots=True)
class CatalogVideoRow:
    """Projection plate utilisée par le CLI ``list-videos``."""

    formation_id: str
    formation_name: str
    formation_slug: str
    chapter_id: str
    chapter_name: str
    video_id: str
    video_title: str
    relative_path: str


class CatalogQueryPort(ABC):
    """Chemin de lecture du catalogue, strictement read-only."""

    @abstractmethod
    async def list_formations(self) -> list[FormationDTO]: ...

    @abstractmethod
    async def get_formation(self, formation_id: str) -> FormationDTO: ...

    @abstractmethod
    async def list_chapter_documents(self, chapter_id: str) -> list[DocumentDTO]: ...

    @abstractmethod
    async def list_videos(
        self, *, formation_filter: str | None = None
    ) -> list[CatalogVideoRow]: ...
