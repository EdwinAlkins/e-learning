"""Port de persistance des utilisateurs."""

from __future__ import annotations

import builtins
from abc import ABC, abstractmethod

from e_learning.domain.user.entities import User
from e_learning.domain.user.value_objects import Email, UserId


class UserRepository(ABC):
    @abstractmethod
    async def save(self, user: User) -> None: ...

    @abstractmethod
    async def get(self, user_id: UserId) -> User: ...

    @abstractmethod
    async def exists(self, user_id: UserId) -> bool: ...

    @abstractmethod
    async def get_by_email(self, email: Email) -> User | None: ...

    @abstractmethod
    async def list(self, *, offset: int, limit: int) -> builtins.list[User]:
        """Page d'utilisateurs, du plus ancien au plus récent."""

    @abstractmethod
    async def count(self) -> int: ...

    @abstractmethod
    async def delete(self, user_id: UserId) -> None:
        """Supprime le compte ; notes, progression et consommation suivent en cascade."""
