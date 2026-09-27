"""Agrégat ``User`` — racine du bounded context ``user``."""

from __future__ import annotations

from datetime import UTC, datetime

from e_learning.domain.user.value_objects import Email, UserId


def _now() -> datetime:
    return datetime.now(UTC)


class User:
    """Compte authentifié par email et mot de passe.

    Le domaine ne manipule que le hash : le mot de passe en clair et
    l'algorithme de hachage restent dans la couche application / infrastructure.
    """

    def __init__(
        self,
        *,
        id: UserId,
        email: Email,
        hashed_password: str,
        full_name: str | None,
        is_admin: bool,
        is_active: bool,
        created_at: datetime,
    ) -> None:
        self.id = id
        self.email = email
        self.hashed_password = hashed_password
        self.full_name = full_name
        self.is_admin = is_admin
        self.is_active = is_active
        self.created_at = created_at

    @classmethod
    def create(
        cls,
        *,
        email: Email,
        hashed_password: str,
        full_name: str | None = None,
        is_admin: bool = False,
    ) -> User:
        return cls(
            id=UserId.generate(),
            email=email,
            hashed_password=hashed_password,
            full_name=_clean_name(full_name),
            is_admin=is_admin,
            is_active=True,
            created_at=_now(),
        )

    def rename(self, full_name: str | None) -> None:
        self.full_name = _clean_name(full_name)

    def change_password(self, hashed_password: str) -> None:
        self.hashed_password = hashed_password

    def set_admin(self, is_admin: bool) -> None:
        self.is_admin = is_admin

    def set_active(self, is_active: bool) -> None:
        self.is_active = is_active

    def __eq__(self, other: object) -> bool:
        return isinstance(other, User) and other.id == self.id

    def __hash__(self) -> int:
        return hash(self.id)


def _clean_name(full_name: str | None) -> str | None:
    if full_name is None:
        return None
    return full_name.strip() or None
