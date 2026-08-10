"""Use case : mettre à jour une vidéo (titre et/ou fichier)."""

from __future__ import annotations

import asyncio
from pathlib import PurePosixPath

from e_learning.application.catalog.dto import (
    MediaConversionJob,
    RenameVideoCommand,
    RenameVideoResult,
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
from e_learning.domain.catalog.job import Job
from e_learning.domain.catalog.repository import (
    ChapterRepository,
    FormationRepository,
    JobRepository,
    VideoRepository,
)
from e_learning.domain.catalog.value_objects import (
    DurationSeconds,
    RelativePath,
    VideoId,
    VideoTitle,
    slugify,
)
from e_learning.domain.shared.exceptions import ValidationError


class RenameVideo:
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

    async def execute(self, command: RenameVideoCommand) -> RenameVideoResult:
        if command.title is None and command.file_bytes is None:
            raise ValidationError("Fournir au moins un titre ou un fichier.")

        video = await self._videos.get(VideoId.from_string(command.video_id))
        chapter = await self._chapters.get(video.chapter_id)
        formation = await self._formations.get(chapter.formation_id)
        conversion: MediaConversionJob | None = None

        if command.title is not None:
            title = VideoTitle(command.title)
            stem = slugify(str(title)) or "video"
            ext = target_extension(video.kind)
            # Si le fichier courant est encore un staging (.src…), conserver le suffixe staging
            current_name = PurePosixPath(str(video.relative_path)).name
            if ".src" in current_name:
                filename = source_staging_filename(stem, current_name.split(".src", 1)[-1])
            else:
                filename = f"{stem}{PurePosixPath(current_name).suffix or ext}"
            new_rel = RelativePath(
                str(PurePosixPath(str(formation.slug)) / str(chapter.slug) / filename)
            )
            if str(new_rel) != str(video.relative_path):
                self._storage.move_file(str(video.relative_path), str(new_rel))
                video.relocate(
                    chapter_id=video.chapter_id,
                    position=video.position,
                    relative_path=new_rel,
                    filename=filename,
                )
            video.rename(title, filename=filename)

        if command.file_bytes is not None:
            original_name = command.filename or "media"
            kind = classify_media_kind(original_name)
            video.set_kind(kind)
            stem = slugify(str(video.title)) or "video"
            target_ext = target_extension(kind)
            target_filename = f"{stem}{target_ext}"
            target_relative = RelativePath(
                str(PurePosixPath(str(formation.slug)) / str(chapter.slug) / target_filename)
            )
            staging_filename = source_staging_filename(stem, original_name)
            staging_relative = RelativePath(
                str(PurePosixPath(str(formation.slug)) / str(chapter.slug) / staging_filename)
            )

            old_path = str(video.relative_path)
            duration = await asyncio.to_thread(
                self._storage.write_video, str(staging_relative), command.file_bytes
            )
            if old_path != str(staging_relative):
                self._storage.delete_file(old_path)

            if not needs_auto_conversion(original_name, kind):
                if str(staging_relative) != str(target_relative):
                    await asyncio.to_thread(
                        self._storage.move_file, str(staging_relative), str(target_relative)
                    )
                video.finalize_file(
                    filename=target_filename,
                    relative_path=target_relative,
                    duration=DurationSeconds(duration),
                )
            else:
                video.filename = staging_filename
                video.relative_path = staging_relative
                video.update_duration(DurationSeconds(duration))
                video.mark_processing()
                job_dto = await create_queued_job(
                    self._jobs,
                    kind=Job.KIND_MEDIA_CONVERSION,
                    video_id=str(video.id),
                    message="Conversion en file d'attente",
                )
                conversion = MediaConversionJob(
                    video_id=str(video.id),
                    source_relative_path=str(staging_relative),
                    target_relative_path=str(target_relative),
                    kind=kind,
                    job_id=job_dto.id,
                )
                await self._videos.save(video)
                await publish_compute_job(self._publisher, job_dto)
                return RenameVideoResult(
                    video=VideoDTO.from_entity(video, active_jobs=(job_dto,)),
                    conversion=conversion,
                )

        await self._videos.save(video)
        return RenameVideoResult(video=VideoDTO.from_entity(video), conversion=conversion)
