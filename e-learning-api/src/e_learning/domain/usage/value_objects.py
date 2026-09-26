"""Value objects du bounded context ``usage``."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from e_learning.domain.usage.exceptions import InvalidTokenUsageId


@dataclass(frozen=True, slots=True)
class TokenUsageId:
    """Identité d'une entrée du journal de consommation (UUIDv7)."""

    value: uuid.UUID

    @classmethod
    def generate(cls) -> TokenUsageId:
        return cls(uuid.uuid7())

    @classmethod
    def from_string(cls, raw: str) -> TokenUsageId:
        try:
            return cls(uuid.UUID(raw))
        except ValueError as exc:
            raise InvalidTokenUsageId(raw) from exc

    def __str__(self) -> str:
        return str(self.value)
