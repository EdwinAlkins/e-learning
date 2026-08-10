"""Port d'extraction de texte depuis un document catalogue."""

from __future__ import annotations

from abc import ABC, abstractmethod


class DocumentTextExtractor(ABC):
    """Extrait du texte indexable ; ``None`` si format non supporté / vide."""

    @abstractmethod
    def extract(
        self,
        data: bytes,
        *,
        filename: str,
        mime_type: str | None = None,
    ) -> str | None: ...
