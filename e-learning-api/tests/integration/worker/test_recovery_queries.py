"""La récupération worker charge les jobs/vidéos par lots, sans N+1."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import event

from e_learning.application.jobs.dto import ComputeJobMessage
from e_learning.application.shared.messaging import JobPublisherPort
from e_learning.domain.catalog.job import Job
from e_learning.infrastructure.persistence.catalog.models import (
    ChapterModel,
    FormationModel,
    JobModel,
    VideoModel,
)
from e_learning.presentation.worker.handlers import WorkerDeps, recover_and_republish


class RecordingPublisher(JobPublisherPort):
    def __init__(self) -> None:
        self.messages: list[ComputeJobMessage] = []

    async def publish(self, message: ComputeJobMessage) -> None:
        self.messages.append(message)


async def test_recovery_uses_a_fixed_number_of_selects(app: Any) -> None:
    formation_id = uuid4()
    chapter_id = uuid4()
    now = datetime.now(UTC)

    async with app.state.session_factory() as session:
        session.add(FormationModel(id=formation_id, name="Worker", slug="worker"))
        await session.commit()
        session.add(
            ChapterModel(
                id=chapter_id,
                formation_id=formation_id,
                name="Recovery",
                slug="recovery",
                position=0,
            )
        )
        await session.commit()

        processing_ids = [uuid4() for _ in range(3)]
        rag_ids = [uuid4() for _ in range(3)]
        session.add_all(
            [
                VideoModel(
                    id=video_id,
                    chapter_id=chapter_id,
                    title=f"Conversion {index}",
                    filename=f"conversion-{index}.src.mp4",
                    relative_path=f"worker/recovery/conversion-{index}.src.mp4",
                    position=index,
                    duration_seconds=10.0,
                    kind="video",
                    processing_status="processing",
                    transcription_status="none",
                    summary_status="none",
                )
                for index, video_id in enumerate(processing_ids)
            ]
            + [
                VideoModel(
                    id=video_id,
                    chapter_id=chapter_id,
                    title=f"RAG {index}",
                    filename=f"rag-{index}.mp4",
                    relative_path=f"worker/recovery/rag-{index}.mp4",
                    position=index + len(processing_ids),
                    duration_seconds=10.0,
                    kind="video",
                    processing_status="ready",
                    transcription_status="ready",
                    summary_status="ready",
                )
                for index, video_id in enumerate(rag_ids)
            ]
        )
        await session.commit()

        session.add_all(
            [
                JobModel(
                    id=uuid4(),
                    kind=Job.KIND_MEDIA_CONVERSION,
                    status=Job.STATUS_RUNNING,
                    progress=20,
                    message="Conversion",
                    video_id=video_id,
                    formation_id=None,
                    created_at=now,
                    updated_at=now,
                )
                for video_id in processing_ids
            ]
            + [
                JobModel(
                    id=uuid4(),
                    kind=Job.KIND_RAG_INDEX_VIDEO,
                    status=Job.STATUS_RUNNING,
                    progress=20,
                    message="RAG",
                    video_id=video_id,
                    formation_id=None,
                    created_at=now,
                    updated_at=now,
                )
                for video_id in rag_ids
            ]
        )
        await session.commit()

    selects: list[str] = []

    def record_statement(
        _connection: object,
        _cursor: object,
        statement: str,
        _parameters: object,
        _context: object,
        _executemany: bool,
    ) -> None:
        if statement.lstrip().upper().startswith(("SELECT", "WITH")):
            selects.append(statement)

    publisher = RecordingPublisher()
    deps = WorkerDeps(
        session_factory=app.state.session_factory,
        settings=app.state.settings,
        catalog_storage=app.state.catalog_storage,
        media_files=app.state.media_files,
        media_converter=app.state.media_converter,
        embeddings=app.state.embeddings,
        vector_store=app.state.vector_store,
        publisher=publisher,
    )

    event.listen(app.state.engine.sync_engine, "before_cursor_execute", record_statement)
    try:
        await recover_and_republish(deps)
    finally:
        event.remove(app.state.engine.sync_engine, "before_cursor_execute", record_statement)

    assert len(selects) == 4
    assert {message.video_id for message in publisher.messages} >= {
        str(video_id) for video_id in [*processing_ids, *rag_ids]
    }
