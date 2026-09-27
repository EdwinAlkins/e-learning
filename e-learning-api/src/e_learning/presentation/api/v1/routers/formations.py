"""Router formations (lecture du catalogue, questions RAG)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from e_learning.application.content.dto import AskFormationCommand
from e_learning.application.content.use_cases.ask_formation import AskFormation
from e_learning.presentation.api.dependencies import (
    get_ask_formation,
)
from e_learning.presentation.api.dependencies.auth import CurrentUserDep, get_current_user
from e_learning.presentation.api.dependencies.queries import CatalogQueryDep
from e_learning.presentation.api.v1.schemas.common import (
    AskFormationRequest,
    AskFormationResponse,
    CatalogResponse,
    FormationResponse,
    RagCitationResponse,
)

formations_router = APIRouter(
    prefix="/formations",
    tags=["formations"],
    dependencies=[Depends(get_current_user)],
)


@formations_router.get("", response_model=CatalogResponse)
async def list_formations(
    queries: CatalogQueryDep,
) -> CatalogResponse:
    dtos = await queries.list_formations()
    return CatalogResponse(formations=[FormationResponse.from_dto(f) for f in dtos])


@formations_router.get("/{formation_id}", response_model=FormationResponse)
async def get_formation(
    formation_id: str,
    queries: CatalogQueryDep,
) -> FormationResponse:
    return FormationResponse.from_dto(await queries.get_formation(formation_id))


@formations_router.post("/{formation_id}/ask", response_model=AskFormationResponse)
async def ask_formation(
    formation_id: str,
    payload: AskFormationRequest,
    user: CurrentUserDep,
    use_case: Annotated[AskFormation, Depends(get_ask_formation)],
) -> AskFormationResponse:
    result = await use_case.execute(
        AskFormationCommand(formation_id=formation_id, question=payload.question, user_id=user.id)
    )
    return AskFormationResponse(
        answer=result.answer,
        citations=[
            RagCitationResponse(
                video_id=c.video_id,
                document_id=c.document_id,
                title=c.title,
                source=c.source,
                excerpt=c.excerpt,
            )
            for c in result.citations
        ],
    )
