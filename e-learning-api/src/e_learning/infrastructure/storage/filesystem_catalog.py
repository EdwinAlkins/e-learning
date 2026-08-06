"""Adaptateur FS pour le catalogue vidéo."""

from __future__ import annotations

import mimetypes
import shutil
import subprocess
from pathlib import Path, PurePosixPath

from e_learning.application.catalog.name_match import strip_order_prefix
from e_learning.application.shared.errors import StorageError
from e_learning.application.shared.storage import (
    CatalogStoragePort,
    ScannedChapter,
    ScannedDocument,
    ScannedFormation,
    ScannedVideo,
)

_VIDEO_EXTS = frozenset({".mp4", ".webm", ".mkv", ".avi", ".mov", ".m4v", ".wmv", ".flv"})
_AUDIO_EXTS = frozenset({".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".wma", ".opus"})
_MEDIA_EXTS = _VIDEO_EXTS | _AUDIO_EXTS
_DOC_EXTS = frozenset({".pdf", ".md", ".txt", ".doc", ".docx", ".ppt", ".pptx", ".png", ".jpg", ".jpeg"})
_STAGING_MARKER = ".src"


def probe_duration(path: Path) -> float:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            return max(0.0, float(result.stdout.strip()))
    except FileNotFoundError, ValueError:
        pass
    return 0.0


class FilesystemCatalogStorage(CatalogStoragePort):
    def __init__(self, root: Path) -> None:
        self._root = root.resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def absolute_path(self, relative_path: str) -> Path:
        candidate = (self._root / relative_path).resolve()
        if not candidate.is_relative_to(self._root):
            raise StorageError(f"Chemin hors racine vidéos : {relative_path}")
        return candidate

    def scan(self) -> list[ScannedFormation]:
        formations: list[ScannedFormation] = []
        if not self._root.is_dir():
            return formations
        for formation_dir in sorted(p for p in self._root.iterdir() if p.is_dir()):
            chapters: list[ScannedChapter] = []
            for chapter_dir in sorted(p for p in formation_dir.iterdir() if p.is_dir()):
                videos: list[ScannedVideo] = []
                documents: list[ScannedDocument] = []
                for file_path in sorted(p for p in chapter_dir.iterdir() if p.is_file()):
                    # Ignore fichiers source en cours de conversion ({stem}.src.ext)
                    if _STAGING_MARKER in file_path.name:
                        continue
                    rel = str(PurePosixPath(formation_dir.name) / chapter_dir.name / file_path.name)
                    suffix = file_path.suffix.lower()
                    if suffix in _MEDIA_EXTS:
                        stem = strip_order_prefix(file_path.stem)
                        kind = "audio" if suffix in _AUDIO_EXTS else "video"
                        videos.append(
                            ScannedVideo(
                                filename=file_path.name,
                                relative_path=rel,
                                title=stem,
                                duration_seconds=probe_duration(file_path),
                                kind=kind,
                            )
                        )
                    elif suffix in _DOC_EXTS or suffix not in {".md", ".txt"}:
                        # sidecars .md/.txt next to media are content, not documents
                        if suffix in {".md", ".txt"} and (
                            (chapter_dir / f"{file_path.stem}.mp4").exists()
                            or (chapter_dir / f"{file_path.stem}.mp3").exists()
                        ):
                            continue
                        mime, _ = mimetypes.guess_type(file_path.name)
                        documents.append(
                            ScannedDocument(
                                filename=file_path.name,
                                relative_path=rel,
                                title=strip_order_prefix(file_path.stem),
                                mime_type=mime,
                            )
                        )
                chapters.append(
                    ScannedChapter(
                        slug=chapter_dir.name,
                        videos=videos,
                        documents=documents,
                    )
                )
            formations.append(ScannedFormation(slug=formation_dir.name, chapters=chapters))
        return formations

    def ensure_formation_dir(self, slug: str) -> None:
        (self._root / slug).mkdir(parents=True, exist_ok=True)

    def ensure_chapter_dir(self, formation_slug: str, chapter_slug: str) -> None:
        (self._root / formation_slug / chapter_slug).mkdir(parents=True, exist_ok=True)

    def rename_formation_dir(self, old_slug: str, new_slug: str) -> None:
        old = self._root / old_slug
        new = self._root / new_slug
        if old.exists():
            old.rename(new)

    def rename_chapter_dir(self, formation_slug: str, old_slug: str, new_slug: str) -> None:
        old = self._root / formation_slug / old_slug
        new = self._root / formation_slug / new_slug
        if old.exists():
            old.rename(new)

    def delete_formation_dir(self, slug: str) -> None:
        path = self._root / slug
        if path.exists():
            shutil.rmtree(path)

    def delete_chapter_dir(self, formation_slug: str, chapter_slug: str) -> None:
        path = self._root / formation_slug / chapter_slug
        if path.exists():
            shutil.rmtree(path)

    def delete_file(self, relative_path: str) -> None:
        path = self.absolute_path(relative_path)
        if path.exists():
            path.unlink()
        for sidecar in (path.with_suffix(".md"), path.with_suffix(".txt")):
            if sidecar.exists():
                sidecar.unlink()
        # Staging source restants : {stem}.src.* lors de la suppression du média final.
        if _STAGING_MARKER not in path.name and path.parent.is_dir():
            for sibling in path.parent.glob(f"{path.stem}{_STAGING_MARKER}.*"):
                if sibling.is_file():
                    sibling.unlink()

    def write_video(self, relative_path: str, data: bytes) -> float:
        path = self.absolute_path(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return probe_duration(path)

    def write_document(self, relative_path: str, data: bytes) -> None:
        path = self.absolute_path(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def move_file(self, old_relative_path: str, new_relative_path: str) -> None:
        old = self.absolute_path(old_relative_path)
        new = self.absolute_path(new_relative_path)
        new.parent.mkdir(parents=True, exist_ok=True)
        if old.exists():
            old.rename(new)
        for suffix in (".md", ".txt"):
            old_side = old.with_suffix(suffix)
            if old_side.exists():
                old_side.rename(new.with_suffix(suffix))

    def file_exists(self, relative_path: str) -> bool:
        return self.absolute_path(relative_path).is_file()

    def probe_duration(self, relative_path: str) -> float:
        return probe_duration(self.absolute_path(relative_path))
