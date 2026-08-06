"""Use case : lire le résumé d'une vidéo."""

from __future__ import annotations

from e_learning.application.content.dto import SummaryDTO
from e_learning.application.shared.errors import SummaryNotFound
from e_learning.application.shared.media import MediaFilePort
from e_learning.domain.catalog.repository import VideoRepository
from e_learning.domain.catalog.value_objects import VideoId


class GetSummary:
    def __init__(self, videos: VideoRepository, media_files: MediaFilePort) -> None:
        self._videos = videos
        self._media_files = media_files

    async def execute(self, video_id: str) -> SummaryDTO:
        video = await self._videos.get(VideoId.from_string(video_id))
        path = self._media_files.summary_path(str(video.relative_path))
        content = self._media_files.read_text(path)
        if content is None:
            raise SummaryNotFound(f"Résumé introuvable pour la vidéo {video_id}")
        return SummaryDTO(summary=content)
