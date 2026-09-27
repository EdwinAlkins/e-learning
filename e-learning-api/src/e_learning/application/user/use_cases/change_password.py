"""Use case : l'utilisateur connecté change son propre mot de passe."""

from __future__ import annotations

from e_learning.application.user.dto import ChangePasswordCommand
from e_learning.application.user.passwords import check_password_policy
from e_learning.application.user.ports import PasswordHasher
from e_learning.domain.user.exceptions import IncorrectPassword
from e_learning.domain.user.repository import UserRepository
from e_learning.domain.user.value_objects import UserId


class ChangePassword:
    def __init__(self, users: UserRepository, hasher: PasswordHasher) -> None:
        self._users = users
        self._hasher = hasher

    async def execute(self, command: ChangePasswordCommand) -> None:
        user = await self._users.get(UserId.from_string(command.user_id))
        if not await self._hasher.verify(command.current_password, user.hashed_password):
            raise IncorrectPassword()
        check_password_policy(command.new_password)
        user.change_password(await self._hasher.hash(command.new_password))
        await self._users.save(user)
