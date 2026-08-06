"""Use case : restaurer / vérifier un utilisateur existant."""

from __future__ import annotations

from e_learning.application.user.dto import UserDTO
from e_learning.domain.user.repository import UserRepository
from e_learning.domain.user.value_objects import UserId


class RestoreUser:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def execute(self, user_id: str) -> UserDTO:
        user = await self._users.get(UserId.from_string(user_id))
        return UserDTO.from_entity(user)
