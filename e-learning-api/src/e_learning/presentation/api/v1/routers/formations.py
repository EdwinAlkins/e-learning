"""Routers formations (lecture) + studio (écriture)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status
from fastapi.exceptions import RequestValidationError

from e_learning.application.catalog.dto import (
    CreateChapterCommand,
    CreateDocumentCommand,
    CreateFormationCommand,
    CreateVideoCommand,
    MoveVideoCommand,
    RenameChapterCommand,
    RenameFormationCommand,
    RenameVideoCommand,
    ReorderChaptersCommand,
    ReorderVideosCommand,
)
from e_learning.application.catalog.use_cases.create_chapter import CreateChapter
from e_learning.application.catalog.use_cases.create_document import CreateDocument
from e_learning.application.catalog.use_cases.create_formation import CreateFormation
from e_learning.application.catalog.use_cases.create_video import CreateVideo
from e_learning.application.catalog.use_cases.delete_chapter import DeleteChapter
from e_learning.application.catalog.use_cases.delete_formation import DeleteFormation
from e_learning.application.catalog.use_cases.delete_video import DeleteVideo
from e_learning.application.catalog.use_cases.get_formation import GetFormation
from e_learning.application.catalog.use_cases.list_formations import ListFormations
from e_learning.application.catalog.use_cases.move_video import MoveVideo
from e_learning.application.catalog.use_cases.rename_chapter import RenameChapter
from e_learning.application.catalog.use_cases.rename_formation import RenameFormation
from e_learning.application.catalog.use_cases.rename_video import RenameVideo
from e_learning.application.catalog.use_cases.reorder_chapters import ReorderChapters
from e_learning.application.catalog.use_cases.reorder_videos import ReorderVideos
from e_learning.application.content.dto import AskFormationCommand
from e_learning.application.content.use_cases.ask_formation import AskFormation
from e_learning.application.content.use_cases.start_formation_index import StartFormationIndex
from e_learning.presentation.api.dependencies import (
    get_ask_formation,
    get_create_chapter,
    get_create_document,
    get_create_formation,
    get_create_video,
    get_delete_chapter,
    get_delete_formation,
    get_delete_video,
    get_get_formation,
    get_list_formations,
    get_move_video,
    get_rename_chapter,
    get_rename_formation,
    get_rename_video,
    get_reorder_chapters,
    get_reorder_videos,
    get_start_formation_index,
)
from e_learning.presentation.api.uploads import read_upload_limited
from e_learning.presentation.api.v1.schemas.common import (
    AskFormationRequest,
    AskFormationResponse,
    CatalogResponse,
    ChapterResponse,
    DocumentResponse,
    FormationResponse,
    IndexFormationAcceptedResponse,
    MoveVideoRequest,
    NameRequest,
    RagCitationResponse,
    ReorderChaptersRequest,
    ReorderVideosRequest,
    VideoResponse,
    VideoTitleRequest,
)

formations_router = APIRouter(prefix="/formations", tags=["formations"])
studio_router = APIRouter(tags=["studio"])


@formations_router.get("", response_model=CatalogResponse)
async def list_formations(
    use_case: Annotated[ListFormations, Depends(get_list_formations)],
) -> CatalogResponse:
    dtos = await use_case.execute()
    return CatalogResponse(formations=[FormationResponse.from_dto(f) for f in dtos])


@formations_router.get("/{formation_id}", response_model=FormationResponse)
async def get_formation(
    formation_id: str,
    use_case: Annotated[GetFormation, Depends(get_get_formation)],
) -> FormationResponse:
    return FormationResponse.from_dto(await use_case.execute(formation_id))


@formations_router.post("/{formation_id}/ask", response_model=AskFormationResponse)
async def ask_formation(
    formation_id: str,
    payload: AskFormationRequest,
    use_case: Annotated[AskFormation, Depends(get_ask_formation)],
) -> AskFormationResponse:
    result = await use_case.execute(
        AskFormationCommand(formation_id=formation_id, question=payload.question)
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


@formations_router.post(
    "/{formation_id}/index",
    response_model=IndexFormationAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def index_formation(
    formation_id: str,
    use_case: Annotated[StartFormationIndex, Depends(get_start_formation_index)],
) -> IndexFormationAcceptedResponse:
    await use_case.execute(formation_id)
    return IndexFormationAcceptedResponse()


@formations_router.post("", response_model=FormationResponse, status_code=status.HTTP_201_CREATED)
async def create_formation(
    payload: NameRequest,
    use_case: Annotated[CreateFormation, Depends(get_create_formation)],
) -> FormationResponse:
    dto = await use_case.execute(CreateFormationCommand(name=payload.name))
    return FormationResponse.from_dto(dto)


@formations_router.patch("/{formation_id}", response_model=FormationResponse)
async def rename_formation(
    formation_id: str,
    payload: NameRequest,
    use_case: Annotated[RenameFormation, Depends(get_rename_formation)],
) -> FormationResponse:
    dto = await use_case.execute(
        RenameFormationCommand(formation_id=formation_id, name=payload.name)
    )
    return FormationResponse.from_dto(dto)


@formations_router.delete("/{formation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_formation(
    formation_id: str,
    use_case: Annotated[DeleteFormation, Depends(get_delete_formation)],
) -> None:
    await use_case.execute(formation_id)


@formations_router.post(
    "/{formation_id}/chapters",
    response_model=ChapterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_chapter(
    formation_id: str,
    payload: NameRequest,
    use_case: Annotated[CreateChapter, Depends(get_create_chapter)],
) -> ChapterResponse:
    dto = await use_case.execute(CreateChapterCommand(formation_id=formation_id, name=payload.name))
    return ChapterResponse.from_dto(dto)


@studio_router.patch("/chapters/{chapter_id}", response_model=ChapterResponse)
async def rename_chapter(
    chapter_id: str,
    payload: NameRequest,
    use_case: Annotated[RenameChapter, Depends(get_rename_chapter)],
) -> ChapterResponse:
    dto = await use_case.execute(RenameChapterCommand(chapter_id=chapter_id, name=payload.name))
    return ChapterResponse.from_dto(dto)


@studio_router.delete("/chapters/{chapter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chapter(
    chapter_id: str,
    use_case: Annotated[DeleteChapter, Depends(get_delete_chapter)],
) -> None:
    await use_case.execute(chapter_id)


@studio_router.post(
    "/chapters/{chapter_id}/videos",
    response_model=VideoResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_video(
    chapter_id: str,
    request: Request,
    use_case: Annotated[CreateVideo, Depends(get_create_video)],
    title: Annotated[str, Form()],
    file: Annotated[UploadFile, File()],
) -> VideoResponse:
    max_size = request.app.state.settings.max_upload_size
    data = await read_upload_limited(file, max_size=max_size, request=request)
    result = await use_case.execute(
        CreateVideoCommand(
            chapter_id=chapter_id,
            title=title,
            file_bytes=data,
            filename=file.filename or "video",
        )
    )
    return VideoResponse.from_dto(result.video)


@studio_router.post(
    "/chapters/{chapter_id}/docs",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_document(
    chapter_id: str,
    request: Request,
    use_case: Annotated[CreateDocument, Depends(get_create_document)],
    title: Annotated[str, Form()],
    file: Annotated[UploadFile, File()],
    video_id: Annotated[str | None, Form()] = None,
) -> DocumentResponse:
    max_size = request.app.state.settings.max_upload_size
    data = await read_upload_limited(file, max_size=max_size, request=request)
    dto = await use_case.execute(
        CreateDocumentCommand(
            chapter_id=chapter_id,
            title=title,
            file_bytes=data,
            filename=file.filename or "document",
            video_id=video_id or None,
        )
    )
    return DocumentResponse.from_dto(dto)


@studio_router.patch("/videos/{video_id}", response_model=VideoResponse)
async def update_video(
    video_id: str,
    request: Request,
    use_case: Annotated[RenameVideo, Depends(get_rename_video)],
) -> VideoResponse:
    """Met à jour le titre et/ou remplace le fichier vidéo.

    - ``application/json`` : ``{"title": "..."}`` (``name`` accepté en compat)
    - ``multipart/form-data`` : ``title?`` + ``file?`` (au moins l'un des deux)
    """
    content_type = request.headers.get("content-type", "")
    title: str | None = None
    file_bytes: bytes | None = None
    filename: str | None = None

    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        raw_title = form.get("title")
        if raw_title is None:
            raw_title = form.get("name")
        if isinstance(raw_title, str) and raw_title.strip():
            title = raw_title.strip()
        upload = form.get("file")
        if upload is not None and hasattr(upload, "read"):
            max_size = request.app.state.settings.max_upload_size
            file_bytes = await read_upload_limited(upload, max_size=max_size)  # type: ignore[arg-type]
            if not file_bytes:
                file_bytes = None
            else:
                filename = getattr(upload, "filename", None) or "media"
    else:
        payload = VideoTitleRequest.model_validate(await request.json())
        try:
            title = payload.resolved_title()
        except ValueError as exc:
            raise RequestValidationError([{"msg": str(exc), "loc": ("body", "title")}]) from exc

    result = await use_case.execute(
        RenameVideoCommand(
            video_id=video_id,
            title=title,
            file_bytes=file_bytes,
            filename=filename,
        )
    )
    return VideoResponse.from_dto(result.video)


@studio_router.delete("/videos/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(
    video_id: str,
    use_case: Annotated[DeleteVideo, Depends(get_delete_video)],
) -> None:
    await use_case.execute(video_id)


@studio_router.put("/chapters/{chapter_id}/videos/order", response_model=ChapterResponse)
async def reorder_videos(
    chapter_id: str,
    payload: ReorderVideosRequest,
    use_case: Annotated[ReorderVideos, Depends(get_reorder_videos)],
) -> ChapterResponse:
    dto = await use_case.execute(
        ReorderVideosCommand(chapter_id=chapter_id, video_ids=payload.video_ids)
    )
    return ChapterResponse.from_dto(dto)


@formations_router.put(
    "/{formation_id}/chapters/order",
    response_model=FormationResponse,
)
async def reorder_chapters(
    formation_id: str,
    payload: ReorderChaptersRequest,
    use_case: Annotated[ReorderChapters, Depends(get_reorder_chapters)],
) -> FormationResponse:
    dto = await use_case.execute(
        ReorderChaptersCommand(formation_id=formation_id, chapter_ids=payload.chapter_ids)
    )
    return FormationResponse.from_dto(dto)


@studio_router.patch(
    "/chapters/{chapter_id_source}/{chapter_id_target}/{video_id}",
    response_model=FormationResponse,
)
async def move_video(
    chapter_id_source: str,
    chapter_id_target: str,
    video_id: str,
    use_case: Annotated[MoveVideo, Depends(get_move_video)],
    payload: MoveVideoRequest | None = None,
) -> FormationResponse:
    body = payload or MoveVideoRequest()
    dto = await use_case.execute(
        MoveVideoCommand(
            video_id=video_id,
            source_chapter_id=chapter_id_source,
            target_chapter_id=chapter_id_target,
            position=body.position,
            after_video_id=body.after_video_id,
        )
    )
    return FormationResponse.from_dto(dto)
