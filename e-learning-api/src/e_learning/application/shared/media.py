"""Ports techniques pour le contenu IA / médias."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from pathlib import Path


class MediaFilePort(ABC):
    """Lecture/écriture des sidecars (``.md``, ``.txt``) à côté d'une vidéo."""

    @abstractmethod
    def summary_path(self, video_relative_path: str) -> Path: ...

    @abstractmethod
    def transcription_path(self, video_relative_path: str) -> Path: ...

    @abstractmethod
    def read_text(self, path: Path) -> str | None: ...

    @abstractmethod
    def write_text(self, path: Path, content: str) -> None: ...


class TranscriptionPort(ABC):
    @abstractmethod
    async def transcribe(
        self,
        video_path: Path,
        *,
        model: str = "base",
        language: str | None = None,
        with_timecodes: bool = False,
    ) -> str: ...


class SummaryPort(ABC):
    @abstractmethod
    async def generate(self, transcription: str) -> str: ...


class MediaConvertPort(ABC):
    @abstractmethod
    def needs_video_transcode(self, path: Path) -> bool: ...

    @abstractmethod
    def needs_audio_transcode(self, path: Path) -> bool: ...

    @abstractmethod
    def convert_to_mp4(
        self,
        source: Path,
        destination: Path,
        *,
        on_progress: Callable[[int], None] | None = None,
    ) -> None: ...

    @abstractmethod
    def convert_to_mp3(
        self,
        source: Path,
        destination: Path,
        *,
        on_progress: Callable[[int], None] | None = None,
    ) -> None: ...
