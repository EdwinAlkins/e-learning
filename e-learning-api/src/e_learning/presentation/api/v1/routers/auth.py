"""Router auth : connexion, déconnexion, compte courant."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from e_learning.application.user.dto import ChangePasswordCommand, LoginCommand
from e_learning.application.user.use_cases.authenticate_user import AuthenticateUser
from e_learning.application.user.use_cases.change_password import ChangePassword
from e_learning.presentation.api.dependencies import get_authenticate_user, get_change_password
from e_learning.presentation.api.dependencies.auth import (
    ACCESS_TOKEN_COOKIE,
    CurrentUserDep,
    get_current_user,
)
from e_learning.presentation.api.v1.schemas.auth import (
    ChangePasswordRequest,
    MeResponse,
    TokenResponse,
)

# Seules routes publiques de l'API (avec les sondes de santé et /metrics).
router = APIRouter(prefix="/auth", tags=["auth"])
me_router = APIRouter(prefix="/auth", tags=["auth"], dependencies=[Depends(get_current_user)])

_LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


def _cookie_secure(request: Request) -> bool:
    # ``Secure`` partout sauf en développement local servi en HTTP.
    return request.url.scheme == "https" or request.url.hostname not in _LOCAL_HOSTS


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    response: Response,
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    use_case: Annotated[AuthenticateUser, Depends(get_authenticate_user)],
) -> TokenResponse:
    """OAuth2 password flow : ``username`` = email.

    Le jeton est renvoyé dans le corps (mobile, Swagger, scripts) et posé en
    cookie ``HttpOnly`` (web : lecture vidéo / document sans header).
    """
    dto = await use_case.execute(
        LoginCommand(
            email=form.username,
            password=form.password,
            client_ip=request.client.host if request.client else None,
        )
    )
    response.set_cookie(
        ACCESS_TOKEN_COOKIE,
        dto.access_token,
        max_age=dto.expires_in,
        path="/",
        secure=_cookie_secure(request),
        httponly=True,
        samesite="lax",
    )
    return TokenResponse.from_dto(dto)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response) -> None:
    """Efface le cookie de session. Public : un jeton expiré doit pouvoir se déconnecter."""
    response.delete_cookie(
        ACCESS_TOKEN_COOKIE,
        path="/",
        secure=_cookie_secure(request),
        httponly=True,
        samesite="lax",
    )


@me_router.get("/me", response_model=MeResponse)
async def me(user: CurrentUserDep) -> MeResponse:
    return MeResponse.from_dto(user)


@me_router.patch("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    payload: ChangePasswordRequest,
    user: CurrentUserDep,
    use_case: Annotated[ChangePassword, Depends(get_change_password)],
) -> None:
    await use_case.execute(
        ChangePasswordCommand(
            user_id=user.id,
            current_password=payload.current_password,
            new_password=payload.new_password,
        )
    )
