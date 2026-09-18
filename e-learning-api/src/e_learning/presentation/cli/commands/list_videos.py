"""Commande : lister les vidéos du catalogue (aide au choix d'UUID)."""

from __future__ import annotations

import asyncio

import click

from e_learning.infrastructure.persistence.catalog.queries import SqlAlchemyCatalogQueryService
from e_learning.presentation.cli.session import transactional_session


@click.command("list-videos")
@click.option("--formation", "-f", default=None, help="Filtrer par nom/slug de formation")
def list_videos_cmd(formation: str | None) -> None:
    """Liste les vidéos en base (id, titre, chemin)."""
    asyncio.run(_list_videos(formation))


async def _list_videos(formation_filter: str | None) -> None:
    async with transactional_session() as session:
        rows = await SqlAlchemyCatalogQueryService(session).list_videos(
            formation_filter=formation_filter
        )

        current_formation: str | None = None
        current_chapter: str | None = None
        for row in rows:
            if row.formation_id != current_formation:
                click.echo(f"\n[{row.formation_slug}] {row.formation_name} ({row.formation_id})")
                current_formation = row.formation_id
                current_chapter = None
            if row.chapter_id != current_chapter:
                click.echo(f"  └─ {row.chapter_name}")
                current_chapter = row.chapter_id
            click.echo(f"       {row.video_id}  {row.video_title}  ({row.relative_path})")

        click.echo(f"\n{len(rows)} vidéo(s).")
