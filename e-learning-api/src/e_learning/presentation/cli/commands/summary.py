"""Commande : générer le résumé d'une vidéo."""

from __future__ import annotations

import asyncio

import click

from e_learning.application.content.dto import GenerateSummaryCommand
from e_learning.application.content.use_cases.generate_summary import GenerateSummary
from e_learning.infrastructure.ai.media_files import FilesystemMediaFiles
from e_learning.infrastructure.ai.summary import GeminiSummaryAdapter, OpenAPISummaryAdapter
from e_learning.infrastructure.config import SummaryStrategyName, get_settings
from e_learning.infrastructure.persistence.catalog.repository import SqlAlchemyVideoRepository
from e_learning.presentation.cli.session import transactional_session


@click.command("summary")
@click.option("--video-id", "-v", required=True, help="UUID de la vidéo")
def summary_cmd(video_id: str) -> None:
    """Génère un résumé à partir de la transcription (sidecar ``.md``)."""
    asyncio.run(_summary(video_id))


# Alias historique
@click.command("resume")
@click.option("--video-id", "-v", required=True, help="UUID de la vidéo")
def resume_cmd(video_id: str) -> None:
    """Alias de ``summary``."""
    asyncio.run(_summary(video_id))


async def _summary(video_id: str) -> None:
    settings = get_settings()
    media = FilesystemMediaFiles(settings.videos_path)
    summary_port = (
        GeminiSummaryAdapter()
        if settings.summary_strategy is SummaryStrategyName.GEMINI
        else OpenAPISummaryAdapter(settings)
    )
    async with transactional_session() as session:
        use_case = GenerateSummary(SqlAlchemyVideoRepository(session), media, summary_port)
        dto = await use_case.execute(GenerateSummaryCommand(video_id=video_id))
    preview = dto.summary[:500] + ("…" if len(dto.summary) > 500 else "")
    click.echo(preview)
    click.echo(f"Résumé enregistré pour {video_id}")
