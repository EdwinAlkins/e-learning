"""Add videos.kind and videos.processing_status.

Revision ID: 003
Revises: 002_deferrable_position_uniques
Create Date: 2026-08-04
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "003_video_kind_processing"
down_revision: str | None = "002_deferrable_position_uniques"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "videos",
        sa.Column("kind", sa.String(length=16), nullable=False, server_default="video"),
    )
    op.add_column(
        "videos",
        sa.Column(
            "processing_status",
            sa.String(length=16),
            nullable=False,
            server_default="ready",
        ),
    )


def downgrade() -> None:
    op.drop_column("videos", "processing_status")
    op.drop_column("videos", "kind")
