"""Initialisations au démarrage de l'API."""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from e_learning.application.user.ports import PasswordHasher
from e_learning.application.user.use_cases.ensure_first_admin import EnsureFirstAdmin
from e_learning.infrastructure.config import Settings
from e_learning.infrastructure.persistence.user.repository import SqlAlchemyUserRepository

logger = logging.getLogger("e_learning")


async def ensure_first_admin(
    session_factory: async_sessionmaker[AsyncSession],
    hasher: PasswordHasher,
    settings: Settings,
) -> None:
    """Crée ``APP_FIRST_ADMIN_EMAIL`` s'il n'existe pas (idempotent)."""
    async with session_factory() as session:
        created = await EnsureFirstAdmin(SqlAlchemyUserRepository(session), hasher).execute(
            email=settings.first_admin_email,
            password=settings.first_admin_password.get_secret_value(),
        )
        await session.commit()
    if created:
        logger.info("Premier administrateur créé : %s", settings.first_admin_email)
