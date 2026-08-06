"""Add videos.transcription_status and videos.summary_status.

Revision ID: 004
Revises: 003_video_kind_processing
Create Date: 2026-08-05
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "004_video_ai_status"
down_revision: str | None = "003_video_kind_processing"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "videos",
        sa.Column(
            "transcription_status",
            sa.String(length=16),
            nullable=False,
            server_default="none",
        ),
    )
    op.add_column(
        "videos",
        sa.Column(
            "summary_status",
            sa.String(length=16),
            nullable=False,
            server_default="none",
        ),
    )


def downgrade() -> None:
    op.drop_column("videos", "summary_status")
    op.drop_column("videos", "transcription_status")
