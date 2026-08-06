"""Commande : convertir des vidéos en MP4."""

from __future__ import annotations

import asyncio
from pathlib import Path

import click

from e_learning.application.content.dto import ConvertVideosCommand
from e_learning.application.content.use_cases.convert_videos import ConvertVideos
from e_learning.infrastructure.config import get_settings
from e_learning.infrastructure.media.ffmpeg_convert import FfmpegConvertAdapter


@click.command("convert")
@click.option(
    "--glob",
    "source_glob",
    default="**/*.*",
    show_default=True,
    help="Motif sous APP_VIDEOS_PATH (vidéos : mp4/webm/mkv/avi/…)",
)
@click.option(
    "--overwrite/--no-overwrite",
    default=False,
    help="Ré-encode aussi les MP4 existants (H.264/AAC web) et écrase les cibles",
)
@click.option(
    "--videos-path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Racine vidéos (défaut : APP_VIDEOS_PATH)",
)
def convert_cmd(source_glob: str, overwrite: bool, videos_path: Path | None) -> None:
    """Convertit des médias en MP4 via ffmpeg."""
    asyncio.run(_convert(source_glob, overwrite, videos_path))


async def _convert(source_glob: str, overwrite: bool, videos_path: Path | None) -> None:
    settings = get_settings()
    root = videos_path or Path(settings.videos_path)
    use_case = ConvertVideos(FfmpegConvertAdapter(), videos_root=root)
    converted = await use_case.execute(
        ConvertVideosCommand(source_glob=source_glob, overwrite=overwrite)
    )
    for path in converted:
        click.echo(path)
    click.echo(f"{len(converted)} fichier(s) converti(s).")
