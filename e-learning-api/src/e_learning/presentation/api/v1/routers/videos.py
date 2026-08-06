"""Router vidéos (stream / file / summary / transcription jobs)."""

from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Request, status
from fastapi.responses import FileResponse, Response
from starlette.responses import StreamingResponse

from e_learning.application.catalog.use_cases.get_video_path import GetVideoPath
from e_learning.application.catalog.use_cases.start_media_conversion import StartMediaConversion
from e_learning.application.content.dto import UpdateSummaryCommand
from e_learning.application.content.use_cases.get_summary import GetSummary
from e_learning.application.content.use_cases.get_transcription import GetTranscription
from e_learning.application.content.use_cases.start_summary_generation import (
    StartSummaryGeneration,
)
from e_learning.application.content.use_cases.start_transcription import StartTranscription
from e_learning.application.content.use_cases.update_summary import UpdateSummary
from e_learning.presentation.api.background import (
    run_media_conversion,
    run_summary_generation,
    run_transcription,
)
from e_learning.presentation.api.dependencies import (
    get_get_summary,
    get_get_transcription,
    get_get_video_path,
    get_start_media_conversion,
    get_start_summary_generation,
    get_start_transcription,
    get_update_summary,
)
from e_learning.presentation.api.http_range import parse_bytes_range
from e_learning.presentation.api.v1.schemas.common import (
    SummaryResponse,
    SummaryUpdateRequest,
    TranscriptionResponse,
    VideoResponse,
)

router = APIRouter(prefix="/videos", tags=["videos"])


def _media_type_for(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".mp3":
        return "audio/mpeg"
    if suffix == ".mp4":
        return "video/mp4"
    guessed, _ = mimetypes.guess_type(path.name)
    return guessed or "application/octet-stream"


@router.get("/{video_id}/file")
async def download_video(
    video_id: str,
    use_case: Annotated[GetVideoPath, Depends(get_get_video_path)],
) -> FileResponse:
    path = await use_case.execute(video_id)
    return FileResponse(path, media_type=_media_type_for(path), filename=path.name)


@router.get("/{video_id}/stream", response_model=None)
async def stream_video(
    video_id: str,
    request: Request,
    use_case: Annotated[GetVideoPath, Depends(get_get_video_path)],
) -> StreamingResponse | Response:
    path = await use_case.execute(video_id)
    file_size = path.stat().st_size
    range_header = request.headers.get("range")
    media_type = _media_type_for(path)

    def _iter(start: int, end: int):
        with path.open("rb") as handle:
            handle.seek(start)
            remaining = end - start + 1
            while remaining > 0:
                chunk = handle.read(min(1024 * 1024, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
                yield chunk

    if range_header and range_header.startswith("bytes="):
        parsed = parse_bytes_range(range_header, file_size)
        if parsed is None:
            return Response(
                status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
                headers={"Content-Range": f"bytes */{file_size}"},
            )
        start, end = parsed
        return StreamingResponse(
            _iter(start, end),
            status_code=206,
            media_type=media_type,
            headers={
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(end - start + 1),
            },
        )
    return StreamingResponse(
        _iter(0, max(file_size - 1, 0)),
        media_type=media_type,
        headers={"Accept-Ranges": "bytes", "Content-Length": str(file_size)},
    )


@router.get("/{video_id}/summary", response_model=SummaryResponse)
async def get_summary(
    video_id: str,
    use_case: Annotated[GetSummary, Depends(get_get_summary)],
) -> SummaryResponse:
    dto = await use_case.execute(video_id)
    return SummaryResponse(summary=dto.summary)


@router.put("/{video_id}/summary", response_model=SummaryResponse)
async def update_summary(
    video_id: str,
    payload: SummaryUpdateRequest,
    use_case: Annotated[UpdateSummary, Depends(get_update_summary)],
) -> SummaryResponse:
    dto = await use_case.execute(UpdateSummaryCommand(video_id=video_id, summary=payload.summary))
    return SummaryResponse(summary=dto.summary)


@router.post(
    "/{video_id}/summary/generate",
    response_model=VideoResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def generate_summary(
    video_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    use_case: Annotated[StartSummaryGeneration, Depends(get_start_summary_generation)],
) -> VideoResponse:
    dto = await use_case.execute(video_id)
    if dto.summary_status == "processing":
        job_id = next((j.id for j in dto.active_jobs if j.kind == "summary"), None)
        background_tasks.add_task(run_summary_generation, request.app, video_id, job_id)
    return VideoResponse.from_dto(dto)


@router.get("/{video_id}/transcription", response_model=TranscriptionResponse)
async def get_transcription(
    video_id: str,
    use_case: Annotated[GetTranscription, Depends(get_get_transcription)],
) -> TranscriptionResponse:
    dto = await use_case.execute(video_id)
    return TranscriptionResponse(content=dto.content)


@router.post(
    "/{video_id}/conversion",
    response_model=VideoResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_media_conversion(
    video_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    use_case: Annotated[StartMediaConversion, Depends(get_start_media_conversion)],
) -> VideoResponse:
    dto, job = await use_case.execute(video_id)
    background_tasks.add_task(run_media_conversion, request.app, job)
    return VideoResponse.from_dto(dto)


@router.post(
    "/{video_id}/transcription",
    response_model=VideoResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_transcription(
    video_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    use_case: Annotated[StartTranscription, Depends(get_start_transcription)],
) -> VideoResponse:
    dto = await use_case.execute(video_id)
    if dto.transcription_status == "processing":
        job_id = next((j.id for j in dto.active_jobs if j.kind == "transcription"), None)
        background_tasks.add_task(run_transcription, request.app, video_id, job_id)
    return VideoResponse.from_dto(dto)
