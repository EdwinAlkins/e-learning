"""Modèles ORM — contexte ``usage``."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from e_learning.infrastructure.persistence.database import Base

# Enregistre la table cible des FK ``users.id`` quel que soit le process (worker, CLI)
from e_learning.infrastructure.persistence.user import models as _user_models  # noqa: F401


class TokenUsageModel(Base):
    __tablename__ = "token_usage"
    __table_args__ = (
        CheckConstraint("prompt_tokens >= 0", name="ck_token_usage_prompt"),
        CheckConstraint("completion_tokens >= 0", name="ck_token_usage_completion"),
        Index("ix_token_usage_user_created", "user_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    model: Mapped[str] = mapped_column(String(255), nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
