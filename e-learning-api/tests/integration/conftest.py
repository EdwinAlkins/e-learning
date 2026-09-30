"""Fixtures integration (Postgres testcontainers)."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from testcontainers.community.postgres import PostgresContainer

from e_learning.application.user.dto import CreateUserCommand
from e_learning.application.user.use_cases.create_user import CreateUser
from e_learning.infrastructure.config import Settings
from e_learning.infrastructure.persistence.database import (
    init_db,
)
from e_learning.infrastructure.persistence.user.repository import SqlAlchemyUserRepository
from e_learning.presentation.api.app import create_app

PASSWORD = "secret-password"
TEST_SECRET_KEY = "integration-tests-secret-key-0123456789"


@pytest.fixture(scope="session")
def postgres_url() -> Iterator[str]:
    with PostgresContainer("postgres:17-alpine") as postgres:
        # asyncpg URL
        url = postgres.get_connection_url().replace("psycopg2", "asyncpg")
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        yield url


@pytest.fixture
async def app(postgres_url: str, tmp_path: Path) -> AsyncIterator:
    settings = Settings(
        database_url=SecretStr(postgres_url),
        videos_path=tmp_path / "videos",
        init_db=True,
        debug=False,
        cors_origins=["http://localhost:3000"],
        secret_key=SecretStr(TEST_SECRET_KEY),
        first_admin_email=f"root-{uuid4().hex[:8]}@example.com",
        first_admin_password=SecretStr("first-admin-password"),
    )
    settings.videos_path.mkdir(parents=True, exist_ok=True)
    application = create_app(settings)
    engine = application.state.engine
    await init_db(engine)
    yield application
    await engine.dispose()


@pytest.fixture
async def client(app) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def create_account(app: Any, *, is_admin: bool = False, password: str = PASSWORD) -> str:
    """Crée un compte (email unique : la base est partagée entre les tests)."""
    email = f"{'admin' if is_admin else 'learner'}-{uuid4().hex[:12]}@example.com"
    async with app.state.session_factory() as session:
        await CreateUser(SqlAlchemyUserRepository(session), app.state.password_hasher).execute(
            CreateUserCommand(email=email, password=password, is_admin=is_admin)
        )
        await session.commit()
    return email


async def login(client: AsyncClient, email: str, password: str = PASSWORD) -> str:
    response = await client.post("/auth/login", data={"username": email, "password": password})
    assert response.status_code == 200, response.text
    token: str = response.json()["access_token"]
    return token


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def admin_token(app: Any, client: AsyncClient) -> str:
    return await login(client, await create_account(app, is_admin=True))


@pytest.fixture
async def learner_token(app: Any, client: AsyncClient) -> str:
    return await login(client, await create_account(app))
