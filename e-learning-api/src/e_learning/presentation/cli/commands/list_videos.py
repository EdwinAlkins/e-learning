"""Commande : lister les vidéos du catalogue (aide au choix d'UUID)."""

from __future__ import annotations

import asyncio

import click

from e_learning.infrastructure.persistence.catalog.repository import (
    SqlAlchemyChapterRepository,
    SqlAlchemyFormationRepository,
    SqlAlchemyVideoRepository,
)
from e_learning.presentation.cli.session import transactional_session


@click.command("list-videos")
@click.option("--formation", "-f", default=None, help="Filtrer par nom/slug de formation")
def list_videos_cmd(formation: str | None) -> None:
    """Liste les vidéos en base (id, titre, chemin)."""
    asyncio.run(_list_videos(formation))


async def _list_videos(formation_filter: str | None) -> None:
    async with transactional_session() as session:
        formations = SqlAlchemyFormationRepository(session)
        chapters = SqlAlchemyChapterRepository(session)
        videos = SqlAlchemyVideoRepository(session)

        all_formations = await formations.list_all()
        if formation_filter:
            needle = formation_filter.lower()
            all_formations = [
                f
                for f in all_formations
                if needle in str(f.name).lower() or needle in str(f.slug).lower()
            ]

        count = 0
        for formation in all_formations:
            click.echo(f"\n[{formation.slug}] {formation.name} ({formation.id})")
            for chapter in await chapters.list_by_formation(formation.id):
                click.echo(f"  └─ {chapter.name}")
                for video in await videos.list_by_chapter(chapter.id):
                    click.echo(f"       {video.id}  {video.title}  ({video.relative_path})")
                    count += 1
        click.echo(f"\n{count} vidéo(s).")
