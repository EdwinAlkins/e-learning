"""Use case : supprimer une note."""

from __future__ import annotations

from e_learning.domain.learning.exceptions import NoteNotFound
from e_learning.domain.learning.repository import NoteRepository
from e_learning.domain.learning.value_objects import NoteId
from e_learning.domain.user.value_objects import UserId


class DeleteNote:
    def __init__(self, notes: NoteRepository) -> None:
        self._notes = notes

    async def execute(self, *, note_id: str, user_id: str) -> None:
        note = await self._notes.get(NoteId.from_string(note_id))
        if note.user_id != UserId.from_string(user_id):
            raise NoteNotFound(note_id)
        await self._notes.delete(NoteId.from_string(note_id))
