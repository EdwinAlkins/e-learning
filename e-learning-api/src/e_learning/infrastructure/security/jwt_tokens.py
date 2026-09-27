"""Adaptateur TokenService — JWT HS256 via pyjwt."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt

from e_learning.application.user.ports import IssuedToken, TokenService
from e_learning.domain.user.exceptions import InvalidCredentials

_ALGORITHM = "HS256"


class JwtTokenService(TokenService):
    """Le jeton ne porte que l'identité (``sub``) : le rôle est relu en base."""

    def __init__(self, secret_key: str, *, expire_minutes: int) -> None:
        self._secret_key = secret_key
        self._expire = timedelta(minutes=expire_minutes)

    def issue(self, subject: str) -> IssuedToken:
        now = datetime.now(UTC)
        payload = {"sub": subject, "iat": now, "exp": now + self._expire}
        token = jwt.encode(payload, self._secret_key, algorithm=_ALGORITHM)
        return IssuedToken(access_token=token, expires_in=int(self._expire.total_seconds()))

    def decode(self, token: str) -> str:
        try:
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=[_ALGORITHM],
                options={"require": ["sub", "exp", "iat"]},
            )
        except jwt.InvalidTokenError as exc:
            raise InvalidCredentials("Jeton invalide ou expiré.") from exc
        subject = payload.get("sub")
        if not isinstance(subject, str):
            raise InvalidCredentials("Jeton invalide ou expiré.")
        return subject
