"""Router gestion des comptes (admin)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from e_learning.application.user.dto import CreateUserCommand, UpdateUserCommand
from e_learning.application.user.use_cases.create_user import CreateUser
from e_learning.application.user.use_cases.delete_user import DeleteUser
from e_learning.application.user.use_cases.list_users import ListUsers
from e_learning.application.user.use_cases.update_user import UpdateUser
from e_learning.presentation.api.dependencies import (
    get_create_user,
    get_delete_user,
    get_list_users,
    get_update_user,
)
from e_learning.presentation.api.dependencies.auth import AdminDep, require_admin
from e_learning.presentation.api.v1.schemas.auth import (
    UserCreateRequest,
    UserListResponse,
    UserResponse,
    UserUpdateRequest,
)

router = APIRouter(
    prefix="/admin/users",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
)


@router.get("", response_model=UserListResponse)
async def list_users(
    use_case: Annotated[ListUsers, Depends(get_list_users)],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> UserListResponse:
    return UserListResponse.from_dto(await use_case.execute(offset=offset, limit=limit))


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreateRequest,
    use_case: Annotated[CreateUser, Depends(get_create_user)],
) -> UserResponse:
    dto = await use_case.execute(
        CreateUserCommand(
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
            is_admin=payload.is_admin,
        )
    )
    return UserResponse.from_dto(dto)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    payload: UserUpdateRequest,
    admin: AdminDep,
    use_case: Annotated[UpdateUser, Depends(get_update_user)],
) -> UserResponse:
    dto = await use_case.execute(
        UpdateUserCommand(
            actor_id=admin.id,
            user_id=user_id,
            full_name=payload.full_name,
            update_full_name="full_name" in payload.model_fields_set,
            is_admin=payload.is_admin,
            is_active=payload.is_active,
            password=payload.password,
        )
    )
    return UserResponse.from_dto(dto)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    admin: AdminDep,
    use_case: Annotated[DeleteUser, Depends(get_delete_user)],
) -> None:
    await use_case.execute(actor_id=admin.id, user_id=user_id)
