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
    # Chat OpenAI-compatible (résumé, ask) — fournisseur distinct des embeddings.
    openai_base_url: str = "http://localhost:1234/v1"
    openai_api_key: SecretStr = SecretStr("lm-studio")
    openai_model: str = "openapi/gpt-oss-20b"
    summary_strategy: SummaryStrategyName = SummaryStrategyName.OPENAPI
    max_upload_size: int = 500 * 1024 * 1024
    # RAG (Qdrant + embeddings)
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "elearning_chunks"
    # Vide → embeddings locaux (sentence-transformers). Sinon API OpenAI-compatible.
    embedding_base_url: str = ""
    embedding_api_key: SecretStr | None = None
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embedding_dims: int = 384
    rag_top_k: int = 6
    rag_chunk_size: int = 800
    rag_chunk_overlap: int = 120
    # Queue jobs de calcul (RabbitMQ)
    rabbitmq_url: SecretStr = SecretStr("amqp://guest:guest@localhost:5672/")
    rabbitmq_exchange: str = "elearning_jobs"
    worker_prefetch: int = 3

    def use_local_embeddings(self) -> bool:
        """True si aucune URL d'embeddings distante n'est configurée."""
        return not self.embedding_base_url.strip()

    def resolved_embedding_base_url(self) -> str:
        url = self.embedding_base_url.strip()
        if not url:
            raise ValueError("APP_EMBEDDING_BASE_URL est vide : utiliser les embeddings locaux.")
        return url

    def resolved_embedding_api_key(self) -> str:
        if self.embedding_api_key is not None:
            return self.embedding_api_key.get_secret_value()
        return self.openai_api_key.get_secret_value()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Point d'accès unique à la configuration (mémoïsé)."""
    return Settings()
