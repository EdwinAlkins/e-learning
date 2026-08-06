"""Helpers partagés par les commandes CLI."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from e_learning.infrastructure.config import get_settings
from e_learning.infrastructure.persistence.database import create_engine, create_session_factory


@asynccontextmanager
async def transactional_session() -> AsyncIterator[AsyncSession]:
    """Frontière transactionnelle alignée sur l'API (commit / rollback)."""
    settings = get_settings()
    engine = create_engine(settings.database_url, echo=settings.echo_sql)
    session_factory = create_session_factory(engine)
    try:
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    finally:
        await engine.dispose()
