"""Tests — authentification et gestion des comptes (use cases, fakes)."""

from __future__ import annotations

import pytest

from e_learning.application.user.dto import (
    ChangePasswordCommand,
    CreateUserCommand,
    LoginCommand,
    UpdateUserCommand,
)
from e_learning.application.user.use_cases.authenticate_user import AuthenticateUser
from e_learning.application.user.use_cases.change_password import ChangePassword
from e_learning.application.user.use_cases.create_user import CreateUser
from e_learning.application.user.use_cases.delete_user import DeleteUser
from e_learning.application.user.use_cases.ensure_first_admin import EnsureFirstAdmin
from e_learning.application.user.use_cases.get_current_user import GetCurrentUser
from e_learning.application.user.use_cases.list_users import ListUsers
from e_learning.application.user.use_cases.update_user import UpdateUser
from e_learning.domain.user.exceptions import (
    EmailAlreadyUsed,
    InactiveUser,
    IncorrectPassword,
    InvalidCredentials,
    InvalidEmail,
    InvalidPassword,
    SelfLockout,
    TooManyLoginAttempts,
    UserNotFound,
)
from e_learning.domain.user.value_objects import Email, UserId
from tests.unit.application._fakes import (
    FakeLoginThrottle,
    FakePasswordHasher,
    FakeTokenService,
    FakeUserRepository,
    make_user,
)

PASSWORD = "secret-password"


@pytest.fixture
def users() -> FakeUserRepository:
    return FakeUserRepository()


@pytest.fixture
def hasher() -> FakePasswordHasher:
    return FakePasswordHasher()


@pytest.fixture
def throttle() -> FakeLoginThrottle:
    return FakeLoginThrottle()


def _authenticate(
    users: FakeUserRepository, hasher: FakePasswordHasher, throttle: FakeLoginThrottle
) -> AuthenticateUser:
    return AuthenticateUser(users, hasher, FakeTokenService(), throttle)


# --- AuthenticateUser ---------------------------------------------------------


async def test_login_returns_bearer_token(users, hasher, throttle) -> None:
    user = make_user("ada@example.com", password=PASSWORD)
    await users.save(user)

    dto = await _authenticate(users, hasher, throttle).execute(
        LoginCommand(email="  ADA@example.com ", password=PASSWORD, client_ip="10.0.0.1")
    )

    assert dto.access_token == f"token:{user.id}"
    assert dto.token_type == "bearer"
    assert dto.expires_in == 3600


async def test_login_wrong_password_and_unknown_email_fail_identically(
    users, hasher, throttle
) -> None:
    await users.save(make_user("ada@example.com", password=PASSWORD))
    use_case = _authenticate(users, hasher, throttle)

    with pytest.raises(InvalidCredentials) as wrong_password:
        await use_case.execute(LoginCommand(email="ada@example.com", password="nope-nope"))
    with pytest.raises(InvalidCredentials) as unknown_email:
        await use_case.execute(LoginCommand(email="bob@example.com", password=PASSWORD))

    assert str(wrong_password.value) == str(unknown_email.value)


async def test_login_unknown_email_still_verifies_a_dummy_hash(users, hasher, throttle) -> None:
    use_case = _authenticate(users, hasher, throttle)

    for email in ("ghost@example.com", "not-an-email"):
        with pytest.raises(InvalidCredentials):
            await use_case.execute(LoginCommand(email=email, password=PASSWORD))

    # S3 : un hash (factice) est vérifié même quand le compte n'existe pas.
    assert hasher.verify_calls == [None, None]


async def test_login_rejects_inactive_account(users, hasher, throttle) -> None:
    user = make_user(password=PASSWORD)
    user.set_active(False)
    await users.save(user)

    with pytest.raises(InactiveUser):
        await _authenticate(users, hasher, throttle).execute(
            LoginCommand(email=str(user.email), password=PASSWORD)
        )


async def test_login_is_throttled_per_email_and_ip(users, hasher, throttle) -> None:
    await users.save(make_user("ada@example.com", password=PASSWORD))
    use_case = _authenticate(users, hasher, throttle)

    for _ in range(5):
        with pytest.raises(InvalidCredentials):
            await use_case.execute(
                LoginCommand(email="ada@example.com", password="bad-pass", client_ip="1.2.3.4")
            )

    # Bloqué par email, même avec le bon mot de passe et depuis une autre IP.
    with pytest.raises(TooManyLoginAttempts):
        await use_case.execute(
            LoginCommand(email="ada@example.com", password=PASSWORD, client_ip="5.6.7.8")
        )
    # Bloqué par IP, même pour un autre email.
    with pytest.raises(TooManyLoginAttempts):
        await use_case.execute(
            LoginCommand(email="bob@example.com", password=PASSWORD, client_ip="1.2.3.4")
        )


async def test_login_success_resets_email_counter(users, hasher, throttle) -> None:
    await users.save(make_user("ada@example.com", password=PASSWORD))
    use_case = _authenticate(users, hasher, throttle)
    for _ in range(4):
        with pytest.raises(InvalidCredentials):
            await use_case.execute(LoginCommand(email="ada@example.com", password="bad-pass"))

    await use_case.execute(LoginCommand(email="ada@example.com", password=PASSWORD))

    assert "email:ada@example.com" not in throttle.failures


async def test_login_rejects_oversized_password_without_hashing(users, hasher, throttle) -> None:
    await users.save(make_user("ada@example.com", password=PASSWORD))

    with pytest.raises(InvalidCredentials):
        await _authenticate(users, hasher, throttle).execute(
            LoginCommand(email="ada@example.com", password="x" * 10_000)
        )
    assert hasher.verify_calls == []


# --- GetCurrentUser -----------------------------------------------------------


async def test_current_user_is_reloaded_from_repository(users) -> None:
    user = make_user(is_admin=True)
    await users.save(user)
    use_case = GetCurrentUser(users, FakeTokenService())

    assert (await use_case.execute(f"token:{user.id}")).is_admin is True

    # Rétrogradé après émission du jeton : effet immédiat.
    user.set_admin(False)
    assert (await use_case.execute(f"token:{user.id}")).is_admin is False


@pytest.mark.parametrize("token", ["garbage", "token:not-a-uuid", f"token:{UserId.generate()}"])
async def test_current_user_rejects_bad_tokens(users, token: str) -> None:
    with pytest.raises(InvalidCredentials):
        await GetCurrentUser(users, FakeTokenService()).execute(token)


async def test_current_user_rejects_deactivated_account(users) -> None:
    user = make_user()
    await users.save(user)
    user.set_active(False)

    with pytest.raises(InactiveUser):
        await GetCurrentUser(users, FakeTokenService()).execute(f"token:{user.id}")


# --- CreateUser / ListUsers ---------------------------------------------------


async def test_create_user_hashes_password_and_normalizes_email(users, hasher) -> None:
    dto = await CreateUser(users, hasher).execute(
        CreateUserCommand(email="Ada@Example.com", password=PASSWORD, full_name="Ada")
    )

    stored = await users.get(UserId.from_string(dto.id))
    assert dto.email == "ada@example.com"
    assert stored.hashed_password == f"hashed:{PASSWORD}"
    assert not hasattr(dto, "hashed_password")
    assert dto.is_admin is False


async def test_create_user_rejects_duplicate_email(users, hasher) -> None:
    await users.save(make_user("ada@example.com"))

    with pytest.raises(EmailAlreadyUsed):
        await CreateUser(users, hasher).execute(
            CreateUserCommand(email="ADA@example.com", password=PASSWORD)
        )


@pytest.mark.parametrize("password", ["short", "x" * 129])
async def test_create_user_enforces_password_length(users, hasher, password: str) -> None:
    with pytest.raises(InvalidPassword):
        await CreateUser(users, hasher).execute(
            CreateUserCommand(email="ada@example.com", password=password)
        )


async def test_create_user_rejects_invalid_email(users, hasher) -> None:
    with pytest.raises(InvalidEmail):
        await CreateUser(users, hasher).execute(CreateUserCommand(email="ada", password=PASSWORD))


async def test_list_users_is_paginated(users) -> None:
    for i in range(5):
        await users.save(make_user(f"user{i}@example.com"))

    page = await ListUsers(users).execute(offset=2, limit=2)

    assert page.total == 5
    assert len(page.items) == 2


# --- UpdateUser / DeleteUser --------------------------------------------------


async def test_update_user_changes_role_status_name_and_password(users, hasher) -> None:
    admin = make_user("admin@example.com", is_admin=True)
    target = make_user("ada@example.com")
    await users.save(admin)
    await users.save(target)

    dto = await UpdateUser(users, hasher).execute(
        UpdateUserCommand(
            actor_id=str(admin.id),
            user_id=str(target.id),
            full_name="Ada L.",
            update_full_name=True,
            is_admin=True,
            is_active=False,
            password="new-password",
        )
    )

    assert (dto.full_name, dto.is_admin, dto.is_active) == ("Ada L.", True, False)
    assert target.hashed_password == "hashed:new-password"


async def test_update_user_keeps_unset_fields(users, hasher) -> None:
    admin = make_user("admin@example.com", is_admin=True)
    target = make_user("ada@example.com")
    target.rename("Ada")
    await users.save(admin)
    await users.save(target)

    dto = await UpdateUser(users, hasher).execute(
        UpdateUserCommand(actor_id=str(admin.id), user_id=str(target.id), is_admin=True)
    )

    assert dto.full_name == "Ada"
    assert dto.is_active is True


@pytest.mark.parametrize(
    "changes", [{"is_admin": False}, {"is_active": False}], ids=["demote", "deactivate"]
)
async def test_admin_cannot_lock_themselves_out(users, hasher, changes: dict[str, bool]) -> None:
    admin = make_user("admin@example.com", is_admin=True)
    await users.save(admin)

    with pytest.raises(SelfLockout):
        await UpdateUser(users, hasher).execute(
            UpdateUserCommand(actor_id=str(admin.id), user_id=str(admin.id), **changes)
        )
    assert admin.is_admin and admin.is_active


async def test_admin_can_rename_themselves(users, hasher) -> None:
    admin = make_user("admin@example.com", is_admin=True)
    await users.save(admin)

    dto = await UpdateUser(users, hasher).execute(
        UpdateUserCommand(
            actor_id=str(admin.id),
            user_id=str(admin.id),
            full_name="Root",
            update_full_name=True,
            is_admin=True,
        )
    )
    assert dto.full_name == "Root"


async def test_delete_user(users) -> None:
    admin = make_user("admin@example.com", is_admin=True)
    target = make_user("ada@example.com")
    await users.save(admin)
    await users.save(target)

    await DeleteUser(users).execute(actor_id=str(admin.id), user_id=str(target.id))

    assert not await users.exists(target.id)


async def test_admin_cannot_delete_themselves(users) -> None:
    admin = make_user("admin@example.com", is_admin=True)
    await users.save(admin)

    with pytest.raises(SelfLockout):
        await DeleteUser(users).execute(actor_id=str(admin.id), user_id=str(admin.id))


async def test_delete_unknown_user(users) -> None:
    with pytest.raises(UserNotFound):
        await DeleteUser(users).execute(
            actor_id=str(UserId.generate()), user_id=str(UserId.generate())
        )


# --- ChangePassword -----------------------------------------------------------


async def test_change_password(users, hasher) -> None:
    user = make_user(password=PASSWORD)
    await users.save(user)

    await ChangePassword(users, hasher).execute(
        ChangePasswordCommand(
            user_id=str(user.id), current_password=PASSWORD, new_password="brand-new-pass"
        )
    )

    assert user.hashed_password == "hashed:brand-new-pass"


async def test_change_password_requires_current_password(users, hasher) -> None:
    user = make_user(password=PASSWORD)
    await users.save(user)

    with pytest.raises(IncorrectPassword):
        await ChangePassword(users, hasher).execute(
            ChangePasswordCommand(
                user_id=str(user.id), current_password="wrong-pass", new_password="brand-new"
            )
        )


async def test_change_password_enforces_policy(users, hasher) -> None:
    user = make_user(password=PASSWORD)
    await users.save(user)

    with pytest.raises(InvalidPassword):
        await ChangePassword(users, hasher).execute(
            ChangePasswordCommand(user_id=str(user.id), current_password=PASSWORD, new_password="x")
        )


# --- EnsureFirstAdmin ---------------------------------------------------------


async def test_ensure_first_admin_is_idempotent(users, hasher) -> None:
    use_case = EnsureFirstAdmin(users, hasher)

    assert await use_case.execute(email="Admin@Example.com", password=PASSWORD) is True
    assert await use_case.execute(email="admin@example.com", password="other-password") is False

    admin = await users.get_by_email(Email("admin@example.com"))
    assert admin is not None
    assert admin.is_admin is True
    # Un redémarrage ne réécrit pas le mot de passe.
    assert admin.hashed_password == f"hashed:{PASSWORD}"
    assert await users.count() == 1
