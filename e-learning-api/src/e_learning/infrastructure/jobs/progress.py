"""Adaptateur SQLAlchemy — progression des jobs de fond."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from e_learning.domain.catalog.job import Job
from e_learning.domain.catalog.value_objects import JobId
from e_learning.infrastructure.persistence.catalog.repository import SqlAlchemyJobRepository

logger = logging.getLogger("e_learning")


class DbJobProgressReporter:
    """Met à jour ``jobs.progress`` avec throttle (Δ≥5 % ou ≥1.5 s)."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        job_id: str,
        *,
        min_interval_s: float = 1.5,
        min_delta: int = 5,
    ) -> None:
        self._session_factory = session_factory
        self._job_id = JobId.from_string(job_id)
        self._min_interval_s = min_interval_s
        self._min_delta = min_delta
        self._last_progress = -1
        self._last_write = 0.0
        self._lock = asyncio.Lock()

    async def set(self, progress: int, message: str | None = None) -> None:
        progress = max(0, min(100, int(progress)))
        now = time.monotonic()
        force = progress >= 100 or progress == 0
        async with self._lock:
            if (
                not force
                and progress < self._last_progress + self._min_delta
                and now - self._last_write < self._min_interval_s
                and message is None
            ):
                return
            try:
                async with self._session_factory() as session:
                    jobs = SqlAlchemyJobRepository(session)
                    job = await jobs.get(self._job_id)
                    if job.status in (
                        Job.STATUS_SUCCEEDED,
                        Job.STATUS_FAILED,
                        Job.STATUS_CANCELLED,
                    ):
                        return
                    job.update_progress(progress, message)
                    await jobs.save(job)
                    await session.commit()
                self._last_progress = progress
                self._last_write = now
            except Exception:
                logger.exception("Échec update progress job %s", self._job_id)

    def as_sync_callback(self, loop: asyncio.AbstractEventLoop) -> Callable[[int], None]:
        """Callback sync (thread ffmpeg) → schedule ``set`` sur la loop."""

        def _cb(progress: int) -> None:
            fut = asyncio.run_coroutine_threadsafe(self.set(progress, "Encodage…"), loop)
            try:
                fut.result(timeout=5)
            except Exception:
                logger.exception("Échec callback progress sync job %s", self._job_id)

        return _cb


async def mark_job_running(
    session_factory: async_sessionmaker[AsyncSession],
    job_id: str,
    *,
    message: str = "Démarrage…",
) -> None:
    async with session_factory() as session:
        jobs = SqlAlchemyJobRepository(session)
        job = await jobs.get(JobId.from_string(job_id))
        job.mark_running(message=message)
        await jobs.save(job)
        await session.commit()


async def mark_job_succeeded(
    session_factory: async_sessionmaker[AsyncSession],
    job_id: str,
    *,
    message: str = "Terminé",
) -> None:
    async with session_factory() as session:
        jobs = SqlAlchemyJobRepository(session)
        job = await jobs.get(JobId.from_string(job_id))
        job.mark_succeeded(message=message)
        await jobs.save(job)
        await session.commit()


async def mark_job_failed(
    session_factory: async_sessionmaker[AsyncSession],
    job_id: str,
    error: str,
    *,
    message: str = "Échec",
) -> None:
    async with session_factory() as session:
        jobs = SqlAlchemyJobRepository(session)
        job = await jobs.get(JobId.from_string(job_id))
        job.mark_failed(error, message=message)
        await jobs.save(job)
        await session.commit()
