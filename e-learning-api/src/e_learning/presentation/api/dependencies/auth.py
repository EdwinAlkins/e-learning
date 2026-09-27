"""Authentification des requêtes : jeton Bearer (mobile, Swagger) ou cookie (web)."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

from e_learning.application.user.dto import UserDTO
from e_learning.application.user.use_cases.get_current_user import GetCurrentUser
from e_learning.domain.user.exceptions import AdminRequired, InvalidCredentials
from e_learning.presentation.api.dependencies.user import get_get_current_user

ACCESS_TOKEN_COOKIE = "access_token"
# Anti-CSRF pour le cookie : un header personnalisé impose un preflight CORS,
# que seules les origines de ``APP_CORS_ORIGINS`` passent. Un formulaire ou un
# lien forgé sur un autre site ne peut pas l'ajouter.
CSRF_HEADER = "X-Requested-With"
_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


async def get_current_user(
    request: Request,
    use_case: Annotated[GetCurrentUser, Depends(get_get_current_user)],
    bearer: Annotated[str | None, Depends(oauth2_scheme)],
) -> UserDTO:
    """Utilisateur actif porteur du jeton, relu en base (une requête SQL)."""
    token = bearer
    if token is None:
        token = request.cookies.get(ACCESS_TOKEN_COOKIE)
        if token and request.method not in _SAFE_METHODS and CSRF_HEADER not in request.headers:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail=f"Header {CSRF_HEADER} requis avec l'authentification par cookie.",
            )
    if not token:
        raise InvalidCredentials("Authentification requise.")
    return await use_case.execute(token)


CurrentUserDep = Annotated[UserDTO, Depends(get_current_user)]


async def require_admin(user: CurrentUserDep) -> UserDTO:
    if not user.is_admin:
        raise AdminRequired()
    return user


AdminDep = Annotated[UserDTO, Depends(require_admin)]
