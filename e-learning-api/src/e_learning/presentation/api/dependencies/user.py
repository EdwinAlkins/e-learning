"""Câblage use cases — user."""

from __future__ import annotations

from fastapi import Request

from e_learning.application.user.ports import LoginThrottle, PasswordHasher, TokenService
from e_learning.application.user.use_cases.authenticate_user import AuthenticateUser
from e_learning.application.user.use_cases.change_password import ChangePassword
from e_learning.application.user.use_cases.create_user import CreateUser
from e_learning.application.user.use_cases.delete_user import DeleteUser
from e_learning.application.user.use_cases.get_current_user import GetCurrentUser
from e_learning.application.user.use_cases.list_users import ListUsers
from e_learning.application.user.use_cases.update_user import UpdateUser
from e_learning.presentation.api.dependencies.repositories import UserRepositoryDep


def _hasher(request: Request) -> PasswordHasher:
    hasher: PasswordHasher = request.app.state.password_hasher
    return hasher


def _tokens(request: Request) -> TokenService:
    tokens: TokenService = request.app.state.token_service
    return tokens


def _throttle(request: Request) -> LoginThrottle:
    throttle: LoginThrottle = request.app.state.login_throttle
    return throttle


def get_authenticate_user(request: Request, users: UserRepositoryDep) -> AuthenticateUser:
    return AuthenticateUser(users, _hasher(request), _tokens(request), _throttle(request))


def get_get_current_user(request: Request, users: UserRepositoryDep) -> GetCurrentUser:
    return GetCurrentUser(users, _tokens(request))


def get_create_user(request: Request, users: UserRepositoryDep) -> CreateUser:
    return CreateUser(users, _hasher(request))


def get_update_user(request: Request, users: UserRepositoryDep) -> UpdateUser:
    return UpdateUser(users, _hasher(request))


def get_delete_user(users: UserRepositoryDep) -> DeleteUser:
    return DeleteUser(users)


def get_list_users(users: UserRepositoryDep) -> ListUsers:
    return ListUsers(users)


def get_change_password(request: Request, users: UserRepositoryDep) -> ChangePassword:
    return ChangePassword(users, _hasher(request))
