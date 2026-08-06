"""Helpers tâches de fond — conversion média + IA + jobs."""

from __future__ import annotations

import asyncio
import logging

from fastapi import FastAPI

from e_learning.application.catalog.dto import MediaConversionJob
from e_learning.application.catalog.use_cases.complete_media_conversion import (
    CompleteMediaConversion,
)
from e_learning.application.catalog.use_cases.start_media_conversion import (
    conversion_job_from_staging,
)
from e_learning.application.content.dto import (
    GenerateSummaryCommand,
    IndexFormationCommand,
    IndexVideoCommand,
    TranscribeCommand,
)
from e_learning.application.content.use_cases.generate_summary import GenerateSummary
from e_learning.application.content.use_cases.index_formation import IndexFormation
from e_learning.application.content.use_cases.index_video_content import IndexVideoContent
from e_learning.application.content.use_cases.transcribe_video import TranscribeVideo
from e_learning.application.jobs.create_job import create_queued_job
from e_learning.domain.catalog.entities import Video
from e_learning.domain.catalog.job import Job
from e_learning.domain.catalog.value_objects import VideoId
from e_learning.infrastructure.ai.summary import GeminiSummaryAdapter, OpenAPISummaryAdapter
from e_learning.infrastructure.ai.whisper_transcription import WhisperTranscriptionAdapter
from e_learning.infrastructure.config import SummaryStrategyName
from e_learning.infrastructure.jobs.progress import (
    DbJobProgressReporter,
    mark_job_failed,
    mark_job_running,
    mark_job_succeeded,
)
from e_learning.infrastructure.persistence.catalog.repository import (
    SqlAlchemyChapterRepository,
    SqlAlchemyFormationRepository,
    SqlAlchemyJobRepository,
    SqlAlchemyVideoRepository,
)

logger = logging.getLogger("e_learning")

_DEFAULT_FFMPEG_CONCURRENCY = 2


async def run_media_conversion(app: FastAPI, job: MediaConversionJob) -> None:
    session_factory = app.state.session_factory
    storage = app.state.catalog_storage
    converter = app.state.media_converter
    sem: asyncio.Semaphore = app.state.media_conversion_semaphore
    job_id = job.job_id
    reporter: DbJobProgressReporter | None = None
    sync_cb = None

    logger.info(
        "Conversion média démarrée : %s (%s → %s, kind=%s, job=%s)",
        job.video_id,
        job.source_relative_path,
        job.target_relative_path,
        job.kind,
        job_id,
    )

    if job_id:
        await mark_job_running(session_factory, job_id, message="Conversion…")
        reporter = DbJobProgressReporter(session_factory, job_id)
        loop = asyncio.get_running_loop()
        sync_cb = reporter.as_sync_callback(loop)

    async with sem:
        async with session_factory() as session:
            try:
                use_case = CompleteMediaConversion(
                    SqlAlchemyVideoRepository(session),
                    storage,
                    converter,
                )
                await use_case.execute(job, on_progress=sync_cb)
                await session.commit()
                if job_id:
                    await mark_job_succeeded(session_factory, job_id, message="Conversion terminée")
                logger.info("Conversion média terminée : %s", job.video_id)
            except Exception as exc:
                await session.rollback()
                try:
                    async with session_factory() as session2:
                        videos2 = SqlAlchemyVideoRepository(session2)
                        video = await videos2.get(VideoId.from_string(job.video_id))
                        if video.processing_status == Video.STATUS_PROCESSING:
                            video.mark_failed()
                            await videos2.save(video)
                            await session2.commit()
                except Exception:
                    logger.exception("Impossible de marquer conversion failed : %s", job.video_id)
                if job_id:
                    await mark_job_failed(session_factory, job_id, str(exc))
                logger.exception("Échec conversion média en arrière-plan : %s", job.video_id)


async def resume_pending_media_conversions(app: FastAPI) -> None:
    """Reprend les conversions orphelines (ex. après redémarrage Docker)."""
    session_factory = app.state.session_factory
    jobs: list[MediaConversionJob] = []
    async with session_factory() as session:
        videos = SqlAlchemyVideoRepository(session)
        job_repo = SqlAlchemyJobRepository(session)
        for video in await videos.list_media_processing():
            existing = await job_repo.find_active(kind=Job.KIND_MEDIA_CONVERSION, video_id=video.id)
            job = conversion_job_from_staging(
                video_id=str(video.id),
                relative_path=str(video.relative_path),
                kind=video.kind,
                job_id=str(existing.id) if existing else None,
            )
            if job is None:
                logger.warning(
                    "Vidéo processing sans staging *.src.* — marquage failed : %s (%s)",
                    video.id,
                    video.relative_path,
                )
                video.mark_failed()
                await videos.save(video)
                if existing:
                    existing.mark_failed("Staging manquant après restart")
                    await job_repo.save(existing)
            else:
                if existing is None:
                    created = await create_queued_job(
                        job_repo,
                        kind=Job.KIND_MEDIA_CONVERSION,
                        video_id=str(video.id),
                        message="Reprise conversion",
                    )
                    job = MediaConversionJob(
                        video_id=job.video_id,
                        source_relative_path=job.source_relative_path,
                        target_relative_path=job.target_relative_path,
                        kind=job.kind,
                        job_id=created.id,
                    )
                jobs.append(job)
        await session.commit()

    if not jobs:
        return
    logger.info("Reprise de %s conversion(s) média en arrière-plan", len(jobs))
    for job in jobs:
        asyncio.create_task(run_media_conversion(app, job))


async def recover_stuck_ai_jobs(app: FastAPI) -> None:
    """Répare transcription/résumé restés en ``processing`` après un restart.

    Sidecar présent → ``ready`` ; sinon → ``failed`` + re-enqueue si job DB actif.
    """
    session_factory = app.state.session_factory
    media_files = app.state.media_files
    recovered = 0
    to_resume_tx: list[tuple[str, str]] = []
    to_resume_sum: list[tuple[str, str]] = []

    async with session_factory() as session:
        videos = SqlAlchemyVideoRepository(session)
        job_repo = SqlAlchemyJobRepository(session)

        for job in await job_repo.list_active():
            if job.kind not in (Job.KIND_TRANSCRIPTION, Job.KIND_SUMMARY):
                continue
            if job.video_id is None:
                job.mark_failed("Job sans video_id")
                await job_repo.save(job)
                recovered += 1
                continue
            video = await videos.get(job.video_id)
            relative = str(video.relative_path)
            if job.kind == Job.KIND_TRANSCRIPTION:
                if media_files.transcription_path(relative).is_file():
                    video.set_transcription_status(Video.AI_READY)
                    await videos.save(video)
                    job.mark_succeeded(message="Récupéré (sidecar présent)")
                    await job_repo.save(job)
                else:
                    to_resume_tx.append((str(video.id), str(job.id)))
            elif job.kind == Job.KIND_SUMMARY:
                if media_files.summary_path(relative).is_file():
                    video.set_summary_status(Video.AI_READY)
                    if video.transcription_status != Video.AI_READY:
                        if media_files.transcription_path(relative).is_file():
                            video.set_transcription_status(Video.AI_READY)
                    await videos.save(video)
                    job.mark_succeeded(message="Récupéré (sidecar présent)")
                    await job_repo.save(job)
                else:
                    to_resume_sum.append((str(video.id), str(job.id)))
            recovered += 1

        # Vidéos processing sans job actif (legacy)
        for video in await videos.list_ai_processing():
            changed = False
            if video.transcription_status == Video.AI_PROCESSING:
                active = await job_repo.find_active(kind=Job.KIND_TRANSCRIPTION, video_id=video.id)
                if active is None:
                    if media_files.transcription_path(str(video.relative_path)).is_file():
                        video.set_transcription_status(Video.AI_READY)
                    else:
                        video.set_transcription_status(Video.AI_FAILED)
                    changed = True
            if video.summary_status == Video.AI_PROCESSING:
                active = await job_repo.find_active(kind=Job.KIND_SUMMARY, video_id=video.id)
                if active is None:
                    if media_files.summary_path(str(video.relative_path)).is_file():
                        video.set_summary_status(Video.AI_READY)
                    else:
                        video.set_summary_status(Video.AI_FAILED)
                    changed = True
            if changed:
                await videos.save(video)
                recovered += 1

        await session.commit()

    if recovered:
        logger.info("Jobs IA stuck récupérés : %s action(s)", recovered)

    for video_id, job_id in to_resume_tx:
        asyncio.create_task(run_transcription(app, video_id, job_id))
    for video_id, job_id in to_resume_sum:
        asyncio.create_task(run_summary_generation(app, video_id, job_id))


async def resume_pending_background_jobs(app: FastAPI) -> None:
    """Au boot : conversions média + jobs IA stuck / reprise."""
    await resume_pending_media_conversions(app)
    await recover_stuck_ai_jobs(app)
    await recover_stuck_rag_jobs(app)


async def recover_stuck_rag_jobs(app: FastAPI) -> None:
    session_factory = app.state.session_factory
    async with session_factory() as session:
        job_repo = SqlAlchemyJobRepository(session)
        for job in await job_repo.list_active():
            if job.kind == Job.KIND_RAG_INDEX_VIDEO and job.video_id is not None:
                asyncio.create_task(run_index_video(app, str(job.video_id), str(job.id)))
            elif job.kind == Job.KIND_RAG_INDEX_FORMATION and job.formation_id is not None:
                asyncio.create_task(run_index_formation(app, str(job.formation_id), str(job.id)))
            elif job.kind in (Job.KIND_RAG_INDEX_VIDEO, Job.KIND_RAG_INDEX_FORMATION):
                job.mark_failed("Cible manquante")
                await job_repo.save(job)
        await session.commit()


async def run_index_video(app: FastAPI, video_id: str, job_id: str | None = None) -> None:
    """Indexation RAG best-effort (ne casse pas le job IA appelant)."""
    session_factory = app.state.session_factory
    settings = app.state.settings

    if job_id is None:
        async with session_factory() as session:
            job_dto = await create_queued_job(
                SqlAlchemyJobRepository(session),
                kind=Job.KIND_RAG_INDEX_VIDEO,
                video_id=video_id,
                message="Indexation RAG",
            )
            await session.commit()
            job_id = job_dto.id

    await mark_job_running(session_factory, job_id, message="Indexation RAG…")
    reporter = DbJobProgressReporter(session_factory, job_id)
    try:
        async with session_factory() as session:
            use_case = IndexVideoContent(
                SqlAlchemyVideoRepository(session),
                SqlAlchemyChapterRepository(session),
                SqlAlchemyFormationRepository(session),
                app.state.media_files,
                app.state.embeddings,
                app.state.vector_store,
                chunk_size=settings.rag_chunk_size,
                chunk_overlap=settings.rag_chunk_overlap,
            )
            n = await use_case.execute(IndexVideoCommand(video_id=video_id), progress=reporter)
            await session.commit()
            await mark_job_succeeded(session_factory, job_id, message=f"{n} chunk(s) indexés")
            logger.info("Index RAG vidéo %s : %s chunk(s)", video_id, n)
    except Exception as exc:
        await mark_job_failed(session_factory, job_id, str(exc))
        logger.exception("Échec indexation RAG (best-effort) : %s", video_id)


async def run_index_formation(app: FastAPI, formation_id: str, job_id: str | None = None) -> None:
    session_factory = app.state.session_factory
    settings = app.state.settings

    if job_id is None:
        async with session_factory() as session:
            job_dto = await create_queued_job(
                SqlAlchemyJobRepository(session),
                kind=Job.KIND_RAG_INDEX_FORMATION,
                formation_id=formation_id,
                message="Indexation formation",
            )
            await session.commit()
            job_id = job_dto.id

    await mark_job_running(session_factory, job_id, message="Indexation formation…")
    reporter = DbJobProgressReporter(session_factory, job_id)
    try:
        async with session_factory() as session:
            videos = SqlAlchemyVideoRepository(session)
            formations = SqlAlchemyFormationRepository(session)
            chapters = SqlAlchemyChapterRepository(session)
            index_video = IndexVideoContent(
                videos,
                chapters,
                formations,
                app.state.media_files,
                app.state.embeddings,
                app.state.vector_store,
                chunk_size=settings.rag_chunk_size,
                chunk_overlap=settings.rag_chunk_overlap,
            )
            result = await IndexFormation(formations, videos, index_video).execute(
                IndexFormationCommand(formation_id=formation_id),
                progress=reporter,
            )
            await session.commit()
            await mark_job_succeeded(
                session_factory,
                job_id,
                message=f"{result.indexed_videos} vidéo(s), {result.indexed_chunks} chunk(s)",
            )
            logger.info(
                "Index RAG formation %s : %s vidéo(s), %s chunk(s)",
                formation_id,
                result.indexed_videos,
                result.indexed_chunks,
            )
    except Exception as exc:
        await mark_job_failed(session_factory, job_id, str(exc))
        logger.exception("Échec indexation RAG formation : %s", formation_id)


async def run_transcription(app: FastAPI, video_id: str, job_id: str | None = None) -> None:
    session_factory = app.state.session_factory
    storage = app.state.catalog_storage
    media_files = app.state.media_files

    if job_id:
        await mark_job_running(session_factory, job_id, message="Transcription…")
        reporter = DbJobProgressReporter(session_factory, job_id)
    else:
        reporter = None

    async with session_factory() as session:
        videos = SqlAlchemyVideoRepository(session)
        try:
            use_case = TranscribeVideo(
                videos,
                storage,
                media_files,
                WhisperTranscriptionAdapter(),
            )
            await use_case.execute(TranscribeCommand(video_id=video_id), progress=reporter)
            video = await videos.get(VideoId.from_string(video_id))
            video.set_transcription_status(Video.AI_READY)
            await videos.save(video)
            await session.commit()
            if job_id:
                await mark_job_succeeded(session_factory, job_id, message="Transcription terminée")
            logger.info("Transcription terminée : %s", video_id)
        except Exception as exc:
            await session.rollback()
            try:
                async with session_factory() as session2:
                    videos2 = SqlAlchemyVideoRepository(session2)
                    video = await videos2.get(VideoId.from_string(video_id))
                    video.set_transcription_status(Video.AI_FAILED)
                    await videos2.save(video)
                    await session2.commit()
            except Exception:
                logger.exception("Impossible de marquer transcription failed : %s", video_id)
            if job_id:
                await mark_job_failed(session_factory, job_id, str(exc))
            logger.exception("Échec transcription en arrière-plan : %s", video_id)
            return
    await run_index_video(app, video_id)


async def run_summary_generation(app: FastAPI, video_id: str, job_id: str | None = None) -> None:
    session_factory = app.state.session_factory
    media_files = app.state.media_files
    settings = app.state.settings
    if settings.summary_strategy is SummaryStrategyName.GEMINI:
        summary_port = GeminiSummaryAdapter()
    else:
        summary_port = OpenAPISummaryAdapter(settings)

    if job_id:
        await mark_job_running(session_factory, job_id, message="Génération du résumé…")
        reporter = DbJobProgressReporter(session_factory, job_id)
    else:
        reporter = None

    async with session_factory() as session:
        videos = SqlAlchemyVideoRepository(session)
        try:
            use_case = GenerateSummary(videos, media_files, summary_port)
            await use_case.execute(GenerateSummaryCommand(video_id=video_id), progress=reporter)
            video = await videos.get(VideoId.from_string(video_id))
            video.set_summary_status(Video.AI_READY)
            if video.transcription_status != Video.AI_READY:
                video.set_transcription_status(Video.AI_READY)
            await videos.save(video)
            await session.commit()
            if job_id:
                await mark_job_succeeded(session_factory, job_id, message="Résumé terminé")
            logger.info("Résumé généré : %s", video_id)
        except Exception as exc:
            await session.rollback()
            try:
                async with session_factory() as session2:
                    videos2 = SqlAlchemyVideoRepository(session2)
                    video = await videos2.get(VideoId.from_string(video_id))
                    video.set_summary_status(Video.AI_FAILED)
                    await videos2.save(video)
                    await session2.commit()
            except Exception:
                logger.exception("Impossible de marquer summary failed : %s", video_id)
            if job_id:
                await mark_job_failed(session_factory, job_id, str(exc))
            logger.exception("Échec génération résumé en arrière-plan : %s", video_id)
            return
    await run_index_video(app, video_id)
