"""Tests — adaptateurs de sécurité (JWT, argon2, anti-bruteforce)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
import pytest

from e_learning.domain.user.exceptions import InvalidCredentials
from e_learning.infrastructure.security.jwt_tokens import JwtTokenService
from e_learning.infrastructure.security.login_throttle import InMemoryLoginThrottle
from e_learning.infrastructure.security.password_hasher import Argon2PasswordHasher

SECRET = "s" * 32


def test_jwt_roundtrip_carries_only_identity() -> None:
    service = JwtTokenService(SECRET, expire_minutes=10)
    issued = service.issue("user-1")

    payload = jwt.decode(issued.access_token, SECRET, algorithms=["HS256"])
    assert set(payload) == {"sub", "iat", "exp"}
    assert service.decode(issued.access_token) == "user-1"
    assert issued.expires_in == 600


def _forge(secret: str, **overrides: object) -> str:
    now = datetime.now(UTC)
    payload: dict[str, object] = {"sub": "user-1", "iat": now, "exp": now + timedelta(minutes=5)}
    payload.update(overrides)
    return jwt.encode(payload, secret, algorithm="HS256")


@pytest.mark.parametrize(
    "token",
    [
        _forge(SECRET, exp=datetime.now(UTC) - timedelta(seconds=1)),
        _forge("another-secret-another-secret-xx"),
        "not.a.jwt",
        jwt.encode({"sub": "user-1"}, SECRET, algorithm="HS256"),
        jwt.encode(
            {"sub": "user-1", "iat": datetime.now(UTC), "exp": datetime.now(UTC)},
            SECRET * 2,
            algorithm="HS512",
        ),
    ],
    ids=["expired", "wrong-key", "malformed", "missing-claims", "wrong-alg"],
)
def test_jwt_rejects_invalid_tokens(token: str) -> None:
    with pytest.raises(InvalidCredentials):
        JwtTokenService(SECRET, expire_minutes=10).decode(token)


async def test_argon2_hash_and_verify() -> None:
    hasher = Argon2PasswordHasher()
    hashed = await hasher.hash("secret-password")

    assert hashed.startswith("$argon2")
    assert "secret-password" not in hashed
    assert await hasher.verify("secret-password", hashed) is True
    assert await hasher.verify("wrong-password", hashed) is False
    assert await hasher.verify("secret-password", None) is False


async def test_throttle_blocks_after_max_failures_then_expires() -> None:
    now = [1000.0]
    throttle = InMemoryLoginThrottle(max_failures=3, window_seconds=60, clock=lambda: now[0])

    for _ in range(3):
        assert await throttle.retry_after(["email:a"]) is None
        await throttle.record_failure(["email:a", "ip:1"])

    assert await throttle.retry_after(["email:a"]) == 61
    assert await throttle.retry_after(["email:b", "ip:1"]) is not None
    assert await throttle.retry_after(["email:b", "ip:2"]) is None

    now[0] += 60
    assert await throttle.retry_after(["email:a"]) is None


async def test_throttle_reset_clears_key() -> None:
    throttle = InMemoryLoginThrottle(max_failures=1, window_seconds=60)
    await throttle.record_failure(["email:a"])
    assert await throttle.retry_after(["email:a"]) is not None

    await throttle.reset("email:a")
    assert await throttle.retry_after(["email:a"]) is None
