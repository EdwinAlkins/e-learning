"""Frontière transactionnelle : session liée à la requête."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from e_learning.infrastructure.messaging.deferred import DeferredJobPublisher


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Fournit une session par requête HTTP.

    Commit unique en fin de scope (succès). Les routers ne doivent **pas**
    appeler ``session.commit()``.

    Après commit, flush des publications RabbitMQ différées (``DeferredJobPublisher``)
    pour que le worker ne voie le job qu'une fois persistant.
    """
    session_factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
            deferred = getattr(request.state, "deferred_publisher", None)
            if isinstance(deferred, DeferredJobPublisher):
                await deferred.flush()
        except Exception:
            deferred = getattr(request.state, "deferred_publisher", None)
            if isinstance(deferred, DeferredJobPublisher):
                deferred.clear()
            await session.rollback()
            raise


SessionDep = Annotated[AsyncSession, Depends(get_session, scope="function")]
