"""Mappers user domaine ↔ ORM."""

from __future__ import annotations

from e_learning.domain.user.entities import User
from e_learning.domain.user.value_objects import UserId
from e_learning.infrastructure.persistence.converters import as_utc
from e_learning.infrastructure.persistence.user.models import UserModel


def to_model(user: User) -> UserModel:
    return UserModel(id=user.id.value, created_at=user.created_at)


def apply_to_model(model: UserModel, user: User) -> None:
    # created_at immutable
    return None


def to_domain(model: UserModel) -> User:
    return User(id=UserId(model.id), created_at=as_utc(model.created_at))
