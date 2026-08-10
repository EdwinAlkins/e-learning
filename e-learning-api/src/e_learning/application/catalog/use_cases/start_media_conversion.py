"""Reconstruit / démarre une conversion média asynchrone."""

from __future__ import annotations

from pathlib import PurePosixPath

from e_learning.application.catalog.dto import MediaConversionJob, VideoDTO
from e_learning.application.catalog.media_kind import (
    source_staging_filename,
    target_extension,
)
from e_learning.application.jobs.create_job import create_queued_job
from e_learning.application.jobs.enqueue import publish_compute_job
from e_learning.application.shared.messaging import JobPublisherPort
from e_learning.application.shared.storage import CatalogStoragePort
from e_learning.domain.catalog.entities import Video
from e_learning.domain.catalog.exceptions import AiJobConflict, MediaNotReady
from e_learning.domain.catalog.job import Job
from e_learning.domain.catalog.repository import JobRepository, VideoRepository
from e_learning.domain.catalog.value_objects import RelativePath, VideoId


def conversion_job_from_staging(
    *,
    video_id: str,
    relative_path: str,
    kind: str,
    job_id: str | None = None,
) -> MediaConversionJob | None:
    """Reconstruit un job si ``relative_path`` est un fichier staging ``*.src.*``."""
    path = PurePosixPath(relative_path)
    name = path.name
    marker = ".src."
    if marker not in name:
        return None
    stem, _, src_rest = name.partition(marker)
    if not stem or not src_rest:
        return None
    target_name = f"{stem}{target_extension(kind)}"
    return MediaConversionJob(
        video_id=video_id,
        source_relative_path=relative_path,
        target_relative_path=str(path.with_name(target_name)),
        kind=kind,
        job_id=job_id,
    )


class StartMediaConversion:
    """Conversion manuelle (studio) : échec à relancer, ou média ready à ré-encoder."""

    def __init__(
        self,
        videos: VideoRepository,
        storage: CatalogStoragePort,
        jobs: JobRepository,
        publisher: JobPublisherPort,
    ) -> None:
        self._videos = videos
        self._storage = storage
        self._jobs = jobs
        self._publisher = publisher

    async def execute(self, video_id: str) -> tuple[VideoDTO, MediaConversionJob]:
        video = await self._videos.get(VideoId.from_string(video_id))
        if video.processing_status == Video.STATUS_PROCESSING:
            raise AiJobConflict(video_id, "conversion", video.processing_status)

        job = conversion_job_from_staging(
            video_id=str(video.id),
            relative_path=str(video.relative_path),
            kind=video.kind,
        )
        if job is not None:
            video.mark_processing()
            await self._videos.save(video)
            job_dto = await create_queued_job(
                self._jobs,
                kind=Job.KIND_MEDIA_CONVERSION,
                video_id=str(video.id),
                message="Conversion en file d'attente",
            )
            job = MediaConversionJob(
                video_id=job.video_id,
                source_relative_path=job.source_relative_path,
                target_relative_path=job.target_relative_path,
                kind=job.kind,
                job_id=job_dto.id,
            )
            await publish_compute_job(self._publisher, job_dto)
            return VideoDTO.from_entity(video, active_jobs=(job_dto,)), job

        if video.processing_status != Video.STATUS_READY:
            raise MediaNotReady(video_id, video.processing_status)

        current = PurePosixPath(str(video.relative_path))
        stem = current.stem
        staging_name = source_staging_filename(stem, current.name)
        staging_rel = str(current.with_name(staging_name))
        target_name = f"{stem}{target_extension(video.kind)}"
        target_rel = str(current.with_name(target_name))

        if staging_rel != str(video.relative_path):
            self._storage.move_file(str(video.relative_path), staging_rel)

        video.filename = staging_name
        video.relative_path = RelativePath(staging_rel)
        video.mark_processing()
        await self._videos.save(video)

        job_dto = await create_queued_job(
            self._jobs,
            kind=Job.KIND_MEDIA_CONVERSION,
            video_id=str(video.id),
            message="Conversion en file d'attente",
        )
        job = MediaConversionJob(
            video_id=str(video.id),
            source_relative_path=staging_rel,
            target_relative_path=target_rel,
            kind=video.kind,
            job_id=job_dto.id,
        )
        await publish_compute_job(self._publisher, job_dto)
        return VideoDTO.from_entity(video, active_jobs=(job_dto,)), job
