"""CLI e-learning — point d'entrée ``e-learning-cli``."""

from __future__ import annotations

import click

from e_learning.infrastructure.config import get_settings
from e_learning.infrastructure.logging import configure_logging
from e_learning.presentation.cli.commands.convert import convert_cmd
from e_learning.presentation.cli.commands.index_rag import index_rag_cmd
from e_learning.presentation.cli.commands.list_videos import list_videos_cmd
from e_learning.presentation.cli.commands.reconcile import reconcile_cmd
from e_learning.presentation.cli.commands.summary import resume_cmd, summary_cmd
from e_learning.presentation.cli.commands.transcribe import transcribe_cmd


@click.group()
def cli() -> None:
    """Outils CLI E-Learning (catalogue, transcription, résumé, conversion)."""
    configure_logging(get_settings().log_level)


cli.add_command(reconcile_cmd)
cli.add_command(list_videos_cmd)
cli.add_command(transcribe_cmd)
cli.add_command(summary_cmd)
cli.add_command(resume_cmd)
cli.add_command(convert_cmd)
cli.add_command(index_rag_cmd)


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
