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
from e_learning.infrastructure.ai.embeddings import OpenAIEmbeddingAdapter
from e_learning.infrastructure.ai.media_files import FilesystemMediaFiles
from e_learning.infrastructure.ai.qdrant_store import QdrantVectorStore
from e_learning.infrastructure.config import Settings, get_settings
from e_learning.infrastructure.logging import configure_logging
from e_learning.infrastructure.media.ffmpeg_convert import FfmpegConvertAdapter
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
from e_learning.infrastructure.storage.filesystem_catalog import FilesystemCatalogStorage
from e_learning.presentation.api.background import (
    _DEFAULT_FFMPEG_CONCURRENCY,
    resume_pending_background_jobs,
)
from e_learning.presentation.api.error_handlers import register_error_handlers
from e_learning.presentation.api.v1.routers import auth, docs, formations, notes, progress, videos

logger = logging.getLogger("e_learning")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)
    logger.info("Démarrage de %s", settings.app_name)

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
    embeddings = OpenAIEmbeddingAdapter(settings)
    vector_store = QdrantVectorStore(settings)
    chat = OpenAIChatAdapter(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        if settings.init_db:
            logger.info("Initialisation du schéma (create_all).")
            await init_db(engine)

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

        # Reprendre conversions média + jobs IA stuck (BackgroundTasks perdues au restart)
        resume_task = asyncio.create_task(resume_pending_background_jobs(app))

        try:
            yield
        finally:
            if task is not None:
                task.cancel()
            resume_task.cancel()
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
    app.state.media_conversion_semaphore = asyncio.Semaphore(_DEFAULT_FFMPEG_CONCURRENCY)

    register_error_handlers(app)
    app.include_router(auth.router)
    app.include_router(formations.formations_router)
    app.include_router(formations.studio_router)
    app.include_router(videos.router)
    app.include_router(notes.router)
    app.include_router(progress.router)
    app.include_router(docs.router)

    @app.get("/", tags=["health"])
    async def health() -> dict[str, str]:
        return {"message": "health ok"}

    @app.get("/health", tags=["health"])
    async def liveness() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/ready", tags=["health"])
    async def readiness() -> dict[str, str]:
        async with session_factory() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ready"}

    return app
