"""Add per-user LLM token usage log and job requester.

Revision ID: 006
Revises: 005_jobs
Create Date: 2026-09-26
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "006_token_usage"
down_revision: str | None = "005_jobs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "token_usage",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("model", sa.String(length=255), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False),
        sa.Column("completion_tokens", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("prompt_tokens >= 0", name="ck_token_usage_prompt"),
        sa.CheckConstraint("completion_tokens >= 0", name="ck_token_usage_completion"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_token_usage_user_created", "token_usage", ["user_id", "created_at"])

    op.add_column("jobs", sa.Column("user_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_jobs_user_id_users", "jobs", "users", ["user_id"], ["id"], ondelete="SET NULL"
    )


def downgrade() -> None:
    op.drop_constraint("fk_jobs_user_id_users", "jobs", type_="foreignkey")
    op.drop_column("jobs", "user_id")
    op.drop_index("ix_token_usage_user_created", table_name="token_usage")
    op.drop_table("token_usage")
