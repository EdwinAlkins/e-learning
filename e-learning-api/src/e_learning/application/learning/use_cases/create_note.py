"""Use case : créer une note."""

from __future__ import annotations

from e_learning.application.learning.dto import CreateNoteCommand, NoteDTO
from e_learning.domain.catalog.exceptions import VideoNotFound
from e_learning.domain.catalog.repository import VideoRepository
from e_learning.domain.catalog.value_objects import VideoId
from e_learning.domain.learning.entities import Note
from e_learning.domain.learning.repository import NoteRepository
from e_learning.domain.learning.value_objects import NoteContent, TimecodeSeconds
from e_learning.domain.user.exceptions import UserNotFound
from e_learning.domain.user.repository import UserRepository
from e_learning.domain.user.value_objects import UserId


class CreateNote:
    def __init__(
        self,
        notes: NoteRepository,
        users: UserRepository,
        videos: VideoRepository,
    ) -> None:
        self._notes = notes
        self._users = users
        self._videos = videos

    async def execute(self, command: CreateNoteCommand) -> NoteDTO:
        user_id = UserId.from_string(command.user_id)
        video_id = VideoId.from_string(command.video_id)
        if not await self._users.exists(user_id):
            raise UserNotFound(str(user_id))
        if not await self._videos.exists(video_id):
            raise VideoNotFound(str(video_id))
        note = Note.create(
            user_id=user_id,
            video_id=video_id,
            timecode=TimecodeSeconds(command.timecode),
            content=NoteContent(command.content),
        )
        await self._notes.save(note)
        return NoteDTO.from_entity(note)
