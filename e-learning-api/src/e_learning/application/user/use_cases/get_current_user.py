"""Use case : résoudre l'utilisateur porteur d'un jeton."""

from __future__ import annotations

from e_learning.application.user.dto import UserDTO
from e_learning.application.user.ports import TokenService
from e_learning.domain.user.exceptions import (
    InactiveUser,
    InvalidCredentials,
    InvalidUserId,
    UserNotFound,
)
from e_learning.domain.user.repository import UserRepository
from e_learning.domain.user.value_objects import UserId


class GetCurrentUser:
    """Relit le compte en base à chaque appel : un retrait de droits ou une
    désactivation s'applique sans attendre l'expiration du jeton."""

    def __init__(self, users: UserRepository, tokens: TokenService) -> None:
        self._users = users
        self._tokens = tokens

    async def execute(self, token: str) -> UserDTO:
        subject = self._tokens.decode(token)
        try:
            user = await self._users.get(UserId.from_string(subject))
        except (InvalidUserId, UserNotFound) as exc:
            raise InvalidCredentials("Jeton invalide.") from exc
        if not user.is_active:
            raise InactiveUser()
        return UserDTO.from_entity(user)
