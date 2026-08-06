"""Agrégat ``User`` — racine du bounded context ``user``."""

from __future__ import annotations

from datetime import UTC, datetime

from e_learning.domain.user.value_objects import UserId


def _now() -> datetime:
    return datetime.now(UTC)


class User:
    """Utilisateur anonyme identifié par un :class:`UserId`."""

    def __init__(self, *, id: UserId, created_at: datetime) -> None:
        self.id = id
        self.created_at = created_at

    @classmethod
    def create(cls) -> User:
        return cls(id=UserId.generate(), created_at=_now())

    def __eq__(self, other: object) -> bool:
        return isinstance(other, User) and other.id == self.id

    def __hash__(self) -> int:
        return hash(self.id)
