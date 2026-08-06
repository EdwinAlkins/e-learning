"""Use case : démarrer une transcription asynchrone."""

from __future__ import annotations

from e_learning.application.catalog.dto import VideoDTO
from e_learning.application.jobs.create_job import create_queued_job
from e_learning.application.shared.media import MediaFilePort
from e_learning.domain.catalog.entities import Video
from e_learning.domain.catalog.exceptions import AiJobConflict, MediaNotReady
from e_learning.domain.catalog.job import Job
from e_learning.domain.catalog.repository import JobRepository, VideoRepository
from e_learning.domain.catalog.value_objects import VideoId


class StartTranscription:
    def __init__(
        self,
        videos: VideoRepository,
        media_files: MediaFilePort,
        jobs: JobRepository,
    ) -> None:
        self._videos = videos
        self._media_files = media_files
        self._jobs = jobs

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
        # Cohérence DB↔FS : .txt présent → ready (évite « Transcription… » fantôme)
        if has_txt:
            if video.transcription_status != Video.AI_READY:
                video.set_transcription_status(Video.AI_READY)
                await self._videos.save(video)
            return VideoDTO.from_entity(video)

        if video.transcription_status == Video.AI_PROCESSING:
            raise AiJobConflict(video_id, "transcription", video.transcription_status)

        video.set_transcription_status(Video.AI_PROCESSING)
        await self._videos.save(video)
        job = await create_queued_job(
            self._jobs,
            kind=Job.KIND_TRANSCRIPTION,
            video_id=str(video.id),
            message="Transcription en file d'attente",
        )
        return VideoDTO.from_entity(video, active_jobs=(job,))
