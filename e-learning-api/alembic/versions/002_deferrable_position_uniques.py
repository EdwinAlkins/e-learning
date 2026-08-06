"""Make position unique constraints DEFERRABLE INITIALLY DEFERRED.

Revision ID: 002
Revises: 001
Create Date: 2026-07-30
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "002_deferrable_position_uniques"
down_revision: str | None = "001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE chapters DROP CONSTRAINT IF EXISTS chapters_formation_id_position_key"
    )
    op.execute(
        """
        ALTER TABLE chapters
        ADD CONSTRAINT chapters_formation_id_position_key
        UNIQUE (formation_id, position)
        DEFERRABLE INITIALLY DEFERRED
        """
    )
    op.execute("ALTER TABLE videos DROP CONSTRAINT IF EXISTS videos_chapter_id_position_key")
    op.execute(
        """
        ALTER TABLE videos
        ADD CONSTRAINT videos_chapter_id_position_key
        UNIQUE (chapter_id, position)
        DEFERRABLE INITIALLY DEFERRED
        """
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE chapters DROP CONSTRAINT IF EXISTS chapters_formation_id_position_key"
    )
    op.execute(
        """
        ALTER TABLE chapters
        ADD CONSTRAINT chapters_formation_id_position_key
        UNIQUE (formation_id, position)
        """
    )
    op.execute("ALTER TABLE videos DROP CONSTRAINT IF EXISTS videos_chapter_id_position_key")
    op.execute(
        """
        ALTER TABLE videos
        ADD CONSTRAINT videos_chapter_id_position_key
        UNIQUE (chapter_id, position)
        """
    )
