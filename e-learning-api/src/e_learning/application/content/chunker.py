"""Découpage de texte pour indexation RAG."""

from __future__ import annotations

import uuid

_RAG_NAMESPACE = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")


def chunk_point_id(
    owner_id: str,
    source: str,
    chunk_index: int,
    *,
    kind: str = "video",
) -> str:
    """Identifiant stable (UUID5) pour upsert idempotent dans le store vectoriel.

    - ``kind="video"`` : clé historique ``{video_id}:{source}:{index}``
    - ``kind="document"`` : clé ``doc:{document_id}:{source}:{index}``
    """
    if kind == "document":
        key = f"doc:{owner_id}:{source}:{chunk_index}"
    else:
        key = f"{owner_id}:{source}:{chunk_index}"
    return str(uuid.uuid5(_RAG_NAMESPACE, key))


def chunk_text(text: str, *, chunk_size: int, overlap: int) -> list[str]:
    """Découpe ``text`` en segments de ``chunk_size`` caractères avec ``overlap``.

    Les blancs de tête/fin sont normalisés ; les segments vides sont ignorés.
    """
    cleaned = " ".join(text.split())
    if not cleaned:
        return []
    if chunk_size <= 0:
        raise ValueError("chunk_size doit être > 0")
    if overlap < 0:
        raise ValueError("overlap doit être >= 0")
    if overlap >= chunk_size:
        raise ValueError("overlap doit être < chunk_size")

    if len(cleaned) <= chunk_size:
        return [cleaned]

    chunks: list[str] = []
    start = 0
    step = chunk_size - overlap
    while start < len(cleaned):
        end = min(start + chunk_size, len(cleaned))
        piece = cleaned[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(cleaned):
            break
        start += step
    return chunks
