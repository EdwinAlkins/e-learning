"""Modèles ORM — contexte ``catalog``."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from e_learning.infrastructure.persistence.database import Base

if TYPE_CHECKING:
    pass


class FormationModel(Base):
    __tablename__ = "formations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    chapters: Mapped[list[ChapterModel]] = relationship(
        back_populates="formation",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ChapterModel.position",
    )


class ChapterModel(Base):
    __tablename__ = "chapters"
    __table_args__ = (
        UniqueConstraint(
            "formation_id",
            "position",
            name="chapters_formation_id_position_key",
            deferrable=True,
            initially="DEFERRED",
        ),
        UniqueConstraint("formation_id", "slug"),
        CheckConstraint("position >= 0", name="ck_chapters_position"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    formation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("formations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    formation: Mapped[FormationModel] = relationship(back_populates="chapters")
    videos: Mapped[list[VideoModel]] = relationship(
        back_populates="chapter",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="VideoModel.position",
    )
    documents: Mapped[list[DocumentModel]] = relationship(
        back_populates="chapter",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="DocumentModel.position",
    )


class VideoModel(Base):
    __tablename__ = "videos"
    __table_args__ = (
        UniqueConstraint(
            "chapter_id",
            "position",
            name="videos_chapter_id_position_key",
            deferrable=True,
            initially="DEFERRED",
        ),
        UniqueConstraint("chapter_id", "filename"),
        UniqueConstraint("relative_path"),
        CheckConstraint("position >= 0", name="ck_videos_position"),
        CheckConstraint("duration_seconds >= 0", name="ck_videos_duration"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    chapter_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    relative_path: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    kind: Mapped[str] = mapped_column(String(16), nullable=False, server_default="video")
    processing_status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default="ready"
    )
    transcription_status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default="none"
    )
    summary_status: Mapped[str] = mapped_column(String(16), nullable=False, server_default="none")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    chapter: Mapped[ChapterModel] = relationship(back_populates="videos")


class JobModel(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        CheckConstraint("progress >= 0 AND progress <= 100", name="ck_jobs_progress"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    progress: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    message: Mapped[str] = mapped_column(String(255), nullable=False, server_default="")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    video_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("videos.id", ondelete="SET NULL"), nullable=True, index=True
    )
    formation_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("formations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class DocumentModel(Base):
    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint("chapter_id", "filename"),
        UniqueConstraint("relative_path"),
        CheckConstraint("position >= 0", name="ck_documents_position"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    chapter_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False, index=True
    )
    video_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("videos.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    relative_path: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    chapter: Mapped[ChapterModel] = relationship(back_populates="documents")
