"""Commande : transcrire une vidéo (Whisper)."""

from __future__ import annotations

import asyncio

import click

from e_learning.application.content.dto import TranscribeCommand
from e_learning.application.content.use_cases.transcribe_video import TranscribeVideo
from e_learning.infrastructure.ai.media_files import FilesystemMediaFiles
from e_learning.infrastructure.ai.whisper_transcription import WhisperTranscriptionAdapter
from e_learning.infrastructure.config import get_settings
from e_learning.infrastructure.persistence.catalog.repository import SqlAlchemyVideoRepository
from e_learning.infrastructure.storage.filesystem_catalog import FilesystemCatalogStorage
from e_learning.presentation.cli.session import transactional_session


@click.command("transcribe")
@click.option("--video-id", "-v", required=True, help="UUID de la vidéo")
@click.option("--model", "-m", default="base", show_default=True, help="Modèle Whisper")
@click.option("--language", "-l", default=None, help="Code langue (ex. fr)")
@click.option("--timecodes/--no-timecodes", default=False, help="Inclure les timecodes")
def transcribe_cmd(video_id: str, model: str, language: str | None, timecodes: bool) -> None:
    """Transcrit une vidéo et écrit le sidecar ``.txt``."""
    asyncio.run(_transcribe(video_id, model, language, timecodes))


async def _transcribe(video_id: str, model: str, language: str | None, timecodes: bool) -> None:
    settings = get_settings()
    storage = FilesystemCatalogStorage(settings.videos_path)
    media = FilesystemMediaFiles(settings.videos_path)
    async with transactional_session() as session:
        use_case = TranscribeVideo(
            SqlAlchemyVideoRepository(session),
            storage,
            media,
            WhisperTranscriptionAdapter(),
        )
        text = await use_case.execute(
            TranscribeCommand(
                video_id=video_id,
                model=model,
                language=language,
                with_timecodes=timecodes,
            )
        )
    preview = text[:500] + ("…" if len(text) > 500 else "")
    click.echo(preview)
    click.echo(f"Transcription enregistrée pour {video_id}")
