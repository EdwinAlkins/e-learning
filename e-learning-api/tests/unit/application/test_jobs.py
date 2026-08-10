"""Tests — entité Job + création / projection."""

from __future__ import annotations

from pathlib import Path

from e_learning.application.content.use_cases.start_summary_generation import (
    StartSummaryGeneration,
)
from e_learning.application.content.use_cases.start_transcription import StartTranscription
from e_learning.application.jobs.create_job import create_queued_job
from e_learning.domain.catalog.entities import Chapter, Formation, Video
from e_learning.domain.catalog.job import Job
from e_learning.domain.catalog.value_objects import (
    ChapterName,
    DurationSeconds,
    FormationName,
    JobId,
    Position,
    RelativePath,
    VideoTitle,
)
from e_learning.presentation.api.dependencies.session import SessionDep
from tests.unit.application._fakes import FakeJobRepository, FakeVideoRepository, RecordingPublisher
from tests.unit.application.test_ai_jobs import FakeMediaFiles


async def _seed_ready_video(
    videos: FakeVideoRepository,
    *,
    transcription_status: str = Video.AI_NONE,
    summary_status: str = Video.AI_NONE,
) -> Video:
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
        transcription_status=transcription_status,
        summary_status=summary_status,
    )
    await videos.save(video)
    return video


def test_job_lifecycle_progress() -> None:
    job = Job.create(kind=Job.KIND_TRANSCRIPTION, message="queued")
    assert job.status == Job.STATUS_QUEUED
    assert job.progress == 0
    job.mark_running(message="go")
    assert job.status == Job.STATUS_RUNNING
    job.update_progress(42, "mid")
    assert job.progress == 42
    assert job.message == "mid"
    job.mark_succeeded()
    assert job.status == Job.STATUS_SUCCEEDED
    assert job.progress == 100


async def test_create_queued_job_persists(tmp_path: Path) -> None:
    jobs = FakeJobRepository()
    videos = FakeVideoRepository()
    video = await _seed_ready_video(videos)
    dto = await create_queued_job(
        jobs, kind=Job.KIND_SUMMARY, video_id=str(video.id), message="wait"
    )
    assert dto.kind == Job.KIND_SUMMARY
    assert dto.status == Job.STATUS_QUEUED
    stored = await jobs.get(JobId.from_string(dto.id))
    assert stored.is_active


async def test_start_transcription_creates_active_job(tmp_path: Path) -> None:
    videos = FakeVideoRepository()
    jobs = FakeJobRepository()
    media = FakeMediaFiles(tmp_path)
    video = await _seed_ready_video(videos)

    dto = await StartTranscription(videos, media, jobs, RecordingPublisher()).execute(str(video.id))

    assert dto.transcription_status == Video.AI_PROCESSING
    assert len(dto.active_jobs) == 1
    assert dto.active_jobs[0].kind == Job.KIND_TRANSCRIPTION
    assert (await jobs.list_active())[0].kind == Job.KIND_TRANSCRIPTION


async def test_start_summary_creates_active_job(tmp_path: Path) -> None:
    videos = FakeVideoRepository()
    jobs = FakeJobRepository()
    media = FakeMediaFiles(tmp_path)
    video = await _seed_ready_video(videos, transcription_status=Video.AI_READY)
    media.write_text(media.transcription_path(str(video.relative_path)), "tx")

    dto = await StartSummaryGeneration(videos, media, jobs, RecordingPublisher()).execute(str(video.id))

    assert dto.summary_status == Video.AI_PROCESSING
    assert dto.active_jobs[0].kind == Job.KIND_SUMMARY


def test_session_dep_uses_function_scope() -> None:
    from typing import get_args

    depends = get_args(SessionDep)[1]
    assert depends.scope == "function"
