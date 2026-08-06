"""Use case : enregistrer la position de lecture."""

from __future__ import annotations

from e_learning.application.learning.dto import ProgressDTO, UpsertProgressCommand
from e_learning.domain.catalog.exceptions import VideoNotFound
from e_learning.domain.catalog.repository import VideoRepository
from e_learning.domain.catalog.value_objects import VideoId
from e_learning.domain.learning.entities import Progress
from e_learning.domain.learning.repository import ProgressRepository
from e_learning.domain.learning.value_objects import LastPositionSeconds
from e_learning.domain.user.exceptions import UserNotFound
from e_learning.domain.user.repository import UserRepository
from e_learning.domain.user.value_objects import UserId


class UpsertProgress:
    def __init__(
        self,
        progress: ProgressRepository,
        users: UserRepository,
        videos: VideoRepository,
    ) -> None:
        self._progress = progress
        self._users = users
        self._videos = videos

    async def execute(self, command: UpsertProgressCommand) -> ProgressDTO:
        user_id = UserId.from_string(command.user_id)
        video_id = VideoId.from_string(command.video_id)
        if not await self._users.exists(user_id):
            raise UserNotFound(str(user_id))
        if not await self._videos.exists(video_id):
            raise VideoNotFound(str(video_id))
        existing = await self._progress.find_by_user_and_video(user_id, video_id)
        position = LastPositionSeconds(command.last_position)
        if existing is None:
            entity = Progress.create(user_id=user_id, video_id=video_id, last_position=position)
        else:
            entity = existing
            entity.update_position(position)
        await self._progress.save(entity)
        return ProgressDTO.from_entity(entity)
