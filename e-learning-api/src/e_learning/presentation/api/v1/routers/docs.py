"""Router documents annexes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import FileResponse

from e_learning.application.catalog.dto import UpdateDocumentCommand
from e_learning.application.catalog.use_cases.delete_document import DeleteDocument
from e_learning.application.catalog.use_cases.get_document_path import GetDocumentPath
from e_learning.application.catalog.use_cases.list_chapter_documents import ListChapterDocuments
from e_learning.application.catalog.use_cases.update_document import UpdateDocument
from e_learning.presentation.api.dependencies import (
    get_delete_document,
    get_get_document_path,
    get_list_chapter_documents,
    get_update_document,
)
from e_learning.presentation.api.dependencies.auth import CurrentUserIdDep
from e_learning.presentation.api.v1.schemas.common import DocumentResponse, DocumentUpdateRequest

router = APIRouter(prefix="/docs", tags=["docs"])


@router.get("/chapters/{chapter_id}", response_model=list[DocumentResponse])
async def list_documents(
    chapter_id: str,
    _user_id: CurrentUserIdDep,
    use_case: Annotated[ListChapterDocuments, Depends(get_list_chapter_documents)],
) -> list[DocumentResponse]:
    dtos = await use_case.execute(chapter_id)
    return [DocumentResponse.from_dto(d) for d in dtos]


@router.patch("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: str,
    payload: DocumentUpdateRequest,
    _user_id: CurrentUserIdDep,
    use_case: Annotated[UpdateDocument, Depends(get_update_document)],
) -> DocumentResponse:
    dto = await use_case.execute(
        UpdateDocumentCommand(
            document_id=document_id,
            title=payload.title,
            video_id=payload.video_id,
            update_video_id="video_id" in payload.model_fields_set,
        )
    )
    return DocumentResponse.from_dto(dto)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    _user_id: CurrentUserIdDep,
    use_case: Annotated[DeleteDocument, Depends(get_delete_document)],
) -> None:
    await use_case.execute(document_id)


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
