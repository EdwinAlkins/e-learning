"""Helper : journaliser la consommation d'un appel LLM."""

from __future__ import annotations

from e_learning.application.shared.llm import LlmUsage
from e_learning.domain.usage.entities import TokenUsage
from e_learning.domain.usage.repository import TokenUsageRepository
from e_learning.domain.user.value_objects import UserId


async def record_llm_usage(
    repository: TokenUsageRepository,
    *,
    usage: LlmUsage | None,
    kind: str,
    user_id: str | None,
) -> None:
    """No-op si le fournisseur n'a pas remonté de consommation."""
    if usage is None:
        return
    await repository.add(
        TokenUsage.record(
            user_id=UserId.from_string(user_id) if user_id else None,
            kind=kind,
            model=usage.model,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
        )
    )
