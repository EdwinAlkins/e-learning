"""Use case : résoudre le chemin absolu d'une vidéo."""

from __future__ import annotations

from pathlib import Path

from e_learning.application.shared.storage import CatalogStoragePort
from e_learning.domain.catalog.entities import Video
from e_learning.domain.catalog.exceptions import MediaNotReady, VideoNotFound
from e_learning.domain.catalog.repository import VideoRepository
from e_learning.domain.catalog.value_objects import VideoId


class GetVideoPath:
    def __init__(self, videos: VideoRepository, storage: CatalogStoragePort) -> None:
        self._videos = videos
        self._storage = storage

    async def execute(self, video_id: str) -> Path:
        video = await self._videos.get(VideoId.from_string(video_id))
        if video.processing_status != Video.STATUS_READY:
            raise MediaNotReady(video_id, video.processing_status)
        path = self._storage.absolute_path(str(video.relative_path))
        if not path.is_file():
            raise VideoNotFound(video_id)
        return path
