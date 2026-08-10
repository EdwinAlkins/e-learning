"""Use case : finaliser une conversion média en arrière-plan."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from pathlib import PurePosixPath

from e_learning.application.catalog.dto import MediaConversionJob
from e_learning.application.shared.media import MediaConvertPort
from e_learning.application.shared.storage import CatalogStoragePort
from e_learning.domain.catalog.entities import Video
from e_learning.domain.catalog.repository import VideoRepository
from e_learning.domain.catalog.value_objects import DurationSeconds, RelativePath, VideoId

logger = logging.getLogger("e_learning")


class CompleteMediaConversion:
    def __init__(
        self,
        videos: VideoRepository,
        storage: CatalogStoragePort,
        converter: MediaConvertPort,
    ) -> None:
        self._videos = videos
        self._storage = storage
        self._converter = converter

    async def execute(
        self,
        job: MediaConversionJob,
        *,
        on_progress: Callable[[int], None] | None = None,
    ) -> None:
        video = await self._videos.get(VideoId.from_string(job.video_id))
        source = self._storage.absolute_path(job.source_relative_path)
        target = self._storage.absolute_path(job.target_relative_path)

        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                target.unlink(missing_ok=True)
                logger.info(
                    "Cible partielle supprimée avant reconversion : %s",
                    job.target_relative_path,
                )

            if job.kind == Video.KIND_AUDIO:
                await asyncio.to_thread(
                    lambda: self._converter.convert_to_mp3(source, target, on_progress=on_progress)
                )
            else:
                await asyncio.to_thread(
                    lambda: self._converter.convert_to_mp4(source, target, on_progress=on_progress)
                )

            duration = await asyncio.to_thread(
                self._storage.probe_duration, job.target_relative_path
            )
            target_name = PurePosixPath(job.target_relative_path).name
            video.finalize_file(
                filename=target_name,
                relative_path=RelativePath(job.target_relative_path),
                duration=DurationSeconds(duration),
            )
            await self._videos.save(video)

            if job.source_relative_path != job.target_relative_path:
                # Les sidecars suivent with_suffix(média) : pendant le staging
                # ``clip.src.mkv`` → ``clip.src.txt`` ; après conversion il faut
                # les ramener sur ``clip.mp4`` → ``clip.txt`` / ``clip.md``.
                for suffix in (".md", ".txt"):
                    old_side = source.with_suffix(suffix)
                    new_side = target.with_suffix(suffix)
                    if not old_side.is_file():
                        continue
                    if old_side.resolve() == new_side.resolve():
                        continue
                    new_side.parent.mkdir(parents=True, exist_ok=True)
                    if new_side.exists():
                        new_side.unlink()
                    old_side.rename(new_side)
                    logger.info(
                        "Sidecar déplacé après conversion : %s → %s",
                        old_side.name,
                        new_side.name,
                    )
                if source.exists():
                    source.unlink(missing_ok=True)
        except Exception:
            logger.exception("Conversion média échouée pour %s", job.video_id)
            video.mark_failed()
            await self._videos.save(video)
            raise
