"""Use case : connexion par email et mot de passe."""

from __future__ import annotations

from e_learning.application.user.dto import AccessTokenDTO, LoginCommand
from e_learning.application.user.passwords import PASSWORD_MAX_LENGTH
from e_learning.application.user.ports import LoginThrottle, PasswordHasher, TokenService
from e_learning.domain.user.entities import User
from e_learning.domain.user.exceptions import (
    InactiveUser,
    InvalidCredentials,
    InvalidEmail,
    TooManyLoginAttempts,
)
from e_learning.domain.user.repository import UserRepository
from e_learning.domain.user.value_objects import Email


class AuthenticateUser:
    def __init__(
        self,
        users: UserRepository,
        hasher: PasswordHasher,
        tokens: TokenService,
        throttle: LoginThrottle,
    ) -> None:
        self._users = users
        self._hasher = hasher
        self._tokens = tokens
        self._throttle = throttle

    async def execute(self, command: LoginCommand) -> AccessTokenDTO:
        email_key = f"email:{command.email.strip().lower()}"
        keys = [email_key]
        if command.client_ip:
            keys.append(f"ip:{command.client_ip}")

        retry_after = await self._throttle.retry_after(keys)
        if retry_after is not None:
            raise TooManyLoginAttempts(retry_after)

        user = await self._check_credentials(command.email, command.password)
        if user is None:
            await self._throttle.record_failure(keys)
            raise InvalidCredentials()
        if not user.is_active:
            raise InactiveUser()

        await self._throttle.reset(email_key)
        issued = self._tokens.issue(str(user.id))
        return AccessTokenDTO(
            access_token=issued.access_token,
            token_type="bearer",
            expires_in=issued.expires_in,
        )

    async def _check_credentials(self, raw_email: str, password: str) -> User | None:
        if len(password) > PASSWORD_MAX_LENGTH:
            # Aucun compte ne peut avoir ce mot de passe : inutile de hacher une entrée géante.
            return None
        try:
            email: Email | None = Email(raw_email)
        except InvalidEmail:
            email = None
        user = await self._users.get_by_email(email) if email is not None else None
        # Hash factice si le compte est absent : même coût, que l'email existe ou non.
        hashed = user.hashed_password if user is not None else None
        if not await self._hasher.verify(password, hashed):
            return None
        return user
