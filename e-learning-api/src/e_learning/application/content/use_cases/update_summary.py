"""Use case : mettre à jour manuellement un résumé (crée le fichier si besoin)."""

from __future__ import annotations

from e_learning.application.content.dto import SummaryDTO, UpdateSummaryCommand
from e_learning.application.shared.media import MediaFilePort
from e_learning.domain.catalog.entities import Video
from e_learning.domain.catalog.repository import VideoRepository
from e_learning.domain.catalog.value_objects import VideoId


class UpdateSummary:
    def __init__(self, videos: VideoRepository, media_files: MediaFilePort) -> None:
        self._videos = videos
        self._media_files = media_files

    async def execute(self, command: UpdateSummaryCommand) -> SummaryDTO:
        video = await self._videos.get(VideoId.from_string(command.video_id))
        path = self._media_files.summary_path(str(video.relative_path))
        self._media_files.write_text(path, command.summary)
        if video.summary_status != Video.AI_READY:
            video.set_summary_status(Video.AI_READY)
            await self._videos.save(video)
        return SummaryDTO(summary=command.summary)
