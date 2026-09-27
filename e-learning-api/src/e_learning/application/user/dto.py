"""DTO / commands — contexte ``user``."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from e_learning.domain.user.entities import User


@dataclass(frozen=True, slots=True)
class UserDTO:
    """Vue d'un compte. Ne transporte jamais le hash du mot de passe."""

    id: str
    email: str
    full_name: str | None
    is_admin: bool
    is_active: bool
    created_at: datetime

    @classmethod
    def from_entity(cls, user: User) -> UserDTO:
        return cls(
            id=str(user.id),
            email=str(user.email),
            full_name=user.full_name,
            is_admin=user.is_admin,
            is_active=user.is_active,
            created_at=user.created_at,
        )


@dataclass(frozen=True, slots=True)
class UserPageDTO:
    items: list[UserDTO]
    total: int


@dataclass(frozen=True, slots=True)
class AccessTokenDTO:
    access_token: str
    token_type: str
    expires_in: int


@dataclass(frozen=True, slots=True)
class LoginCommand:
    email: str
    password: str
    client_ip: str | None = None


@dataclass(frozen=True, slots=True)
class CreateUserCommand:
    email: str
    password: str
    full_name: str | None = None
    is_admin: bool = False


@dataclass(frozen=True, slots=True)
class UpdateUserCommand:
    """Modification par un admin. ``None`` = champ inchangé.

    ``full_name`` suit ``update_full_name`` pour distinguer « effacer » de « ne pas toucher ».
    """

    actor_id: str
    user_id: str
    full_name: str | None = None
    update_full_name: bool = False
    is_admin: bool | None = None
    is_active: bool | None = None
    password: str | None = None


@dataclass(frozen=True, slots=True)
class ChangePasswordCommand:
    user_id: str
    current_password: str
    new_password: str
