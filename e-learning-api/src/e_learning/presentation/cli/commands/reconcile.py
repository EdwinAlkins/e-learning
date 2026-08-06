"""Commande : réconcilier le catalogue FS ↔ base."""

from __future__ import annotations

import asyncio
from pathlib import Path

import click

from e_learning.application.catalog.use_cases.reconcile_catalog import ReconcileCatalog
from e_learning.infrastructure.config import get_settings
from e_learning.infrastructure.persistence.catalog.repository import (
    SqlAlchemyChapterRepository,
    SqlAlchemyDocumentRepository,
    SqlAlchemyFormationRepository,
    SqlAlchemyVideoRepository,
)
from e_learning.infrastructure.storage.filesystem_catalog import FilesystemCatalogStorage
from e_learning.presentation.cli.session import transactional_session


@click.command("reconcile")
@click.option(
    "--videos-path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Racine vidéos (défaut : APP_VIDEOS_PATH)",
)
def reconcile_cmd(videos_path: Path | None) -> None:
    """Régénère le catalogue en synchronisant le FS avec Postgres."""
    asyncio.run(_reconcile(videos_path))


async def _reconcile(videos_path: Path | None) -> None:
    settings = get_settings()
    root = videos_path or Path(settings.videos_path)
    storage = FilesystemCatalogStorage(root)
    scanned = storage.scan()
    n_videos = sum(len(c.videos) for f in scanned for c in f.chapters)
    n_docs = sum(len(c.documents) for f in scanned for c in f.chapters)
    click.echo(
        f"Scan de {root} : {len(scanned)} formation(s), {n_videos} vidéo(s), {n_docs} document(s)"
    )

    async with transactional_session() as session:
        use_case = ReconcileCatalog(
            SqlAlchemyFormationRepository(session),
            SqlAlchemyChapterRepository(session),
            SqlAlchemyVideoRepository(session),
            SqlAlchemyDocumentRepository(session),
            storage,
        )
        await use_case.execute()
        videos = await SqlAlchemyVideoRepository(session).list_all()

    n_tx = sum(1 for v in videos if v.transcription_status == "ready")
    n_sum = sum(1 for v in videos if v.summary_status == "ready")
    click.echo(
        f"Catalogue réconcilié "
        f"({n_tx}/{len(videos)} transcriptions, {n_sum}/{len(videos)} résumés ready)."
    )
