"""Use case : convertir / ré-encoder des médias en MP4 / MP3 web-compatible."""

from __future__ import annotations

from pathlib import Path

from e_learning.application.content.dto import ConvertVideosCommand
from e_learning.application.shared.media import MediaConvertPort

_VIDEO_EXTS = frozenset({".mp4", ".webm", ".mkv", ".avi", ".mov", ".m4v", ".wmv", ".flv"})
_AUDIO_EXTS = frozenset({".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".wma", ".opus"})


class ConvertVideos:
    def __init__(self, converter: MediaConvertPort, *, videos_root: Path) -> None:
        self._converter = converter
        self._videos_root = videos_root

    async def execute(self, command: ConvertVideosCommand) -> list[str]:
        converted: list[str] = []
        for source in sorted(self._videos_root.glob(command.source_glob)):
            if not source.is_file():
                continue
            suffix = source.suffix.lower()
            if suffix in _AUDIO_EXTS:
                destination = source.with_suffix(".mp3")
                is_native = suffix == ".mp3"
                if is_native and not command.overwrite:
                    continue
                if not is_native and destination.exists() and not command.overwrite:
                    continue
                self._converter.convert_to_mp3(source, destination)
                converted.append(str(destination.relative_to(self._videos_root)))
                continue

            if suffix not in _VIDEO_EXTS:
                continue

            destination = source.with_suffix(".mp4")
            is_mp4_source = suffix == ".mp4"
            if is_mp4_source and not command.overwrite:
                continue
            if not is_mp4_source and destination.exists() and not command.overwrite:
                continue

            self._converter.convert_to_mp4(source, destination)
            converted.append(str(destination.relative_to(self._videos_root)))
        return converted
