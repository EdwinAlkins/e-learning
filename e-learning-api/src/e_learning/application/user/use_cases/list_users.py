"""Use case : lister les comptes (admin), paginé."""

from __future__ import annotations

from e_learning.application.user.dto import UserDTO, UserPageDTO
from e_learning.domain.user.repository import UserRepository


class ListUsers:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def execute(self, *, offset: int, limit: int) -> UserPageDTO:
        users = await self._users.list(offset=offset, limit=limit)
        return UserPageDTO(
            items=[UserDTO.from_entity(u) for u in users],
            total=await self._users.count(),
        )
