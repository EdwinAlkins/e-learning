"""Lecture d'uploads avec plafond de taille."""

from __future__ import annotations

from fastapi import HTTPException, Request, UploadFile, status


async def read_upload_limited(
    upload: UploadFile,
    *,
    max_size: int,
    request: Request | None = None,
) -> bytes:
    """Lit un ``UploadFile`` par chunks ; lève 413 si ``max_size`` est dépassé."""
    if request is not None:
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                if int(content_length) > max_size:
                    raise HTTPException(
                        status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                        detail=f"Fichier trop volumineux (max {max_size} octets).",
                    )
            except ValueError:
                pass

    chunks: list[bytes] = []
    size = 0
    while True:
        chunk = await upload.read(1024 * 1024)
        if not chunk:
            break
        size += len(chunk)
        if size > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail=f"Fichier trop volumineux (max {max_size} octets).",
            )
        chunks.append(chunk)
    return b"".join(chunks)
