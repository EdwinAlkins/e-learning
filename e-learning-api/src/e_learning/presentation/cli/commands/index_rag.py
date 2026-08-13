"""Commande : indexer le corpus RAG (transcriptions / résumés / documents) dans Qdrant."""

from __future__ import annotations

import asyncio

import click

from e_learning.application.content.dto import (
    IndexFormationCommand,
    IndexFormationResult,
    IndexVideoCommand,
)
from e_learning.application.content.use_cases.index_document_content import IndexDocumentContent
from e_learning.application.content.use_cases.index_formation import IndexFormation
from e_learning.application.content.use_cases.index_video_content import IndexVideoContent
from e_learning.domain.catalog.entities import Video
from e_learning.infrastructure.ai.document_text import FilesystemDocumentTextExtractor
from e_learning.infrastructure.ai.embeddings import build_embedding_adapter
from e_learning.infrastructure.ai.media_files import FilesystemMediaFiles
from e_learning.infrastructure.ai.qdrant_store import QdrantVectorStore
from e_learning.infrastructure.config import get_settings
from e_learning.infrastructure.persistence.catalog.repository import (
    SqlAlchemyChapterRepository,
    SqlAlchemyDocumentRepository,
    SqlAlchemyFormationRepository,
    SqlAlchemyVideoRepository,
)
from e_learning.infrastructure.storage.filesystem_catalog import FilesystemCatalogStorage
from e_learning.presentation.cli.session import transactional_session


@click.command("index-rag")
@click.option("--formation-id", default=None, help="Limiter à une formation (UUID)")
@click.option("--video-id", default=None, help="Indexer une seule vidéo (UUID)")
def index_rag_cmd(formation_id: str | None, video_id: str | None) -> None:
    """Indexe les sidecars prêts et les documents extractibles dans Qdrant."""
    if formation_id and video_id:
        raise click.UsageError("Utiliser --formation-id ou --video-id, pas les deux.")
    asyncio.run(_index_rag(formation_id, video_id))


async def _index_rag(formation_id: str | None, video_id: str | None) -> None:
    settings = get_settings()
    media_files = FilesystemMediaFiles(settings.videos_path)
    storage = FilesystemCatalogStorage(settings.videos_path)
    embeddings = build_embedding_adapter(settings)
    await embeddings.warmup()
    vectors = QdrantVectorStore(settings)
    extractor = FilesystemDocumentTextExtractor()

    async with transactional_session() as session:
        videos = SqlAlchemyVideoRepository(session)
        chapters = SqlAlchemyChapterRepository(session)
        formations = SqlAlchemyFormationRepository(session)
        documents = SqlAlchemyDocumentRepository(session)
        index_video = IndexVideoContent(
            videos,
            chapters,
            formations,
            media_files,
            embeddings,
            vectors,
            chunk_size=settings.rag_chunk_size,
            chunk_overlap=settings.rag_chunk_overlap,
        )
        index_document = IndexDocumentContent(
            documents,
            chapters,
            formations,
            storage,
            extractor,
            embeddings,
            vectors,
            chunk_size=settings.rag_chunk_size,
            chunk_overlap=settings.rag_chunk_overlap,
        )

        if video_id:
            n = await index_video.execute(IndexVideoCommand(video_id=video_id))
            click.echo(f"Vidéo {video_id} : {n} chunk(s) indexé(s).")
            return

        def _fmt(result: IndexFormationResult) -> str:
            return (
                f"{result.indexed_videos} vidéo(s), "
                f"{result.indexed_documents} doc(s), "
                f"{result.indexed_chunks} chunk(s)"
            )

        index_formation = IndexFormation(
            formations, videos, chapters, documents, index_video, index_document
        )

        if formation_id:
            result = await index_formation.execute(
                IndexFormationCommand(formation_id=formation_id)
            )
            click.echo(f"Formation {formation_id} : {_fmt(result)}.")
            return

        total_videos = 0
        total_docs = 0
        total_chunks = 0
        for formation in await formations.list_all():
            result = await index_formation.execute(
                IndexFormationCommand(formation_id=str(formation.id))
            )
            total_videos += result.indexed_videos
            total_docs += result.indexed_documents
            total_chunks += result.indexed_chunks
            click.echo(f"  {formation.name}: {_fmt(result)}")
        ready = sum(
            1
            for v in await videos.list_all()
            if v.transcription_status == Video.AI_READY or v.summary_status == Video.AI_READY
        )
        click.echo(
            f"Terminé : {total_videos}/{ready} vidéos indexables, "
            f"{total_docs} doc(s), {total_chunks} chunk(s)."
        )
