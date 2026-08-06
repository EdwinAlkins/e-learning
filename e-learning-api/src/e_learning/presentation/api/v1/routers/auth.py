"""Router auth."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from e_learning.application.user.use_cases.generate_user import GenerateUser
from e_learning.application.user.use_cases.restore_user import RestoreUser
from e_learning.presentation.api.dependencies import get_generate_user, get_restore_user
from e_learning.presentation.api.v1.schemas.common import RestoreRequest, UIDResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/generate", response_model=UIDResponse)
async def generate(
    use_case: Annotated[GenerateUser, Depends(get_generate_user)],
) -> UIDResponse:
    return UIDResponse.from_dto(await use_case.execute())


@router.post("/restore", response_model=UIDResponse)
async def restore(
    payload: RestoreRequest,
    use_case: Annotated[RestoreUser, Depends(get_restore_user)],
) -> UIDResponse:
    return UIDResponse.from_dto(await use_case.execute(payload.uid))
