"""Router progress."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from e_learning.application.learning.dto import UpsertProgressCommand
from e_learning.application.learning.use_cases.upsert_progress import UpsertProgress
from e_learning.presentation.api.dependencies import (
    get_upsert_progress,
)
from e_learning.presentation.api.dependencies.auth import CurrentUserIdDep
from e_learning.presentation.api.dependencies.queries import LearningQueryDep
from e_learning.presentation.api.v1.schemas.common import (
    FormationProgressResponse,
    FormationsProgressResponse,
    ProgressResponse,
    ProgressUpdateRequest,
)

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("/formations", response_model=FormationsProgressResponse)
async def list_formations_progress(
    user_id: CurrentUserIdDep,
    queries: LearningQueryDep,
) -> FormationsProgressResponse:
    data = await queries.list_formations_progress(user_id=user_id)
    return FormationsProgressResponse(
        progress={k: FormationProgressResponse.from_dto(v) for k, v in data.items()}
    )


@router.get("/formation/{formation_id}", response_model=FormationProgressResponse)
async def get_formation_progress(
    formation_id: str,
    user_id: CurrentUserIdDep,
    queries: LearningQueryDep,
) -> FormationProgressResponse:
    dto = await queries.get_formation_progress(user_id=user_id, formation_id=formation_id)
    return FormationProgressResponse.from_dto(dto)


@router.get("/{video_id}", response_model=ProgressResponse)
async def get_progress(
    video_id: str,
    user_id: CurrentUserIdDep,
    queries: LearningQueryDep,
) -> ProgressResponse:
    dto = await queries.get_progress(user_id=user_id, video_id=video_id)
    return ProgressResponse(last_position=dto.last_position)


@router.post("/{video_id}", response_model=ProgressResponse)
async def upsert_progress(
    video_id: str,
    payload: ProgressUpdateRequest,
    user_id: CurrentUserIdDep,
    use_case: Annotated[UpsertProgress, Depends(get_upsert_progress)],
) -> ProgressResponse:
    dto = await use_case.execute(
        UpsertProgressCommand(
            user_id=user_id,
            video_id=video_id,
            last_position=payload.last_position,
        )
    )
    return ProgressResponse(last_position=dto.last_position)
