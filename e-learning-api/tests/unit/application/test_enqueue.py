"""Tests — enqueue jobs + dispatch worker."""

from __future__ import annotations

from pathlib import Path

import pytest

from e_learning.application.content.use_cases.start_formation_index import StartFormationIndex
from e_learning.application.content.use_cases.start_transcription import StartTranscription
from e_learning.application.jobs.dto import ComputeJobMessage, routing_key_for
from e_learning.application.jobs.enqueue import publish_compute_job
from e_learning.domain.catalog.entities import Chapter, Formation, Video
from e_learning.domain.catalog.job import Job
from e_learning.domain.catalog.value_objects import (
    ChapterName,
    DurationSeconds,
    FormationName,
    Position,
    RelativePath,
    VideoTitle,
)
from e_learning.infrastructure.messaging.deferred import DeferredJobPublisher
from e_learning.presentation.worker.handlers import HANDLERS, dispatch
from tests.unit.application._fakes import (
    FakeFormationRepository,
    FakeJobRepository,
    FakeVideoRepository,
    RecordingPublisher,
)
from tests.unit.application.test_ai_jobs import FakeMediaFiles


async def _seed_ready_video(videos: FakeVideoRepository) -> Video:
    formation = Formation.create(name=FormationName("Formation Test"))
    chapter = Chapter.create(
        formation_id=formation.id,
        name=ChapterName("Chapitre 1"),
        position=Position(0),
    )
    video = Video.create(
        chapter_id=chapter.id,
        title=VideoTitle("Intro"),
        filename="intro.mp4",
        relative_path=RelativePath("formation/chapitre/intro.mp4"),
        position=Position(0),
        duration=DurationSeconds(10),
        processing_status=Video.STATUS_READY,
    )
    await videos.save(video)
    return video


async def test_start_transcription_publishes_job(tmp_path: Path) -> None:
    videos = FakeVideoRepository()
    jobs = FakeJobRepository()
    media = FakeMediaFiles(tmp_path)
    publisher = RecordingPublisher()
    video = await _seed_ready_video(videos)

    dto = await StartTranscription(videos, media, jobs, publisher).execute(str(video.id))

    assert len(publisher.published) == 1
    message = publisher.published[0]
    assert isinstance(message, ComputeJobMessage)
    assert message.routing_key == routing_key_for(Job.KIND_TRANSCRIPTION)
    assert message.kind == Job.KIND_TRANSCRIPTION
    assert message.job_id == dto.active_jobs[0].id
    assert message.video_id == str(video.id)


async def test_start_formation_index_publishes_job() -> None:
    formations = FakeFormationRepository()
    jobs = FakeJobRepository()
    publisher = RecordingPublisher()
    formation = Formation.create(name=FormationName("F1"))
    await formations.save(formation)

    job = await StartFormationIndex(formations, jobs, publisher).execute(str(formation.id))

    assert job.kind == Job.KIND_RAG_INDEX_FORMATION
    assert len(publisher.published) == 1
    message = publisher.published[0]
    assert message.routing_key == "job.rag_index_formation"
    assert message.formation_id == str(formation.id)


async def test_deferred_publisher_flushes_after_commit() -> None:
    inner = RecordingPublisher()
    deferred = DeferredJobPublisher(inner)
    await deferred.publish(
        ComputeJobMessage(job_id="1", kind=Job.KIND_TRANSCRIPTION, video_id="v1")
    )
    assert inner.published == []
    await deferred.flush()
    assert len(inner.published) == 1
    deferred.clear()
    await deferred.publish(
        ComputeJobMessage(job_id="2", kind=Job.KIND_SUMMARY, video_id="v1")
    )
    deferred.clear()
    await deferred.flush()
    assert len(inner.published) == 1


async def test_publish_compute_job_helper() -> None:
    from e_learning.application.catalog.dto import JobDTO

    publisher = RecordingPublisher()
    job = JobDTO(
        id="abc",
        kind=Job.KIND_MEDIA_CONVERSION,
        status=Job.STATUS_QUEUED,
        progress=0,
        message="wait",
        video_id="vid",
    )
    await publish_compute_job(publisher, job)
    message = publisher.published[0]
    assert message.routing_key == "job.media_conversion"
    assert message.job_id == "abc"
    assert message.video_id == "vid"


def test_compute_job_message_rejects_unknown_kind() -> None:
    with pytest.raises(ValueError, match="kind invalide"):
        ComputeJobMessage(job_id="x", kind="unknown_kind")


def test_compute_job_message_requires_video_id() -> None:
    with pytest.raises(ValueError, match="video_id requis"):
        ComputeJobMessage(job_id="x", kind=Job.KIND_TRANSCRIPTION)


def test_compute_job_message_from_dict_validates() -> None:
    msg = ComputeJobMessage.from_dict(
        {"job_id": "abc", "kind": "transcription", "video_id": "vid"}
    )
    assert msg.job_id == "abc"
    with pytest.raises(ValueError, match="incomplet"):
        ComputeJobMessage.from_dict({"kind": "transcription"})


async def test_dispatch_unknown_kind_raises() -> None:
    class _Deps:
        pass

    # Bypass __post_init__ pour tester le fallback dispatch
    message = object.__new__(ComputeJobMessage)
    object.__setattr__(message, "job_id", "x")
    object.__setattr__(message, "kind", "unknown_kind")
    object.__setattr__(message, "video_id", None)
    object.__setattr__(message, "formation_id", None)

    with pytest.raises(ValueError, match="inconnu"):
        await dispatch(_Deps(), message)  # type: ignore[arg-type]


def test_all_job_kinds_have_handlers() -> None:
    for kind in (
        Job.KIND_MEDIA_CONVERSION,
        Job.KIND_TRANSCRIPTION,
        Job.KIND_SUMMARY,
        Job.KIND_RAG_INDEX_VIDEO,
        Job.KIND_RAG_INDEX_FORMATION,
    ):
        assert kind in HANDLERS
