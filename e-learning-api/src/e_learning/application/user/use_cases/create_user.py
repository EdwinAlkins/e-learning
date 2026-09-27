"""Use case : créer un compte (admin)."""

from __future__ import annotations

from e_learning.application.user.dto import CreateUserCommand, UserDTO
from e_learning.application.user.passwords import check_password_policy
from e_learning.application.user.ports import PasswordHasher
from e_learning.domain.user.entities import User
from e_learning.domain.user.exceptions import EmailAlreadyUsed
from e_learning.domain.user.repository import UserRepository
from e_learning.domain.user.value_objects import Email


class CreateUser:
    def __init__(self, users: UserRepository, hasher: PasswordHasher) -> None:
        self._users = users
        self._hasher = hasher

    async def execute(self, command: CreateUserCommand) -> UserDTO:
        email = Email(command.email)
        check_password_policy(command.password)
        if await self._users.get_by_email(email) is not None:
            raise EmailAlreadyUsed(str(email))
        user = User.create(
            email=email,
            hashed_password=await self._hasher.hash(command.password),
            full_name=command.full_name,
            is_admin=command.is_admin,
        )
        await self._users.save(user)
        return UserDTO.from_entity(user)
