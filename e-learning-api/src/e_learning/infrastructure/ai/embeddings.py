"""Adaptateur embeddings OpenAI-compatible."""

from __future__ import annotations

from e_learning.application.shared.errors import RagError
from e_learning.application.shared.rag import EmbeddingPort
from e_learning.infrastructure.config import Settings


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

        client = AsyncOpenAI(
            base_url=self._settings.openai_base_url,
            api_key=self._settings.openai_api_key.get_secret_value(),
        )
        try:
            response = await client.embeddings.create(
                model=self._settings.embedding_model,
                input=texts,
            )
        except Exception as exc:  # noqa: BLE001
            raise RagError(
                f"Échec embeddings ({self._settings.embedding_model} "
                f"via {self._settings.openai_base_url}) : {exc}. "
                "Vérifiez que le serveur d'embeddings écoute "
                "(LM Studio / Ollama) et que APP_OPENAI_BASE_URL est joignable "
                "depuis le conteneur api."
            ) from exc

        by_index = {item.index: item.embedding for item in response.data}
        vectors: list[list[float]] = []
        for i in range(len(texts)):
            vector = by_index.get(i)
            if vector is None:
                raise RagError(f"Embedding manquant pour l'index {i}.")
            if len(vector) != self._settings.embedding_dims:
                raise RagError(
                    f"Dimension embedding {len(vector)} "
                    f"≠ APP_EMBEDDING_DIMS={self._settings.embedding_dims}."
                )
            vectors.append(list(vector))
        return vectors
