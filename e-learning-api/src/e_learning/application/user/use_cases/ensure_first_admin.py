"""Use case : créer le premier admin depuis la configuration (idempotent)."""

from __future__ import annotations

from e_learning.application.user.dto import CreateUserCommand
from e_learning.application.user.ports import PasswordHasher
from e_learning.application.user.use_cases.create_user import CreateUser
from e_learning.domain.user.repository import UserRepository
from e_learning.domain.user.value_objects import Email


class EnsureFirstAdmin:
    """Ne recrée rien et ne touche pas au mot de passe si le compte existe déjà."""

    def __init__(self, users: UserRepository, hasher: PasswordHasher) -> None:
        self._users = users
        self._hasher = hasher

    async def execute(self, *, email: str, password: str) -> bool:
        """Renvoie ``True`` si le compte a été créé."""
        if await self._users.get_by_email(Email(email)) is not None:
            return False
        await CreateUser(self._users, self._hasher).execute(
            CreateUserCommand(email=email, password=password, is_admin=True)
        )
        return True
