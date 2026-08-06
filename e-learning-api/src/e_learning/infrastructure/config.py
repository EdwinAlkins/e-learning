"""Configuration de l'application (préfixe ``APP_``)."""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class LogLevel(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class SummaryStrategyName(StrEnum):
    OPENAPI = "openapi"
    GEMINI = "gemini"


class Settings(BaseSettings):
    """Paramètres applicatifs (surchargables par variables d'environnement)."""

    model_config = SettingsConfigDict(
        env_file=[".env.template", ".env"],
        env_file_encoding="utf-8",
        env_prefix="APP_",
        extra="ignore",
    )

    app_name: str = "E-Learning API"
    database_url: SecretStr = SecretStr(
        "postgresql+asyncpg://elearning:elearning@localhost:5432/elearning"
    )
    echo_sql: bool = False
    init_db: bool = False
    # Réconciliation FS↔DB au boot. Défaut false : préférer ``e-learning-cli reconcile``.
    reconcile_on_startup: bool = False
    videos_path: Path = Path("videos/")
    debug: bool = False
    log_level: LogLevel = LogLevel.INFO
    cors_origins: list[str] = Field(default_factory=list)
    db_pool_size: int = 10
    db_max_overflow: int = 20
    openai_base_url: str = "http://localhost:1234/v1"
    openai_api_key: SecretStr = SecretStr("lm-studio")
    openai_model: str = "openapi/gpt-oss-20b"
    summary_strategy: SummaryStrategyName = SummaryStrategyName.OPENAPI
    max_upload_size: int = 500 * 1024 * 1024
    # RAG (Qdrant + embeddings OpenAI-compatible)
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "elearning_chunks"
    embedding_model: str = "text-embedding-nomic-embed-text-v1.5"
    embedding_dims: int = 768
    rag_top_k: int = 6
    rag_chunk_size: int = 800
    rag_chunk_overlap: int = 120


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Point d'accès unique à la configuration (mémoïsé)."""
    return Settings()
