"""Adaptateur Qdrant pour le store vectoriel RAG."""

from __future__ import annotations

import contextlib
import logging
from typing import Any

from e_learning.application.shared.errors import RagError
from e_learning.application.shared.rag import RagChunk, RagHit, VectorStorePort
from e_learning.infrastructure.config import Settings

logger = logging.getLogger("e_learning")


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _collection_vector_size(info: Any) -> int | None:
    """Lit la taille des vecteurs d'une collection (API qdrant-client variable)."""
    params = getattr(info, "config", None)
    params = getattr(params, "params", None) if params is not None else None
    vectors = getattr(params, "vectors", None) if params is not None else None
    if vectors is None:
        return None
    size = getattr(vectors, "size", None)
    if size is not None:
        return int(size)
    if isinstance(vectors, dict):
        for cfg in vectors.values():
            nested = getattr(cfg, "size", None)
            if nested is not None:
                return int(nested)
            if isinstance(cfg, dict) and "size" in cfg:
                return int(cfg["size"])
    return None


class QdrantVectorStore(VectorStorePort):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: Any | None = None

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        try:
            from qdrant_client import AsyncQdrantClient
        except ImportError as exc:
            raise RagError(
                "Le paquet qdrant-client n'est pas installé (groupe de deps ai)."
            ) from exc
        self._client = AsyncQdrantClient(
            url=self._settings.qdrant_url,
            check_compatibility=False,
        )
        return self._client

    async def ensure_collection(self) -> None:
        from qdrant_client.http import models as qm

        client = self._get_client()
        name = self._settings.qdrant_collection
        expected_dims = self._settings.embedding_dims
        try:
            exists = await client.collection_exists(name)
            if exists:
                info = await client.get_collection(name)
                current_dims = _collection_vector_size(info)
                if current_dims is not None and current_dims != expected_dims:
                    logger.warning(
                        "Collection Qdrant %s : dims %s ≠ APP_EMBEDDING_DIMS=%s — "
                        "recréation (réindexer le corpus RAG).",
                        name,
                        current_dims,
                        expected_dims,
                    )
                    await client.delete_collection(name)
                    exists = False
            if not exists:
                await client.create_collection(
                    collection_name=name,
                    vectors_config=qm.VectorParams(
                        size=expected_dims,
                        distance=qm.Distance.COSINE,
                    ),
                )
                logger.info(
                    "Collection Qdrant créée : %s (dims=%s)",
                    name,
                    expected_dims,
                )
            for field_name in ("formation_id", "video_id", "document_id"):
                with contextlib.suppress(Exception):
                    # Index déjà présent sur collection existante
                    await client.create_payload_index(
                        collection_name=name,
                        field_name=field_name,
                        field_schema=qm.PayloadSchemaType.KEYWORD,
                    )
        except RagError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise RagError(f"Échec ensure_collection Qdrant : {exc}") from exc

    async def upsert_chunks(self, chunks: list[RagChunk]) -> None:
        if not chunks:
            return
        from qdrant_client.http import models as qm

        await self.ensure_collection()
        client = self._get_client()
        points = [
            qm.PointStruct(
                id=chunk.id,
                vector=chunk.vector,
                payload={
                    "formation_id": chunk.formation_id,
                    "chapter_id": chunk.chapter_id,
                    "video_id": chunk.video_id,
                    "document_id": chunk.document_id,
                    "title": chunk.title,
                    "source": chunk.source,
                    "chunk_index": chunk.chunk_index,
                    "text": chunk.text,
                },
            )
            for chunk in chunks
        ]
        try:
            await client.upsert(
                collection_name=self._settings.qdrant_collection,
                points=points,
            )
        except Exception as exc:  # noqa: BLE001
            raise RagError(f"Échec upsert Qdrant : {exc}") from exc

    async def delete_by_video(self, video_id: str) -> None:
        await self._delete_by_keyword("video_id", video_id)

    async def delete_by_document(self, document_id: str) -> None:
        await self._delete_by_keyword("document_id", document_id)

    async def _delete_by_keyword(self, field: str, value: str) -> None:
        from qdrant_client.http import models as qm

        await self.ensure_collection()
        client = self._get_client()
        try:
            await client.delete(
                collection_name=self._settings.qdrant_collection,
                points_selector=qm.FilterSelector(
                    filter=qm.Filter(
                        must=[
                            qm.FieldCondition(
                                key=field,
                                match=qm.MatchValue(value=value),
                            )
                        ]
                    )
                ),
            )
        except Exception as exc:  # noqa: BLE001
            raise RagError(f"Échec delete Qdrant ({field}) : {exc}") from exc

    async def search(self, formation_id: str, vector: list[float], *, top_k: int) -> list[RagHit]:
        from qdrant_client.http import models as qm

        await self.ensure_collection()
        client = self._get_client()
        try:
            response = await client.query_points(
                collection_name=self._settings.qdrant_collection,
                query=vector,
                limit=top_k,
                query_filter=qm.Filter(
                    must=[
                        qm.FieldCondition(
                            key="formation_id",
                            match=qm.MatchValue(value=formation_id),
                        )
                    ]
                ),
                with_payload=True,
            )
        except Exception as exc:  # noqa: BLE001
            raise RagError(f"Échec search Qdrant : {exc}") from exc

        hits: list[RagHit] = []
        for point in response.points:
            payload = point.payload or {}
            hits.append(
                RagHit(
                    formation_id=str(payload.get("formation_id", "")),
                    chapter_id=str(payload.get("chapter_id", "")),
                    title=str(payload.get("title", "")),
                    source=str(payload.get("source", "")),
                    chunk_index=int(payload.get("chunk_index", 0)),
                    text=str(payload.get("text", "")),
                    score=float(point.score or 0.0),
                    video_id=_optional_str(payload.get("video_id")),
                    document_id=_optional_str(payload.get("document_id")),
                )
            )
        return hits

    async def count_by_formation(self, formation_id: str) -> int:
        from qdrant_client.http import models as qm

        await self.ensure_collection()
        client = self._get_client()
        try:
            result = await client.count(
                collection_name=self._settings.qdrant_collection,
                count_filter=qm.Filter(
                    must=[
                        qm.FieldCondition(
                            key="formation_id",
                            match=qm.MatchValue(value=formation_id),
                        )
                    ]
                ),
                exact=True,
            )
            return int(result.count)
        except Exception as exc:  # noqa: BLE001
            raise RagError(f"Échec count Qdrant : {exc}") from exc
