"""Use case : lire la position de lecture."""

from __future__ import annotations

from e_learning.application.learning.dto import ProgressDTO
from e_learning.domain.catalog.value_objects import VideoId
from e_learning.domain.learning.repository import ProgressRepository
from e_learning.domain.user.value_objects import UserId


class GetProgress:
    def __init__(self, progress: ProgressRepository) -> None:
        self._progress = progress

    async def execute(self, *, user_id: str, video_id: str) -> ProgressDTO:
        found = await self._progress.find_by_user_and_video(
            UserId.from_string(user_id),
            VideoId.from_string(video_id),
        )
        if found is None:
            return ProgressDTO(last_position=0.0)
        return ProgressDTO.from_entity(found)
