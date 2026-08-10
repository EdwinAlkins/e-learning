"""Use case : démarrer l'indexation RAG d'une formation."""

from __future__ import annotations

from e_learning.application.catalog.dto import JobDTO
from e_learning.application.jobs.create_job import create_queued_job
from e_learning.application.jobs.enqueue import publish_compute_job
from e_learning.application.shared.messaging import JobPublisherPort
from e_learning.domain.catalog.job import Job
from e_learning.domain.catalog.repository import FormationRepository, JobRepository
from e_learning.domain.catalog.value_objects import FormationId


class StartFormationIndex:
    def __init__(
        self,
        formations: FormationRepository,
        jobs: JobRepository,
        publisher: JobPublisherPort,
    ) -> None:
        self._formations = formations
        self._jobs = jobs
        self._publisher = publisher

    async def execute(self, formation_id: str) -> JobDTO:
        await self._formations.get(FormationId.from_string(formation_id))
        job = await create_queued_job(
            self._jobs,
            kind=Job.KIND_RAG_INDEX_FORMATION,
            formation_id=formation_id,
            message="Indexation formation en file d'attente",
        )
        await publish_compute_job(self._publisher, job)
        return job
