"""Use case : lister les notes d'une vidéo pour un utilisateur."""

from __future__ import annotations

from e_learning.application.learning.dto import NoteDTO
from e_learning.domain.catalog.value_objects import VideoId
from e_learning.domain.learning.repository import NoteRepository
from e_learning.domain.user.value_objects import UserId


class ListNotes:
    def __init__(self, notes: NoteRepository) -> None:
        self._notes = notes

    async def execute(self, *, user_id: str, video_id: str) -> list[NoteDTO]:
        notes = await self._notes.list_by_user_and_video(
            UserId.from_string(user_id),
            VideoId.from_string(video_id),
        )
        return [NoteDTO.from_entity(n) for n in notes]
