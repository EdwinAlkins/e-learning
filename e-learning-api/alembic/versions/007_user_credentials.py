"""Add credentials and roles to users; drop anonymous users.

Les comptes anonymes (UID sans email) ne peuvent pas être rattachés de façon
sûre à un email : ils sont supprimés, avec leurs notes, leur progression et
leur consommation LLM (FK ``ON DELETE CASCADE`` ; ``jobs.user_id`` passe à NULL).
Le downgrade retire les colonnes mais ne restaure pas les lignes supprimées :
sauvegarder la base avant d'appliquer cette migration.

Revision ID: 007
Revises: 006_token_usage
Create Date: 2026-09-26
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "007_user_credentials"
down_revision: str | None = "006_token_usage"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("email", sa.String(length=320), nullable=True))
    op.add_column("users", sa.Column("hashed_password", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("full_name", sa.String(length=255), nullable=True))
    op.add_column(
        "users",
        sa.Column("is_admin", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column(
        "users",
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
    )

    op.execute("DELETE FROM users WHERE email IS NULL")

    op.alter_column("users", "email", nullable=False)
    op.alter_column("users", "hashed_password", nullable=False)
    op.create_unique_constraint("users_email_key", "users", ["email"])


def downgrade() -> None:
    op.drop_constraint("users_email_key", "users", type_="unique")
    op.drop_column("users", "is_active")
    op.drop_column("users", "is_admin")
    op.drop_column("users", "full_name")
    op.drop_column("users", "hashed_password")
    op.drop_column("users", "email")
