"""Entité ``TokenUsage`` — une ligne du journal de consommation LLM."""

from __future__ import annotations

from datetime import UTC, datetime

from e_learning.domain.usage.exceptions import InvalidTokenCount, InvalidUsageKind
from e_learning.domain.usage.value_objects import TokenUsageId
from e_learning.domain.user.value_objects import UserId


def _now() -> datetime:
    return datetime.now(UTC)


class TokenUsage:
    """Tokens consommés par un appel LLM, attribués à un utilisateur si connu.

    ``user_id`` est ``None`` pour les appels hors requête utilisateur (CLI).
    Journal append-only : l'entité n'est jamais modifiée après création.
    """

    KIND_CHAT = "chat"
    KIND_SUMMARY = "summary"

    KINDS = frozenset({KIND_CHAT, KIND_SUMMARY})

    def __init__(
        self,
        *,
        id: TokenUsageId,
        user_id: UserId | None,
        kind: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        created_at: datetime,
    ) -> None:
        if kind not in self.KINDS:
            raise InvalidUsageKind(kind)
        if prompt_tokens < 0:
            raise InvalidTokenCount("prompt_tokens", prompt_tokens)
        if completion_tokens < 0:
            raise InvalidTokenCount("completion_tokens", completion_tokens)
        self.id = id
        self.user_id = user_id
        self.kind = kind
        self.model = model
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.created_at = created_at

    @classmethod
    def record(
        cls,
        *,
        user_id: UserId | None,
        kind: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> TokenUsage:
        return cls(
            id=TokenUsageId.generate(),
            user_id=user_id,
            kind=kind,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            created_at=_now(),
        )

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def __eq__(self, other: object) -> bool:
        return isinstance(other, TokenUsage) and other.id == self.id

    def __hash__(self) -> int:
        return hash(self.id)
