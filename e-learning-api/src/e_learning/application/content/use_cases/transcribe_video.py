"""Use case : transcrire une vidéo."""

from __future__ import annotations

from e_learning.application.content.dto import TranscribeCommand
from e_learning.application.jobs.progress import NullProgressReporter, ProgressReporter
from e_learning.application.shared.media import MediaFilePort, TranscriptionPort
from e_learning.application.shared.storage import CatalogStoragePort
from e_learning.domain.catalog.repository import VideoRepository
from e_learning.domain.catalog.value_objects import VideoId


class TranscribeVideo:
    def __init__(
        self,
        videos: VideoRepository,
        storage: CatalogStoragePort,
        media_files: MediaFilePort,
        transcription: TranscriptionPort,
    ) -> None:
        self._videos = videos
        self._storage = storage
        self._media_files = media_files
        self._transcription = transcription

    async def execute(
        self,
        command: TranscribeCommand,
        *,
        progress: ProgressReporter | None = None,
    ) -> str:
        reporter = progress or NullProgressReporter()
        video = await self._videos.get(VideoId.from_string(command.video_id))
        video_path = self._storage.absolute_path(str(video.relative_path))
        await reporter.set(10, "Chargement du modèle…")
        await reporter.set(40, "Transcription en cours…")
        text = await self._transcription.transcribe(
            video_path,
            model=command.model,
            language=command.language,
            with_timecodes=command.with_timecodes,
        )
        await reporter.set(90, "Écriture de la transcription…")
        out = self._media_files.transcription_path(str(video.relative_path))
        self._media_files.write_text(out, text)
        await reporter.set(100, "Transcription terminée")
        return text
