"""Use case : modifier un compte (admin)."""

from __future__ import annotations

from e_learning.application.user.dto import UpdateUserCommand, UserDTO
from e_learning.application.user.passwords import check_password_policy
from e_learning.application.user.ports import PasswordHasher
from e_learning.domain.user.exceptions import SelfLockout
from e_learning.domain.user.repository import UserRepository
from e_learning.domain.user.value_objects import UserId


class UpdateUser:
    def __init__(self, users: UserRepository, hasher: PasswordHasher) -> None:
        self._users = users
        self._hasher = hasher

    async def execute(self, command: UpdateUserCommand) -> UserDTO:
        user = await self._users.get(UserId.from_string(command.user_id))
        is_self = str(user.id) == command.actor_id
        # Garde-fou : on ne peut pas perdre le dernier admin en se sabordant soi-même.
        if is_self and command.is_admin is False:
            raise SelfLockout("retirer le rôle admin de")
        if is_self and command.is_active is False:
            raise SelfLockout("désactiver")

        if command.password is not None:
            check_password_policy(command.password)
            user.change_password(await self._hasher.hash(command.password))
        if command.update_full_name:
            user.rename(command.full_name)
        if command.is_admin is not None:
            user.set_admin(command.is_admin)
        if command.is_active is not None:
            user.set_active(command.is_active)

        await self._users.save(user)
        return UserDTO.from_entity(user)
