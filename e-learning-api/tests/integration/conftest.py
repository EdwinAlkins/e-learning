"""Fixtures integration (Postgres testcontainers)."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from testcontainers.postgres import PostgresContainer

from e_learning.infrastructure.config import Settings
from e_learning.infrastructure.persistence.database import (
    init_db,
)
from e_learning.presentation.api.app import create_app


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
        cors_origins=["*"],
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
