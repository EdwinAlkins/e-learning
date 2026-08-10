"""Use case : uploader une vidéo / un audio dans un chapitre."""

from __future__ import annotations

import asyncio
from pathlib import PurePosixPath

from e_learning.application.catalog.dto import (
    CreateVideoCommand,
    CreateVideoResult,
    MediaConversionJob,
    VideoDTO,
)
from e_learning.application.catalog.media_kind import (
    classify_media_kind,
    needs_auto_conversion,
    source_staging_filename,
    target_extension,
)
from e_learning.application.jobs.create_job import create_queued_job
from e_learning.application.jobs.enqueue import publish_compute_job
from e_learning.application.shared.messaging import JobPublisherPort
from e_learning.application.shared.storage import CatalogStoragePort
from e_learning.domain.catalog.entities import Video
from e_learning.domain.catalog.job import Job
from e_learning.domain.catalog.repository import (
    ChapterRepository,
    FormationRepository,
    JobRepository,
    VideoRepository,
)
from e_learning.domain.catalog.value_objects import (
    ChapterId,
    DurationSeconds,
    Position,
    RelativePath,
    VideoTitle,
    slugify,
)


class CreateVideo:
    def __init__(
        self,
        formations: FormationRepository,
        chapters: ChapterRepository,
        videos: VideoRepository,
        storage: CatalogStoragePort,
        jobs: JobRepository,
        publisher: JobPublisherPort,
    ) -> None:
        self._formations = formations
        self._chapters = chapters
        self._videos = videos
        self._storage = storage
        self._jobs = jobs
        self._publisher = publisher

    async def execute(self, command: CreateVideoCommand) -> CreateVideoResult:
        chapter = await self._chapters.get(ChapterId.from_string(command.chapter_id))
        formation = await self._formations.get(chapter.formation_id)
        title = VideoTitle(command.title)
        position = Position(await self._videos.next_position(chapter.id))
        base_stem = slugify(str(title)) or "video"
        kind = classify_media_kind(command.filename)
        target_ext = target_extension(kind)

        counter = 0
        while True:
            stem = base_stem if counter == 0 else f"{base_stem}-{counter}"
            target_filename = f"{stem}{target_ext}"
            target_relative = RelativePath(
                str(PurePosixPath(str(formation.slug)) / str(chapter.slug) / target_filename)
            )
            staging_filename = source_staging_filename(stem, command.filename)
            staging_relative = RelativePath(
                str(PurePosixPath(str(formation.slug)) / str(chapter.slug) / staging_filename)
            )
            if (
                not self._storage.file_exists(str(target_relative))
                and not self._storage.file_exists(str(staging_relative))
                and await self._videos.find_by_relative_path(target_relative) is None
                and await self._videos.find_by_relative_path(staging_relative) is None
            ):
                break
            counter += 1

        duration = await asyncio.to_thread(
            self._storage.write_video, str(staging_relative), command.file_bytes
        )

        # Conversion auto uniquement si le conteneur n'est pas déjà mp4/mp3
        # (pas de probe codec — évite les ré-encodages inutiles).
        if not needs_auto_conversion(command.filename, kind):
            if str(staging_relative) != str(target_relative):
                await asyncio.to_thread(
                    self._storage.move_file, str(staging_relative), str(target_relative)
                )
            video = Video.create(
                chapter_id=chapter.id,
                title=title,
                filename=target_filename,
                relative_path=target_relative,
                position=position,
                duration=DurationSeconds(duration),
                kind=kind,
                processing_status=Video.STATUS_READY,
            )
            await self._videos.save(video)
            return CreateVideoResult(video=VideoDTO.from_entity(video))

        video = Video.create(
            chapter_id=chapter.id,
            title=title,
            filename=staging_filename,
            relative_path=staging_relative,
            position=position,
            duration=DurationSeconds(duration),
            kind=kind,
            processing_status=Video.STATUS_PROCESSING,
        )
        await self._videos.save(video)
        job_dto = await create_queued_job(
            self._jobs,
            kind=Job.KIND_MEDIA_CONVERSION,
            video_id=str(video.id),
            message="Conversion en file d'attente",
        )
        await publish_compute_job(self._publisher, job_dto)
        return CreateVideoResult(
            video=VideoDTO.from_entity(video, active_jobs=(job_dto,)),
            conversion=MediaConversionJob(
                video_id=str(video.id),
                source_relative_path=str(staging_relative),
                target_relative_path=str(target_relative),
                kind=kind,
                job_id=job_dto.id,
            ),
        )
