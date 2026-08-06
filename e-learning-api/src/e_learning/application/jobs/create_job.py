"""Helpers création de jobs (même transaction que le passage à processing)."""

from __future__ import annotations

from e_learning.application.catalog.dto import JobDTO
from e_learning.domain.catalog.job import Job
from e_learning.domain.catalog.repository import JobRepository
from e_learning.domain.catalog.value_objects import FormationId, VideoId


async def create_queued_job(
    jobs: JobRepository,
    *,
    kind: str,
    video_id: str | None = None,
    formation_id: str | None = None,
    message: str = "En file d'attente",
) -> JobDTO:
    job = Job.create(
        kind=kind,
        video_id=VideoId.from_string(video_id) if video_id else None,
        formation_id=FormationId.from_string(formation_id) if formation_id else None,
        message=message,
    )
    await jobs.save(job)
    return JobDTO.from_entity(job)
