"""Configuration de la base de données (SQLAlchemy async / PostgreSQL)."""

from __future__ import annotations

from uuid import uuid4

from pydantic import SecretStr
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base déclarative commune à tous les modèles ORM."""


def create_engine(
    database_url: SecretStr,
    *,
    echo: bool = False,
    pool_size: int = 10,
    max_overflow: int = 20,
) -> AsyncEngine:
    return create_async_engine(
        database_url.get_secret_value(),
        echo=echo,
        future=True,
        pool_pre_ping=True,
        pool_size=pool_size,
        max_overflow=max_overflow,
        connect_args={"prepared_statement_name_func": lambda: f"__asyncpg_{uuid4()}__"},
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=engine, expire_on_commit=False)


async def init_db(engine: AsyncEngine) -> None:
    from e_learning.infrastructure.persistence.catalog import models as catalog_models  # noqa: F401
    from e_learning.infrastructure.persistence.learning import (
        models as learning_models,  # noqa: F401
    )
    from e_learning.infrastructure.persistence.user import models as user_models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
