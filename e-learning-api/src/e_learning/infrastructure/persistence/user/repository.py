"""Adaptateur SQLAlchemy — UserRepository."""

from __future__ import annotations

import builtins

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from e_learning.domain.user.entities import User
from e_learning.domain.user.exceptions import UserNotFound
from e_learning.domain.user.repository import UserRepository
from e_learning.domain.user.value_objects import Email, UserId
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

    async def get_by_email(self, email: Email) -> User | None:
        stmt = select(UserModel).where(UserModel.email == str(email))
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return mappers.to_domain(model) if model is not None else None

    async def list(self, *, offset: int, limit: int) -> builtins.list[User]:
        stmt = (
            select(UserModel)
            .order_by(UserModel.created_at, UserModel.id)
            .offset(offset)
            .limit(limit)
        )
        models = (await self._session.execute(stmt)).scalars().all()
        return [mappers.to_domain(m) for m in models]

    async def count(self) -> int:
        result = await self._session.execute(select(func.count()).select_from(UserModel))
        return int(result.scalar_one())

    async def delete(self, user_id: UserId) -> None:
        # Suppression SQL directe : les FK ``ON DELETE CASCADE`` emportent notes,
        # progression et consommation ; ``jobs.user_id`` passe à NULL.
        await self._session.execute(delete(UserModel).where(UserModel.id == user_id.value))
