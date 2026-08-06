"""Port de stockage catalogue (FS)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ScannedVideo:
    filename: str
    relative_path: str
    title: str
    duration_seconds: float
    kind: str = "video"


@dataclass(frozen=True, slots=True)
class ScannedDocument:
    filename: str
    relative_path: str
    title: str
    mime_type: str | None


@dataclass(frozen=True, slots=True)
class ScannedChapter:
    slug: str
    videos: list[ScannedVideo]
    documents: list[ScannedDocument]


@dataclass(frozen=True, slots=True)
class ScannedFormation:
    slug: str
    chapters: list[ScannedChapter]


class CatalogStoragePort(ABC):
    """Accès fichiers sous ``APP_VIDEOS_PATH``."""

    @abstractmethod
    def absolute_path(self, relative_path: str) -> Path: ...

    @abstractmethod
    def scan(self) -> list[ScannedFormation]: ...

    @abstractmethod
    def ensure_formation_dir(self, slug: str) -> None: ...

    @abstractmethod
    def ensure_chapter_dir(self, formation_slug: str, chapter_slug: str) -> None: ...

    @abstractmethod
    def rename_formation_dir(self, old_slug: str, new_slug: str) -> None: ...

    @abstractmethod
    def rename_chapter_dir(self, formation_slug: str, old_slug: str, new_slug: str) -> None: ...

    @abstractmethod
    def delete_formation_dir(self, slug: str) -> None: ...

    @abstractmethod
    def delete_chapter_dir(self, formation_slug: str, chapter_slug: str) -> None: ...

    @abstractmethod
    def delete_file(self, relative_path: str) -> None: ...

    @abstractmethod
    def write_video(self, relative_path: str, data: bytes) -> float:
        """Écrit la vidéo et retourne la durée en secondes."""

    @abstractmethod
    def write_document(self, relative_path: str, data: bytes) -> None:
        """Écrit un document annexe (sans probe durée)."""

    @abstractmethod
    def move_file(self, old_relative_path: str, new_relative_path: str) -> None: ...

    @abstractmethod
    def file_exists(self, relative_path: str) -> bool: ...

    @abstractmethod
    def probe_duration(self, relative_path: str) -> float:
        """Durée en secondes du fichier (0 si inconnue)."""
