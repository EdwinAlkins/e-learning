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


# Valeur d'exemple de ``.env.template`` : refusée hors mode debug.
INSECURE_DEFAULT_SECRET = "changethis"
SECRET_KEY_MIN_LENGTH = 32


class Settings(BaseSettings):
    """Paramètres applicatifs (surchargables par variables d'environnement)."""

    model_config = SettingsConfigDict(
        env_file=[".env.template", ".env"],
        env_file_encoding="utf-8",
        env_prefix="APP_",
        extra="ignore",
    )

    app_name: str = "Cladèse API"
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
    # Authentification (JWT HS256 + premier admin)
    secret_key: SecretStr = SecretStr(INSECURE_DEFAULT_SECRET)
    access_token_expire_minutes: int = 60 * 24 * 7
    first_admin_email: str = "admin@example.com"
    first_admin_password: SecretStr = SecretStr(INSECURE_DEFAULT_SECRET)
    # Anti-bruteforce : N échecs par email ou par IP sur la fenêtre → 429
    login_max_failures: int = 5
    login_window_minutes: int = 15
    # Hôtes où le cookie de session est posé sans ``Secure`` quand l'API est
    # servie en HTTP (sinon le navigateur le rejette). Ex. : IP d'un serveur LAN.
    insecure_cookie_hosts: list[str] = Field(
        default_factory=lambda: ["localhost", "127.0.0.1", "::1"]
    )

    def security_problems(self) -> list[str]:
        """Réglages dangereux en production (bloquants hors mode debug)."""
        problems: list[str] = []
        secret = self.secret_key.get_secret_value()
        if secret == INSECURE_DEFAULT_SECRET or len(secret) < SECRET_KEY_MIN_LENGTH:
            problems.append(
                f"APP_SECRET_KEY doit être changée et faire au moins "
                f"{SECRET_KEY_MIN_LENGTH} caractères."
            )
        if self.first_admin_password.get_secret_value() == INSECURE_DEFAULT_SECRET:
            problems.append("APP_FIRST_ADMIN_PASSWORD doit être changé.")
        return problems

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
