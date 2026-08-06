"""Frontière transactionnelle : session liée à la requête."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Fournit une session par requête HTTP.

    Commit unique en fin de scope (succès). Les routers ne doivent **pas**
    appeler ``session.commit()``.

    **``scope="function"`` est obligatoire** avec les BackgroundTasks : le scope
    ``request`` (défaut) ferme le yield *après* l'envoi de la réponse et donc
    *après* les tâches de fond. La session requête, encore dirty avec
    ``processing``, recommitterait alors par-dessus le ``ready`` du job → UI
    coincée en « Génération… » jusqu'au restart (recover stuck).

    Avec ``function``, le commit a lieu dès la fin du path operation, **avant**
    les BackgroundTasks, qui ouvrent leur propre session.
    """
    session_factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


SessionDep = Annotated[AsyncSession, Depends(get_session, scope="function")]
