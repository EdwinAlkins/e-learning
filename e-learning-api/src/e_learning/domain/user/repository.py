"""Port de persistance des utilisateurs."""

from __future__ import annotations

from abc import ABC, abstractmethod

from e_learning.domain.user.entities import User
from e_learning.domain.user.value_objects import UserId


class UserRepository(ABC):
    @abstractmethod
    async def save(self, user: User) -> None: ...

    @abstractmethod
    async def get(self, user_id: UserId) -> User: ...

    @abstractmethod
    async def exists(self, user_id: UserId) -> bool: ...
