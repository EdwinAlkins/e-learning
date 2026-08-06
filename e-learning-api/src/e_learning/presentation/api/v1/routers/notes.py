"""Router notes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from e_learning.application.learning.dto import CreateNoteCommand, UpdateNoteCommand
from e_learning.application.learning.use_cases.create_note import CreateNote
from e_learning.application.learning.use_cases.delete_note import DeleteNote
from e_learning.application.learning.use_cases.list_notes import ListNotes
from e_learning.application.learning.use_cases.update_note import UpdateNote
from e_learning.presentation.api.dependencies import (
    get_create_note,
    get_delete_note,
    get_list_notes,
    get_update_note,
)
from e_learning.presentation.api.dependencies.auth import CurrentUserIdDep
from e_learning.presentation.api.v1.schemas.common import (
    NoteCreateRequest,
    NoteResponse,
    NoteUpdateRequest,
)

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("/{video_id}", response_model=list[NoteResponse])
async def list_notes(
    video_id: str,
    user_id: CurrentUserIdDep,
    use_case: Annotated[ListNotes, Depends(get_list_notes)],
) -> list[NoteResponse]:
    dtos = await use_case.execute(user_id=user_id, video_id=video_id)
    return [NoteResponse.from_dto(n) for n in dtos]


@router.post("/{video_id}", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    video_id: str,
    payload: NoteCreateRequest,
    user_id: CurrentUserIdDep,
    use_case: Annotated[CreateNote, Depends(get_create_note)],
) -> NoteResponse:
    dto = await use_case.execute(
        CreateNoteCommand(
            user_id=user_id,
            video_id=video_id,
            timecode=payload.timecode,
            content=payload.content,
        )
    )
    return NoteResponse.from_dto(dto)


@router.put("/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: str,
    payload: NoteUpdateRequest,
    user_id: CurrentUserIdDep,
    use_case: Annotated[UpdateNote, Depends(get_update_note)],
) -> NoteResponse:
    dto = await use_case.execute(
        UpdateNoteCommand(note_id=note_id, user_id=user_id, content=payload.content)
    )
    return NoteResponse.from_dto(dto)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: str,
    user_id: CurrentUserIdDep,
    use_case: Annotated[DeleteNote, Depends(get_delete_note)],
) -> None:
    await use_case.execute(note_id=note_id, user_id=user_id)
