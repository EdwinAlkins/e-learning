"""Migration 007 : colonnes d'identification, suppression des comptes anonymes."""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import asyncpg
import pytest
from alembic.config import Config

from alembic import command
from e_learning.infrastructure.config import get_settings

API_ROOT = Path(__file__).resolve().parents[3]


def _plain(url: str) -> str:
    return url.replace("postgresql+asyncpg://", "postgresql://", 1)


async def _execute(url: str, *statements: str) -> None:
    conn = await asyncpg.connect(_plain(url))
    try:
        for statement in statements:
            await conn.execute(statement)
    finally:
        await conn.close()


async def _fetchval(url: str, query: str) -> object:
    conn = await asyncpg.connect(_plain(url))
    try:
        return await conn.fetchval(query)
    finally:
        await conn.close()


@pytest.fixture
def migration_db(postgres_url: str, monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    """Base vierge dédiée : les autres tests utilisent ``create_all``."""
    name = f"migration_{uuid4().hex[:8]}"
    asyncio.run(_execute(postgres_url, f"CREATE DATABASE {name}"))
    url = f"{postgres_url.rsplit('/', 1)[0]}/{name}"
    monkeypatch.setenv("APP_DATABASE_URL", url)
    get_settings.cache_clear()
    yield url
    get_settings.cache_clear()


def _alembic_config() -> Config:
    config = Config(str(API_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(API_ROOT / "alembic"))
    return config


def _user_columns(url: str) -> set[str]:
    rows = asyncio.run(
        _fetchval(
            url,
            "SELECT string_agg(column_name, ',') FROM information_schema.columns "
            "WHERE table_name = 'users'",
        )
    )
    return set(str(rows).split(","))


def test_upgrade_drops_anonymous_users_then_downgrade(migration_db: str) -> None:
    config = _alembic_config()
    command.upgrade(config, "006_token_usage")

    anonymous = uuid4()
    asyncio.run(
        _execute(
            migration_db,
            f"INSERT INTO users (id) VALUES ('{anonymous}'), ('{uuid4()}')",
            "INSERT INTO token_usage (id, user_id, kind, model, prompt_tokens, completion_tokens) "
            f"VALUES ('{uuid4()}', '{anonymous}', 'chat', 'm', 1, 1)",
        )
    )

    command.upgrade(config, "007_user_credentials")

    assert asyncio.run(_fetchval(migration_db, "SELECT count(*) FROM users")) == 0
    # Cascade : les données rattachées aux UID anonymes disparaissent aussi.
    assert asyncio.run(_fetchval(migration_db, "SELECT count(*) FROM token_usage")) == 0
    assert {"email", "hashed_password", "full_name", "is_admin", "is_active"} <= _user_columns(
        migration_db
    )
    asyncio.run(
        _execute(
            migration_db,
            "INSERT INTO users (id, email, hashed_password) "
            f"VALUES ('{uuid4()}', 'ada@example.com', 'hash')",
        )
    )
    is_active = asyncio.run(_fetchval(migration_db, "SELECT is_active AND NOT is_admin FROM users"))
    assert is_active is True
    with pytest.raises(asyncpg.UniqueViolationError):
        asyncio.run(
            _execute(
                migration_db,
                "INSERT INTO users (id, email, hashed_password) "
                f"VALUES ('{uuid4()}', 'ada@example.com', 'hash')",
            )
        )

    command.downgrade(config, "006_token_usage")

    assert _user_columns(migration_db) == {"id", "created_at"}
