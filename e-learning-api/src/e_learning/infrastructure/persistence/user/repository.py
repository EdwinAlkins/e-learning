"""Adaptateur SQLAlchemy — UserRepository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from e_learning.domain.user.entities import User
from e_learning.domain.user.exceptions import UserNotFound
from e_learning.domain.user.repository import UserRepository
from e_learning.domain.user.value_objects import UserId
from e_learning.infrastructure.persistence.user import mappers
from e_learning.infrastructure.persistence.user.models import UserModel


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, user: User) -> None:
        existing = await self._session.get(UserModel, user.id.value)
        if existing is None:
            self._session.add(mappers.to_model(user))
        else:
            mappers.apply_to_model(existing, user)

    async def get(self, user_id: UserId) -> User:
        model = await self._session.get(UserModel, user_id.value)
        if model is None:
            raise UserNotFound(str(user_id))
        return mappers.to_domain(model)

    async def exists(self, user_id: UserId) -> bool:
        stmt = select(UserModel.id).where(UserModel.id == user_id.value).limit(1)
        result = await self._session.execute(stmt)
        return result.first() is not None
