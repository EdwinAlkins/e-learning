"""Adaptateur SQLAlchemy — TokenUsageRepository."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from e_learning.domain.usage.entities import TokenUsage
from e_learning.domain.usage.repository import TokenUsageRepository
from e_learning.infrastructure.persistence.usage.models import TokenUsageModel


class SqlAlchemyTokenUsageRepository(TokenUsageRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, usage: TokenUsage) -> None:
        self._session.add(
            TokenUsageModel(
                id=usage.id.value,
                user_id=usage.user_id.value if usage.user_id else None,
                kind=usage.kind,
                model=usage.model,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                created_at=usage.created_at,
            )
        )
