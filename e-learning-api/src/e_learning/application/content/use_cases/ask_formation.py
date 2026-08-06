"""Use case : poser une question RAG scoped à une formation."""

from __future__ import annotations

from e_learning.application.content.dto import (
    AskFormationCommand,
    AskFormationResult,
    RagCitationDTO,
)
from e_learning.application.shared.errors import RagEmptyIndexError
from e_learning.application.shared.rag import ChatPort, EmbeddingPort, VectorStorePort
from e_learning.domain.catalog.repository import FormationRepository
from e_learning.domain.catalog.value_objects import FormationId


class AskFormation:
    def __init__(
        self,
        formations: FormationRepository,
        embeddings: EmbeddingPort,
        vectors: VectorStorePort,
        chat: ChatPort,
        *,
        top_k: int,
    ) -> None:
        self._formations = formations
        self._embeddings = embeddings
        self._vectors = vectors
        self._chat = chat
        self._top_k = top_k

    async def execute(self, command: AskFormationCommand) -> AskFormationResult:
        question = command.question.strip()
        if not question:
            raise RagEmptyIndexError("La question ne peut pas être vide.")

        formation = await self._formations.get(FormationId.from_string(command.formation_id))
        formation_id = str(formation.id)

        count = await self._vectors.count_by_formation(formation_id)
        if count == 0:
            raise RagEmptyIndexError(
                "Aucun contenu indexé pour cette formation. "
                "Transcrivez des vidéos puis lancez l'indexation RAG."
            )

        [query_vector] = await self._embeddings.embed([question])
        hits = await self._vectors.search(formation_id, query_vector, top_k=self._top_k)
        if not hits:
            raise RagEmptyIndexError(
                "Aucun passage pertinent trouvé. Réindexez la formation ou reformulez."
            )

        context_parts: list[str] = []
        citations: list[RagCitationDTO] = []
        seen_keys: set[tuple[str, str]] = set()
        for hit in hits:
            context_parts.append(f"[{hit.title} — {hit.source}]\n{hit.text}")
            key = (hit.video_id, hit.source)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            excerpt = hit.text if len(hit.text) <= 240 else hit.text[:237] + "…"
            citations.append(
                RagCitationDTO(
                    video_id=hit.video_id,
                    title=hit.title,
                    source=hit.source,
                    excerpt=excerpt,
                )
            )

        answer = await self._chat.answer(
            question=question,
            context="\n\n---\n\n".join(context_parts),
        )
        return AskFormationResult(answer=answer, citations=citations)
