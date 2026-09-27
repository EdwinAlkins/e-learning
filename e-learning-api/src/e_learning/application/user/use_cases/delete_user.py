"""Use case : supprimer un compte (admin), avec ses notes et sa progression."""

from __future__ import annotations

from e_learning.domain.user.exceptions import SelfLockout, UserNotFound
from e_learning.domain.user.repository import UserRepository
from e_learning.domain.user.value_objects import UserId


class DeleteUser:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def execute(self, *, actor_id: str, user_id: str) -> None:
        target = UserId.from_string(user_id)
        if str(target) == actor_id:
            raise SelfLockout("supprimer")
        if not await self._users.exists(target):
            raise UserNotFound(str(target))
        await self._users.delete(target)
