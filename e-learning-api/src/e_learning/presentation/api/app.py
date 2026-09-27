"""Fabrique de l'application FastAPI."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text

from e_learning.application.catalog.use_cases.reconcile_catalog import ReconcileCatalog
from e_learning.infrastructure.ai.chat import OpenAIChatAdapter
from e_learning.infrastructure.ai.embeddings import build_embedding_adapter
from e_learning.infrastructure.ai.media_files import FilesystemMediaFiles
from e_learning.infrastructure.ai.qdrant_store import QdrantVectorStore
from e_learning.infrastructure.config import Settings, get_settings
from e_learning.infrastructure.logging import configure_logging
from e_learning.infrastructure.media.ffmpeg_convert import FfmpegConvertAdapter
from e_learning.infrastructure.messaging.rabbitmq import RabbitMQMessageAdapter
from e_learning.infrastructure.persistence.catalog.repository import (
    SqlAlchemyChapterRepository,
    SqlAlchemyDocumentRepository,
    SqlAlchemyFormationRepository,
    SqlAlchemyVideoRepository,
)
from e_learning.infrastructure.persistence.database import (
    create_engine,
    create_session_factory,
    init_db,
)
from e_learning.infrastructure.security.jwt_tokens import JwtTokenService
from e_learning.infrastructure.security.login_throttle import InMemoryLoginThrottle
from e_learning.infrastructure.security.password_hasher import Argon2PasswordHasher
from e_learning.infrastructure.storage.filesystem_catalog import FilesystemCatalogStorage
from e_learning.presentation.api.bootstrap import ensure_first_admin
from e_learning.presentation.api.error_handlers import register_error_handlers
from e_learning.presentation.api.v1.routers import (
    admin_users,
    auth,
    docs,
    formations,
    notes,
    progress,
    studio,
    usage,
    videos,
)

logger = logging.getLogger("e_learning")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)
    logger.info("Démarrage de %s", settings.app_name)
    _check_security(settings)

    engine = create_engine(
        settings.database_url,
        echo=settings.echo_sql,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
    )
    session_factory = create_session_factory(engine)
    catalog_storage = FilesystemCatalogStorage(settings.videos_path)
    media_files = FilesystemMediaFiles(settings.videos_path)
    media_converter = FfmpegConvertAdapter()
    embeddings = build_embedding_adapter(settings)
    vector_store = QdrantVectorStore(settings)
    chat = OpenAIChatAdapter(settings)
    job_publisher = RabbitMQMessageAdapter(
        settings.rabbitmq_url.get_secret_value(),
        exchange_name=settings.rabbitmq_exchange,
    )
    password_hasher = Argon2PasswordHasher()
    token_service = JwtTokenService(
        settings.secret_key.get_secret_value(),
        expire_minutes=settings.access_token_expire_minutes,
    )
    login_throttle = InMemoryLoginThrottle(
        max_failures=settings.login_max_failures,
        window_seconds=settings.login_window_minutes * 60,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        if settings.init_db:
            logger.info("Initialisation du schéma (create_all).")
            await init_db(engine)

        await ensure_first_admin(session_factory, password_hasher, settings)
        await embeddings.warmup()
        await job_publisher.connect()

        task: asyncio.Task[None] | None = None
        if settings.reconcile_on_startup:

            async def _reconcile() -> None:
                async with session_factory() as session:
                    try:
                        use_case = ReconcileCatalog(
                            SqlAlchemyFormationRepository(session),
                            SqlAlchemyChapterRepository(session),
                            SqlAlchemyVideoRepository(session),
                            SqlAlchemyDocumentRepository(session),
                            catalog_storage,
                        )
                        await use_case.execute()
                        await session.commit()
                        logger.info("Catalogue réconcilié.")
                    except Exception:
                        await session.rollback()
                        logger.exception("Échec de la réconciliation du catalogue.")

            task = asyncio.create_task(_reconcile())
        else:
            logger.info(
                "Réconciliation au démarrage désactivée "
                "(APP_RECONCILE_ON_STARTUP=false) — utiliser e-learning-cli reconcile."
            )

        try:
            yield
        finally:
            if task is not None:
                task.cancel()
            await job_publisher.close()
            await engine.dispose()

    docs_url = "/api-docs" if settings.debug else None
    redoc_url = "/api-redoc" if settings.debug else None
    openapi_url = "/openapi.json" if settings.debug else None

    app = FastAPI(
        title=settings.app_name,
        lifespan=lifespan,
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    Instrumentator().instrument(app).expose(app, include_in_schema=False)
    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = session_factory
    app.state.catalog_storage = catalog_storage
    app.state.media_files = media_files
    app.state.media_converter = media_converter
    app.state.embeddings = embeddings
    app.state.vector_store = vector_store
    app.state.chat = chat
    app.state.job_publisher = job_publisher
    app.state.password_hasher = password_hasher
    app.state.token_service = token_service
    app.state.login_throttle = login_throttle

    register_error_handlers(app)
    # Routes fermées par défaut : chaque routeur porte sa garde (get_current_user
    # ou require_admin) ; seuls auth.router et les sondes ci-dessous sont publics.
    app.include_router(auth.router)
    app.include_router(auth.me_router)
    app.include_router(admin_users.router)
    app.include_router(formations.formations_router)
    app.include_router(studio.studio_router)
    app.include_router(videos.router)
    app.include_router(notes.router)
    app.include_router(progress.router)
    app.include_router(usage.router)
    app.include_router(docs.router)

    @app.get("/", tags=["health"])
    async def health() -> dict[str, str]:
        return {"message": "health ok"}

    @app.get("/health", tags=["health"])
    async def liveness() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/ready", tags=["health"])
    async def readiness() -> dict[str, str]:
        # Readiness sans RabbitMQ : le publish est fire-and-forget ; le worker porte le broker.
        async with session_factory() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ready"}

    return app


def _check_security(settings: Settings) -> None:
    """Refuse de démarrer avec des secrets d'exemple hors mode debug (S5, S7)."""
    if "*" in settings.cors_origins:
        raise RuntimeError(
            "APP_CORS_ORIGINS ne doit pas contenir '*' : les cookies d'authentification "
            "exigent une liste explicite d'origines."
        )
    problems = settings.security_problems()
    if not problems:
        return
    if not settings.debug:
        raise RuntimeError("Configuration non sûre : " + " ".join(problems))
    for problem in problems:
        logger.warning("Mode debug, configuration non sûre tolérée : %s", problem)
