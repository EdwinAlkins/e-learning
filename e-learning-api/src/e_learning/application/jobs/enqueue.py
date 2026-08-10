"""Helper : publier un job de calcul sur le broker."""

from __future__ import annotations

import logging

from e_learning.application.catalog.dto import JobDTO
from e_learning.application.jobs.dto import ComputeJobMessage
from e_learning.application.shared.messaging import JobPublisherPort

logger = logging.getLogger(__name__)


async def publish_compute_job(publisher: JobPublisherPort, job: JobDTO) -> None:
    message = ComputeJobMessage(
        job_id=job.id,
        kind=job.kind,
        video_id=job.video_id,
        formation_id=job.formation_id,
    )
    logger.debug(
        "Enqueue job %s kind=%s routing_key=%s video_id=%s formation_id=%s",
        message.job_id,
        message.kind,
        message.routing_key,
        message.video_id,
        message.formation_id,
    )
    await publisher.publish(message)
