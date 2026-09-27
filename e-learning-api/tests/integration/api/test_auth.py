"""Tests d'intégration — connexion, session, comptes, cloisonnement."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
import pytest
from httpx import AsyncClient
from sqlalchemy import text

from e_learning.domain.user.value_objects import Email
from e_learning.infrastructure.persistence.user.repository import SqlAlchemyUserRepository
from e_learning.presentation.api.bootstrap import ensure_first_admin
from tests.integration.api.test_access_matrix import seed_catalog
from tests.integration.conftest import (
    PASSWORD,
    TEST_SECRET_KEY,
    bearer,
    create_account,
    login,
)


async def test_health_is_public(client: AsyncClient) -> None:
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "health ok"


# --- Connexion ----------------------------------------------------------------


async def test_login_returns_token_and_sets_httponly_cookie(app: Any, client: AsyncClient) -> None:
    email = await create_account(app)

    response = await client.post("/auth/login", data={"username": email, "password": PASSWORD})

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == app.state.settings.access_token_expire_minutes * 60
    cookie = response.headers["set-cookie"].lower()
    assert cookie.startswith("access_token=")
    assert "httponly" in cookie
    assert "samesite=lax" in cookie
    assert "secure" in cookie
    assert f"max-age={body['expires_in']}" in cookie


async def test_login_failure_does_not_reveal_which_field_is_wrong(
    app: Any, client: AsyncClient
) -> None:
    email = await create_account(app)

    wrong_password = await client.post(
        "/auth/login", data={"username": email, "password": "wrong-password"}
    )
    unknown_email = await client.post(
        "/auth/login", data={"username": "nobody@example.com", "password": PASSWORD}
    )

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()


async def test_login_is_rate_limited(app: Any, client: AsyncClient) -> None:
    email = await create_account(app)
    for _ in range(5):
        response = await client.post(
            "/auth/login", data={"username": email, "password": "bad!bad!"}
        )
        assert response.status_code == 401

    blocked = await client.post("/auth/login", data={"username": email, "password": PASSWORD})

    assert blocked.status_code == 429
    assert int(blocked.headers["Retry-After"]) > 0


async def test_me_and_logout(app: Any, client: AsyncClient) -> None:
    email = await create_account(app)
    token = await login(client, email)

    me = await client.get("/auth/me", headers=bearer(token))
    assert me.status_code == 200
    assert me.json() == {
        "id": me.json()["id"],
        "email": email,
        "full_name": None,
        "is_admin": False,
    }

    logout = await client.post("/auth/logout")
    assert logout.status_code == 204
    assert 'access_token=""' in logout.headers["set-cookie"]


async def test_change_password(app: Any, client: AsyncClient) -> None:
    email = await create_account(app)
    token = await login(client, email)

    wrong = await client.patch(
        "/auth/me/password",
        json={"current_password": "not-the-one", "new_password": "another-password"},
        headers=bearer(token),
    )
    assert wrong.status_code == 400  # pas 401 : le client ne doit pas déconnecter

    ok = await client.patch(
        "/auth/me/password",
        json={"current_password": PASSWORD, "new_password": "another-password"},
        headers=bearer(token),
    )
    assert ok.status_code == 204
    await login(client, email, "another-password")


# --- Jetons -------------------------------------------------------------------


def _token(user_id: str, *, secret: str = TEST_SECRET_KEY, delta: timedelta) -> str:
    now = datetime.now(UTC)
    return jwt.encode({"sub": user_id, "iat": now, "exp": now + delta}, secret, algorithm="HS256")


async def test_invalid_tokens_are_rejected(client: AsyncClient, learner_token: str) -> None:
    user_id = (await client.get("/auth/me", headers=bearer(learner_token))).json()["id"]
    for token in (
        _token(user_id, delta=timedelta(seconds=-1)),
        _token(user_id, secret="another-secret-key-another-secret-key", delta=timedelta(hours=1)),
        "not-a-jwt",
    ):
        response = await client.get("/formations", headers=bearer(token))
        assert response.status_code == 401, token


async def test_deactivated_account_loses_access_immediately(
    client: AsyncClient, admin_token: str, learner_token: str
) -> None:
    learner_id = (await client.get("/auth/me", headers=bearer(learner_token))).json()["id"]

    patch = await client.patch(
        f"/admin/users/{learner_id}", json={"is_active": False}, headers=bearer(admin_token)
    )
    assert patch.status_code == 200

    assert (await client.get("/formations", headers=bearer(learner_token))).status_code == 401


async def test_demoted_admin_loses_studio_immediately(
    app: Any, client: AsyncClient, admin_token: str
) -> None:
    other_admin_token = await login(client, await create_account(app, is_admin=True))
    other_id = (await client.get("/auth/me", headers=bearer(other_admin_token))).json()["id"]
    assert (await client.get("/admin/users", headers=bearer(other_admin_token))).status_code == 200

    await client.patch(
        f"/admin/users/{other_id}", json={"is_admin": False}, headers=bearer(admin_token)
    )

    assert (await client.get("/admin/users", headers=bearer(other_admin_token))).status_code == 403
    assert (await client.get("/formations", headers=bearer(other_admin_token))).status_code == 200


# --- Cookie (web) -------------------------------------------------------------


async def test_cookie_authenticates_reads_and_requires_csrf_header_on_writes(
    client: AsyncClient, admin_token: str
) -> None:
    cookie = {"Cookie": f"access_token={admin_token}"}

    assert (await client.get("/auth/me", headers=cookie)).status_code == 200

    forged = await client.post("/formations", json={"name": "CSRF"}, headers=cookie)
    assert forged.status_code == 403

    legit = await client.post(
        "/formations",
        json={"name": f"Cookie {admin_token[-6:]}"},
        headers={**cookie, "X-Requested-With": "XMLHttpRequest"},
    )
    assert legit.status_code == 201, legit.text


@pytest.mark.parametrize("transport", ["bearer", "cookie"])
async def test_video_range_streaming(
    app: Any, client: AsyncClient, learner_token: str, transport: str
) -> None:
    catalog = await seed_catalog(app)
    auth = (
        bearer(learner_token)
        if transport == "bearer"
        else {"Cookie": f"access_token={learner_token}"}
    )

    for start, end in ((0, 99), (100, 199), (4000, 4095)):
        response = await client.get(
            f"/videos/{catalog.video_id}/stream",
            headers={**auth, "Range": f"bytes={start}-{end}"},
        )
        assert response.status_code == 206
        assert response.content == catalog.video_bytes[start : end + 1]


# --- Premier admin ------------------------------------------------------------


async def test_first_admin_is_created_once(app: Any, client: AsyncClient) -> None:
    settings = app.state.settings
    await ensure_first_admin(app.state.session_factory, app.state.password_hasher, settings)
    await ensure_first_admin(app.state.session_factory, app.state.password_hasher, settings)

    async with app.state.session_factory() as session:
        admin = await SqlAlchemyUserRepository(session).get_by_email(
            Email(settings.first_admin_email)
        )
    assert admin is not None
    assert admin.is_admin

    token = await login(
        client, settings.first_admin_email, settings.first_admin_password.get_secret_value()
    )
    listing = await client.get("/admin/users", params={"limit": 200}, headers=bearer(token))
    emails = [u["email"] for u in listing.json()["items"]]
    assert emails.count(settings.first_admin_email) == 1


# --- Gestion des comptes ------------------------------------------------------


async def test_admin_user_crud(client: AsyncClient, admin_token: str) -> None:
    headers = bearer(admin_token)
    email = f"crud-{admin_token[-8:]}@example.com".lower()

    created = await client.post(
        "/admin/users",
        json={"email": email.upper(), "password": PASSWORD, "full_name": "Ada"},
        headers=headers,
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["email"] == email
    assert "password" not in body and "hashed_password" not in body

    duplicate = await client.post(
        "/admin/users", json={"email": email, "password": PASSWORD}, headers=headers
    )
    assert duplicate.status_code == 409

    short = await client.post(
        "/admin/users", json={"email": "x" + email, "password": "short"}, headers=headers
    )
    assert short.status_code == 422

    listing = await client.get("/admin/users", params={"limit": 1}, headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()["items"]) == 1
    assert listing.json()["total"] >= 2

    patched = await client.patch(
        f"/admin/users/{body['id']}",
        json={"full_name": None, "is_admin": True},
        headers=headers,
    )
    assert patched.json()["full_name"] is None
    assert patched.json()["is_admin"] is True

    assert (await client.delete(f"/admin/users/{body['id']}", headers=headers)).status_code == 204
    assert (await client.delete(f"/admin/users/{body['id']}", headers=headers)).status_code == 404


async def test_admin_cannot_lock_themselves_out(client: AsyncClient, admin_token: str) -> None:
    headers = bearer(admin_token)
    me = (await client.get("/auth/me", headers=headers)).json()["id"]

    for payload in ({"is_admin": False}, {"is_active": False}):
        response = await client.patch(f"/admin/users/{me}", json=payload, headers=headers)
        assert response.status_code == 409, payload
    assert (await client.delete(f"/admin/users/{me}", headers=headers)).status_code == 409
    assert (await client.get("/admin/users", headers=headers)).status_code == 200


async def test_deleting_a_user_removes_their_notes_and_progress(
    app: Any, client: AsyncClient, admin_token: str, learner_token: str
) -> None:
    catalog = await seed_catalog(app)
    learner = bearer(learner_token)
    learner_id = (await client.get("/auth/me", headers=learner)).json()["id"]
    await client.post(
        f"/notes/{catalog.video_id}", json={"timecode": 1.0, "content": "x"}, headers=learner
    )
    await client.post(f"/progress/{catalog.video_id}", json={"last_position": 2.0}, headers=learner)

    deleted = await client.delete(f"/admin/users/{learner_id}", headers=bearer(admin_token))
    assert deleted.status_code == 204

    async with app.state.engine.connect() as conn:
        for table in ("notes", "progress"):
            count = await conn.scalar(
                text(f"SELECT count(*) FROM {table} WHERE user_id = :uid"), {"uid": learner_id}
            )
            assert count == 0, table


# --- Cloisonnement des données (S9) -------------------------------------------


async def test_notes_and_progress_are_isolated_per_user(
    app: Any, client: AsyncClient, learner_token: str, admin_token: str
) -> None:
    catalog = await seed_catalog(app)
    v = catalog.video_id
    alice = bearer(learner_token)
    bob = bearer(await login(client, await create_account(app)))
    admin = bearer(admin_token)

    note = await client.post(f"/notes/{v}", json={"timecode": 1.0, "content": "A"}, headers=alice)
    note_id = note.json()["id"]
    await client.post(f"/progress/{v}", json={"last_position": 42.0}, headers=alice)

    for other in (bob, admin):
        assert (await client.get(f"/notes/{v}", headers=other)).json() == []
        assert (await client.get(f"/progress/{v}", headers=other)).json()["last_position"] == 0
        edit = await client.put(f"/notes/{note_id}", json={"content": "B"}, headers=other)
        assert edit.status_code in (403, 404)
        delete = await client.delete(f"/notes/{note_id}", headers=other)
        assert delete.status_code in (403, 404)

    notes = (await client.get(f"/notes/{v}", headers=alice)).json()
    assert [n["content"] for n in notes] == ["A"]
