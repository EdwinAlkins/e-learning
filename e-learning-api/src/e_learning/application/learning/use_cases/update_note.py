"""Use case : mettre à jour le contenu d'une note."""

from __future__ import annotations

from e_learning.application.learning.dto import NoteDTO, UpdateNoteCommand
from e_learning.domain.learning.exceptions import NoteNotFound
from e_learning.domain.learning.repository import NoteRepository
from e_learning.domain.learning.value_objects import NoteContent, NoteId
from e_learning.domain.user.value_objects import UserId


class UpdateNote:
    def __init__(self, notes: NoteRepository) -> None:
        self._notes = notes

    async def execute(self, command: UpdateNoteCommand) -> NoteDTO:
        note = await self._notes.get(NoteId.from_string(command.note_id))
        if note.user_id != UserId.from_string(command.user_id):
            raise NoteNotFound(command.note_id)
        note.update_content(NoteContent(command.content))
        await self._notes.save(note)
        return NoteDTO.from_entity(note)
