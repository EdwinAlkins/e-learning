"""Use case : démarrer une génération de résumé asynchrone."""

from __future__ import annotations

from e_learning.application.catalog.dto import VideoDTO
from e_learning.application.jobs.create_job import create_queued_job
from e_learning.application.jobs.enqueue import publish_compute_job
from e_learning.application.shared.media import MediaFilePort
from e_learning.application.shared.messaging import JobPublisherPort
from e_learning.domain.catalog.entities import Video
from e_learning.domain.catalog.exceptions import (
    AiJobConflict,
    MediaNotReady,
    TranscriptionNotReady,
)
from e_learning.domain.catalog.job import Job
from e_learning.domain.catalog.repository import JobRepository, VideoRepository
from e_learning.domain.catalog.value_objects import VideoId


class StartSummaryGeneration:
    def __init__(
        self,
        videos: VideoRepository,
        media_files: MediaFilePort,
        jobs: JobRepository,
        publisher: JobPublisherPort,
    ) -> None:
        self._videos = videos
        self._media_files = media_files
        self._jobs = jobs
        self._publisher = publisher

    async def execute(self, video_id: str) -> VideoDTO:
        video = await self._videos.get(VideoId.from_string(video_id))
        if video.processing_status != Video.STATUS_READY:
            raise MediaNotReady(video_id, video.processing_status)

        has_txt = (
            self._media_files.read_text(
                self._media_files.transcription_path(str(video.relative_path))
            )
            is not None
        )
        has_md = (
            self._media_files.read_text(self._media_files.summary_path(str(video.relative_path)))
            is not None
        )

        # Cohérence DB↔FS : sidecar présent → ready (évite « Génération… » fantôme)
        if has_md and video.summary_status != Video.AI_READY:
            video.set_summary_status(Video.AI_READY)
            if has_txt and video.transcription_status != Video.AI_READY:
                video.set_transcription_status(Video.AI_READY)
            await self._videos.save(video)
            return VideoDTO.from_entity(video)

        if video.summary_status == Video.AI_PROCESSING:
            raise AiJobConflict(video_id, "summary", video.summary_status)

        # Toujours exiger le fichier .txt (pas seulement le statut DB) :
        # un ready fantôme arrive si le sidecar est resté en ``*.src.txt``
        # après conversion.
        if not has_txt:
            if video.transcription_status == Video.AI_READY:
                video.set_transcription_status(Video.AI_NONE)
                await self._videos.save(video)
            raise TranscriptionNotReady(video_id)

        if video.transcription_status != Video.AI_READY:
            video.set_transcription_status(Video.AI_READY)

        video.set_summary_status(Video.AI_PROCESSING)
        await self._videos.save(video)
        job = await create_queued_job(
            self._jobs,
            kind=Job.KIND_SUMMARY,
            video_id=str(video.id),
            message="Résumé en file d'attente",
        )
        await publish_compute_job(self._publisher, job)
        return VideoDTO.from_entity(video, active_jobs=(job,))
