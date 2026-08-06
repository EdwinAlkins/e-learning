"""Use case : supprimer une vidéo."""

from __future__ import annotations

import logging

from e_learning.application.shared.storage import CatalogStoragePort
from e_learning.domain.catalog.repository import VideoRepository
from e_learning.domain.catalog.value_objects import VideoId

logger = logging.getLogger("e_learning")


class DeleteVideo:
    def __init__(self, videos: VideoRepository, storage: CatalogStoragePort) -> None:
        self._videos = videos
        self._storage = storage

    async def execute(self, video_id: str) -> None:
        video = await self._videos.get(VideoId.from_string(video_id))
        relative_path = str(video.relative_path)
        # DB d'abord : la transaction HTTP commit après le use case ; FS best-effort.
        await self._videos.delete(video.id)
        try:
            self._storage.delete_file(relative_path)
        except Exception:
            logger.exception(
                "Suppression FS échouée après delete DB (vidéo %s, path=%s)",
                video_id,
                relative_path,
            )
