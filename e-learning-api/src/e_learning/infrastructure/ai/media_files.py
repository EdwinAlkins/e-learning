"""Adaptateur fichiers sidecars (résumé / transcription)."""

from __future__ import annotations

from pathlib import Path

from e_learning.application.shared.media import MediaFilePort


class FilesystemMediaFiles(MediaFilePort):
    def __init__(self, root: Path) -> None:
        self._root = root.resolve()

    def _abs(self, relative: str) -> Path:
        return (self._root / relative).resolve()

    def summary_path(self, video_relative_path: str) -> Path:
        return self._abs(video_relative_path).with_suffix(".md")

    def transcription_path(self, video_relative_path: str) -> Path:
        return self._abs(video_relative_path).with_suffix(".txt")

    def read_text(self, path: Path) -> str | None:
        if not path.is_file():
            return None
        return path.read_text(encoding="utf-8")

    def write_text(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
