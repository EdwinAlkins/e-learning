"""Port de persistance du journal de consommation LLM."""

from __future__ import annotations

from abc import ABC, abstractmethod

from e_learning.domain.usage.entities import TokenUsage


class TokenUsageRepository(ABC):
    @abstractmethod
    async def add(self, usage: TokenUsage) -> None: ...
