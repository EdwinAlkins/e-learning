"""DTO / commands — contexte ``user``."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from e_learning.domain.user.entities import User


@dataclass(frozen=True, slots=True)
class UserDTO:
    id: str
    created_at: datetime

    @classmethod
    def from_entity(cls, user: User) -> UserDTO:
        return cls(id=str(user.id), created_at=user.created_at)
