"""Mappers user domaine ↔ ORM."""

from __future__ import annotations

from e_learning.domain.user.entities import User
from e_learning.domain.user.value_objects import Email, UserId
from e_learning.infrastructure.persistence.converters import as_utc
from e_learning.infrastructure.persistence.user.models import UserModel


def to_model(user: User) -> UserModel:
    return UserModel(
        id=user.id.value,
        email=str(user.email),
        hashed_password=user.hashed_password,
        full_name=user.full_name,
        is_admin=user.is_admin,
        is_active=user.is_active,
        created_at=user.created_at,
    )


def apply_to_model(model: UserModel, user: User) -> None:
    # id, email et created_at immuables
    model.hashed_password = user.hashed_password
    model.full_name = user.full_name
    model.is_admin = user.is_admin
    model.is_active = user.is_active


def to_domain(model: UserModel) -> User:
    return User(
        id=UserId(model.id),
        email=Email(model.email),
        hashed_password=model.hashed_password,
        full_name=model.full_name,
        is_admin=model.is_admin,
        is_active=model.is_active,
        created_at=as_utc(model.created_at),
    )
