"""Publisher qui bufferise jusqu'au commit DB (évite la course worker/DB)."""

from __future__ import annotations

import logging

from e_learning.application.jobs.dto import ComputeJobMessage
from e_learning.application.shared.messaging import JobPublisherPort

logger = logging.getLogger(__name__)


class DeferredJobPublisher(JobPublisherPort):
    """Accumule les ``publish`` et les envoie via ``flush`` après le commit."""

    def __init__(self, inner: JobPublisherPort) -> None:
        self._inner = inner
        self._pending: list[ComputeJobMessage] = []

    async def publish(self, message: ComputeJobMessage) -> None:
        self._pending.append(message)
        logger.debug(
            "Publication différée job %s kind=%s (pending=%s)",
            message.job_id,
            message.kind,
            len(self._pending),
        )

    async def flush(self) -> None:
        pending, self._pending = self._pending, []
        if not pending:
            return
        logger.info("Flush de %s publication(s) RabbitMQ après commit", len(pending))
        for message in pending:
            await self._inner.publish(message)

    def clear(self) -> None:
        if self._pending:
            logger.warning(
                "Annulation de %s publication(s) différée(s) (rollback)",
                len(self._pending),
            )
        self._pending.clear()
