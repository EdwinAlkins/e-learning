"""Extraction de l'utilisateur authentifié depuis la requête."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status

from e_learning.domain.user.exceptions import InvalidUserId, UserNotFound
from e_learning.domain.user.value_objects import UserId
from e_learning.presentation.api.dependencies.repositories import UserRepositoryDep

DEBUG_USER_ID = "00000000-0000-7000-8000-000000000001"


async def get_current_user_id(
    request: Request,
    users: UserRepositoryDep,
    x_user_uid: Annotated[str | None, Header(alias="X-User-UID")] = None,
) -> str:
    """Résout l'UID utilisateur (header, sinon fallback DEBUG).

    Le fallback debug ne persiste **pas** d'utilisateur en base : créer via
    ``POST /auth/generate`` (ou seed) avant d'appeler des routes protégées.
    """
    settings = request.app.state.settings
    raw = x_user_uid
    if raw is None and settings.debug:
        raw = DEBUG_USER_ID
    if raw is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Header X-User-UID requis.")
    try:
        user_id = UserId.from_string(raw)
    except InvalidUserId as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    if not await users.exists(user_id):
        raise UserNotFound(str(user_id))
    return str(user_id)


CurrentUserIdDep = Annotated[str, Depends(get_current_user_id)]
