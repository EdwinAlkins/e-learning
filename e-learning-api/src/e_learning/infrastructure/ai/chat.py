"""Adaptateur chat OpenAI-compatible pour réponses RAG."""

from __future__ import annotations

from e_learning.application.shared.errors import RagError
from e_learning.application.shared.rag import ChatPort
from e_learning.infrastructure.config import Settings


class OpenAIChatAdapter(ChatPort):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def answer(self, *, question: str, context: str) -> str:
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            raise RagError("Le paquet openai n'est pas installé (groupe de deps ai).") from exc

        client = AsyncOpenAI(
            base_url=self._settings.openai_base_url,
            api_key=self._settings.openai_api_key.get_secret_value(),
        )
        system = (
            "Tu es un assistant pédagogique pour une formation e-learning. "
            "Réponds uniquement à partir du contexte fourni. "
            "Si le contexte ne permet pas de répondre, dis-le clairement. "
            "Cite les titres de vidéos pertinents. Réponds en français, "
            "de façon concise et structurée."
        )
        user = f"Contexte :\n{context}\n\nQuestion :\n{question}"
        try:
            response = await client.chat.completions.create(
                model=self._settings.openai_model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            if not response.choices:
                raise RagError("Réponse LLM vide.")
            content = response.choices[0].message.content
            if not content:
                raise RagError("Réponse LLM vide.")
            return content.strip()
        except RagError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise RagError(f"Échec génération réponse : {exc}") from exc
