"""Câblage use cases — user."""

from __future__ import annotations

from e_learning.application.user.use_cases.generate_user import GenerateUser
from e_learning.application.user.use_cases.restore_user import RestoreUser
from e_learning.presentation.api.dependencies.repositories import UserRepositoryDep


def get_generate_user(users: UserRepositoryDep) -> GenerateUser:
    return GenerateUser(users)


def get_restore_user(users: UserRepositoryDep) -> RestoreUser:
    return RestoreUser(users)
