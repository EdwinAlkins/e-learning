"""Traduction des exceptions métier en réponses HTTP."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from e_learning.application.shared.errors import InfrastructureError
from e_learning.domain.shared.exceptions import (
    ConflictError,
    DomainError,
    NotFoundError,
    ValidationError,
)
from e_learning.domain.user.exceptions import (
    AdminRequired,
    InactiveUser,
    InvalidCredentials,
    TooManyLoginAttempts,
)

logger = logging.getLogger("e_learning")


def _error(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": message})


def register_error_handlers(app: FastAPI) -> None:
    # 401 = pas de jeton, jeton invalide ou compte désactivé ; 403 = rôle insuffisant.
    @app.exception_handler(InvalidCredentials)
    async def _unauthorized(_: Request, exc: InvalidCredentials) -> JSONResponse:
        response = _error(status.HTTP_401_UNAUTHORIZED, str(exc))
        response.headers["WWW-Authenticate"] = "Bearer"
        return response

    @app.exception_handler(InactiveUser)
    async def _inactive(_: Request, exc: InactiveUser) -> JSONResponse:
        response = _error(status.HTTP_401_UNAUTHORIZED, str(exc))
        response.headers["WWW-Authenticate"] = "Bearer"
        return response

    @app.exception_handler(AdminRequired)
    async def _forbidden(_: Request, exc: AdminRequired) -> JSONResponse:
        return _error(status.HTTP_403_FORBIDDEN, str(exc))

    @app.exception_handler(TooManyLoginAttempts)
    async def _too_many(_: Request, exc: TooManyLoginAttempts) -> JSONResponse:
        response = _error(status.HTTP_429_TOO_MANY_REQUESTS, str(exc))
        response.headers["Retry-After"] = str(exc.retry_after_seconds)
        return response

    @app.exception_handler(NotFoundError)
    async def _not_found(_: Request, exc: NotFoundError) -> JSONResponse:
        return _error(status.HTTP_404_NOT_FOUND, str(exc))

    @app.exception_handler(ConflictError)
    async def _conflict(_: Request, exc: ConflictError) -> JSONResponse:
        return _error(status.HTTP_409_CONFLICT, str(exc))

    @app.exception_handler(ValidationError)
    async def _unprocessable(_: Request, exc: ValidationError) -> JSONResponse:
        return _error(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc))

    @app.exception_handler(DomainError)
    async def _bad_request(_: Request, exc: DomainError) -> JSONResponse:
        return _error(status.HTTP_400_BAD_REQUEST, str(exc))

    @app.exception_handler(InfrastructureError)
    async def _service_unavailable(_: Request, exc: InfrastructureError) -> JSONResponse:
        logger.error("Dépendance technique indisponible : %s", exc, exc_info=exc)
        message = str(exc).strip() or "Une dépendance technique est indisponible."
        return _error(status.HTTP_503_SERVICE_UNAVAILABLE, message)

    @app.exception_handler(RequestValidationError)
    async def _request_validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = exc.errors()
        if len(errors) == 1:
            msg = str(errors[0].get("msg", "Requête invalide"))
        else:
            msg = "; ".join(str(e.get("msg", "invalid")) for e in errors)
        return _error(status.HTTP_422_UNPROCESSABLE_CONTENT, msg)

    @app.exception_handler(IntegrityError)
    async def _integrity(_: Request, exc: IntegrityError) -> JSONResponse:
        logger.warning("Conflit d'intégrité DB : %s", exc)
        return _error(
            status.HTTP_409_CONFLICT,
            "Conflit de données (contrainte d'unicité ou référence).",
        )
