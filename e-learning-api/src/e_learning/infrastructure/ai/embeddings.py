"""Adaptateurs embeddings : API OpenAI-compatible ou sentence-transformers local."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from e_learning.application.shared.errors import RagError
from e_learning.application.shared.rag import EmbeddingPort
from e_learning.infrastructure.config import Settings

logger = logging.getLogger("e_learning")


class OpenAIEmbeddingAdapter(EmbeddingPort):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            raise RagError("Le paquet openai n'est pas installé (groupe de deps ai).") from exc

        base_url = self._settings.resolved_embedding_base_url()
        client = AsyncOpenAI(
            base_url=base_url,
            api_key=self._settings.resolved_embedding_api_key(),
        )
        try:
            response = await client.embeddings.create(
                model=self._settings.embedding_model,
                input=texts,
            )
        except Exception as exc:  # noqa: BLE001
            raise RagError(
                f"Échec embeddings ({self._settings.embedding_model} via {base_url}) : {exc}. "
                "Vérifiez que le serveur d'embeddings écoute "
                "(LM Studio / Ollama) et que APP_EMBEDDING_BASE_URL est joignable."
            ) from exc

        by_index = {item.index: item.embedding for item in response.data}
        vectors: list[list[float]] = []
        for i in range(len(texts)):
            vector = by_index.get(i)
            if vector is None:
                raise RagError(f"Embedding manquant pour l'index {i}.")
            vectors.append(_validate_dims(vector, self._settings.embedding_dims))
        return vectors


class SentenceTransformersEmbeddingAdapter(EmbeddingPort):
    """Embeddings locaux via sentence-transformers (pas d'API distante)."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._model: Any | None = None

    def _load_model(self) -> Any:
        if self._model is not None:
            return self._model
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RagError(
                "Le paquet sentence-transformers n'est pas installé (groupe de deps ai)."
            ) from exc
        model_name = self._settings.embedding_model
        logger.info("Chargement du modèle embeddings local : %s", model_name)
        try:
            self._model = SentenceTransformer(model_name)
        except Exception as exc:  # noqa: BLE001
            raise RagError(
                f"Impossible de charger le modèle sentence-transformers « {model_name} » : {exc}."
            ) from exc
        logger.info("Modèle embeddings local prêt : %s", model_name)
        return self._model

    async def warmup(self) -> None:
        """Télécharge (si absent du cache) et charge le modèle en mémoire."""
        await asyncio.to_thread(self._load_model)

    def _encode_sync(self, texts: list[str]) -> list[list[float]]:
        model = self._load_model()
        encoded = model.encode(texts, normalize_embeddings=True)
        return [list(vector) for vector in encoded]

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            raw_vectors = await asyncio.to_thread(self._encode_sync, texts)
        except RagError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise RagError(
                f"Échec embeddings locaux ({self._settings.embedding_model}) : {exc}."
            ) from exc
        return [_validate_dims(vector, self._settings.embedding_dims) for vector in raw_vectors]


def build_embedding_adapter(settings: Settings) -> EmbeddingPort:
    """API distante si ``APP_EMBEDDING_BASE_URL`` est défini, sinon sentence-transformers."""
    if settings.use_local_embeddings():
        logger.info(
            "Embeddings locaux (sentence-transformers) — modèle=%s dims=%s",
            settings.embedding_model,
            settings.embedding_dims,
        )
        return SentenceTransformersEmbeddingAdapter(settings)
    logger.info(
        "Embeddings distants — %s (%s)",
        settings.resolved_embedding_base_url(),
        settings.embedding_model,
    )
    return OpenAIEmbeddingAdapter(settings)


def _validate_dims(vector: list[float], expected: int) -> list[float]:
    if len(vector) != expected:
        raise RagError(f"Dimension embedding {len(vector)} ≠ APP_EMBEDDING_DIMS={expected}.")
    return vector
