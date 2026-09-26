"""Router consommation LLM de l'utilisateur courant."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from e_learning.presentation.api.dependencies.auth import CurrentUserIdDep
from e_learning.presentation.api.dependencies.queries import UsageQueryDep
from e_learning.presentation.api.v1.schemas.usage import UserTokenUsageResponse

router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("", response_model=UserTokenUsageResponse)
async def get_my_usage(
    user_id: CurrentUserIdDep,
    queries: UsageQueryDep,
    days: Annotated[int, Query(ge=1, le=365)] = 30,
) -> UserTokenUsageResponse:
    dto = await queries.get_user_usage(user_id=user_id, days=days)
    return UserTokenUsageResponse.from_dto(dto)
