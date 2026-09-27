"""Schémas Pydantic — authentification et gestion des comptes."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from e_learning.application.user.dto import AccessTokenDTO, UserDTO, UserPageDTO
from e_learning.application.user.passwords import PASSWORD_MAX_LENGTH, PASSWORD_MIN_LENGTH


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

    @classmethod
    def from_dto(cls, dto: AccessTokenDTO) -> TokenResponse:
        return cls(
            access_token=dto.access_token,
            token_type=dto.token_type,
            expires_in=dto.expires_in,
        )


class MeResponse(BaseModel):
    id: str
    email: str
    full_name: str | None
    is_admin: bool

    @classmethod
    def from_dto(cls, dto: UserDTO) -> MeResponse:
        return cls(id=dto.id, email=dto.email, full_name=dto.full_name, is_admin=dto.is_admin)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(max_length=PASSWORD_MAX_LENGTH)
    new_password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str | None
    is_admin: bool
    is_active: bool
    created_at: datetime

    @classmethod
    def from_dto(cls, dto: UserDTO) -> UserResponse:
        return cls(
            id=dto.id,
            email=dto.email,
            full_name=dto.full_name,
            is_admin=dto.is_admin,
            is_active=dto.is_active,
            created_at=dto.created_at,
        )


class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int

    @classmethod
    def from_dto(cls, dto: UserPageDTO) -> UserListResponse:
        return cls(items=[UserResponse.from_dto(u) for u in dto.items], total=dto.total)


class UserCreateRequest(BaseModel):
    email: str = Field(max_length=320)
    password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)
    full_name: str | None = Field(default=None, max_length=255)
    is_admin: bool = False


class UserUpdateRequest(BaseModel):
    """Champs absents = inchangés. ``full_name: null`` efface le nom."""

    full_name: str | None = Field(default=None, max_length=255)
    is_admin: bool | None = None
    is_active: bool | None = None
    password: str | None = Field(
        default=None, min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH
    )
