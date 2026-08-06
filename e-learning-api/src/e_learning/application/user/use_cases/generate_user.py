"""Use case : générer un utilisateur anonyme."""

from __future__ import annotations

from e_learning.application.user.dto import UserDTO
from e_learning.domain.user.entities import User
from e_learning.domain.user.repository import UserRepository


class GenerateUser:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def execute(self) -> UserDTO:
        user = User.create()
        await self._users.save(user)
        return UserDTO.from_entity(user)
