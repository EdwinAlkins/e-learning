"""Router documents annexes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse

from e_learning.application.catalog.use_cases.get_document_path import GetDocumentPath
from e_learning.presentation.api.dependencies import (
    get_get_document_path,
)
from e_learning.presentation.api.dependencies.auth import get_current_user
from e_learning.presentation.api.dependencies.queries import CatalogQueryDep
from e_learning.presentation.api.v1.schemas.common import DocumentResponse

router = APIRouter(
    prefix="/docs",
    tags=["docs"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/chapters/{chapter_id}", response_model=list[DocumentResponse])
async def list_documents(
    chapter_id: str,
    queries: CatalogQueryDep,
) -> list[DocumentResponse]:
    dtos = await queries.list_chapter_documents(chapter_id)
    return [DocumentResponse.from_dto(d) for d in dtos]


@router.get("/{document_id}/file")
async def download_document(
    document_id: str,
    use_case: Annotated[GetDocumentPath, Depends(get_get_document_path)],
    download: Annotated[bool, Query()] = False,
) -> FileResponse:
    path = await use_case.execute(document_id)
    return FileResponse(
        path,
        filename=path.name,
        content_disposition_type="attachment" if download else "inline",
    )
