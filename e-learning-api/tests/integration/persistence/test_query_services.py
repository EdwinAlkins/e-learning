"""Tests d'intégration des projections de lecture SQLAlchemy."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import event

from e_learning.infrastructure.persistence.catalog.models import (
    ChapterModel,
    DocumentModel,
    FormationModel,
    JobModel,
    VideoModel,
)
from e_learning.infrastructure.persistence.catalog.queries import SqlAlchemyCatalogQueryService
from e_learning.infrastructure.persistence.learning.models import NoteModel, ProgressModel
from e_learning.infrastructure.persistence.learning.queries import SqlAlchemyLearningQueryService
from e_learning.infrastructure.persistence.user.models import UserModel


async def test_query_services_project_without_rebuilding_aggregates(app: Any) -> None:
    formation_id = uuid4()
    chapter_id = uuid4()
    empty_chapter_id = uuid4()
    video_id = uuid4()
    user_id = uuid4()
    now = datetime.now(UTC)

    async with app.state.session_factory() as session:
        session.add_all(
            [
                FormationModel(id=formation_id, name="Query Services", slug="query-services"),
                UserModel(id=user_id),
            ]
        )
        await session.commit()
        session.add_all(
            [
                ChapterModel(
                    id=chapter_id,
                    formation_id=formation_id,
                    name="Lecture",
                    slug="lecture",
                    position=0,
                ),
                ChapterModel(
                    id=empty_chapter_id,
                    formation_id=formation_id,
                    name="Vide",
                    slug="vide",
                    position=1,
                ),
            ]
        )
        await session.commit()
        session.add_all(
            [
                VideoModel(
                    id=video_id,
                    chapter_id=chapter_id,
                    title="SQL exact",
                    filename="sql.mp4",
                    relative_path="query-services/lecture/sql.mp4",
                    position=0,
                    duration_seconds=200.0,
                    kind="video",
                    processing_status="ready",
                    transcription_status="none",
                    summary_status="none",
                ),
            ]
        )
        await session.commit()
        session.add_all(
            [
                DocumentModel(
                    id=uuid4(),
                    chapter_id=chapter_id,
                    video_id=video_id,
                    title="Support",
                    filename="support.pdf",
                    relative_path="query-services/lecture/support.pdf",
                    mime_type="application/pdf",
                    position=0,
                ),
                JobModel(
                    id=uuid4(),
                    kind="summary",
                    status="running",
                    progress=40,
                    message="Calcul",
                    video_id=video_id,
                    formation_id=None,
                    created_at=now,
                    updated_at=now,
                ),
                ProgressModel(
                    id=uuid4(),
                    user_id=user_id,
                    video_id=video_id,
                    last_position_seconds=50.0,
                    updated_at=now,
                ),
                NoteModel(
                    id=uuid4(),
                    user_id=user_id,
                    video_id=video_id,
                    timecode_seconds=20.0,
                    content="Deuxième",
                    created_at=now,
                ),
                NoteModel(
                    id=uuid4(),
                    user_id=user_id,
                    video_id=video_id,
                    timecode_seconds=10.0,
                    content="Première",
                    created_at=now,
                ),
            ]
        )
        await session.commit()

    statements: list[str] = []

    def record_statement(
        _connection: object,
        _cursor: object,
        statement: str,
        _parameters: object,
        _context: object,
        _executemany: bool,
    ) -> None:
        if statement.lstrip().upper().startswith(("SELECT", "WITH")):
            statements.append(statement)

    event.listen(app.state.engine.sync_engine, "before_cursor_execute", record_statement)
    try:
        async with app.state.session_factory() as session:
            catalog = SqlAlchemyCatalogQueryService(session)
            learning = SqlAlchemyLearningQueryService(session)

            detail = await catalog.get_formation(str(formation_id))
            assert len(statements) == 4
            assert detail.name == "Query Services"
            assert [chapter.name for chapter in detail.chapters] == ["Lecture", "Vide"]
            assert detail.chapters[0].videos[0].active_jobs[0].progress == 40
            assert detail.chapters[0].documents[0].filename == "support.pdf"
            statements.clear()
            videos = await catalog.list_videos(formation_filter="query")
            assert len(statements) == 1
            assert [(row.chapter_name, row.video_title) for row in videos] == [
                ("Lecture", "SQL exact")
            ]

            statements.clear()
            progress = await learning.get_formation_progress(
                user_id=str(user_id), formation_id=str(formation_id)
            )
            assert len(statements) == 1
            assert progress.chapters[0].videos[0].progress_percentage == 25.0
            assert progress.chapters[0].progress_percentage == 25.0
            assert progress.chapters[1].progress_percentage == 0.0
            assert progress.progress_percentage == 12.5

            statements.clear()
            notes = await learning.list_notes(user_id=str(user_id), video_id=str(video_id))
            assert len(statements) == 1
            assert [note.content for note in notes] == ["Première", "Deuxième"]

            statements.clear()
            position = await learning.get_progress(user_id=str(user_id), video_id=str(video_id))
            assert len(statements) == 1
            assert position.last_position == 50.0
    finally:
        event.remove(app.state.engine.sync_engine, "before_cursor_execute", record_statement)
