"""Value objects du bounded context ``user``."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from e_learning.domain.user.exceptions import InvalidUserId


@dataclass(frozen=True, slots=True)
class UserId:
    """Identité d'un utilisateur (UUIDv7)."""

    value: uuid.UUID

    @classmethod
    def generate(cls) -> UserId:
        return cls(uuid.uuid7())

    @classmethod
    def from_string(cls, raw: str) -> UserId:
        try:
            return cls(uuid.UUID(raw))
        except ValueError as exc:
            raise InvalidUserId(raw) from exc

    def __str__(self) -> str:
        return str(self.value)
