"""Handlers worker — exécution des jobs de calcul."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

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
from e_learning.application.content.use_cases.index_document_content import IndexDocumentContent
from e_learning.application.content.use_cases.index_formation import IndexFormation
from e_learning.application.content.use_cases.index_video_content import IndexVideoContent
from e_learning.application.content.use_cases.transcribe_video import TranscribeVideo
from e_learning.application.jobs.create_job import create_queued_job
from e_learning.application.jobs.dto import ComputeJobMessage
from e_learning.application.jobs.enqueue import publish_compute_job
from e_learning.application.shared.media import SummaryPort
from e_learning.application.shared.messaging import JobPublisherPort
from e_learning.domain.catalog.entities import Video
from e_learning.domain.catalog.job import Job
from e_learning.domain.catalog.value_objects import JobId, VideoId
from e_learning.infrastructure.ai.document_text import FilesystemDocumentTextExtractor
from e_learning.infrastructure.ai.summary import GeminiSummaryAdapter, OpenAPISummaryAdapter
from e_learning.infrastructure.ai.whisper_transcription import WhisperTranscriptionAdapter
from e_learning.infrastructure.config import Settings, SummaryStrategyName
from e_learning.infrastructure.jobs.progress import (
    DbJobProgressReporter,
    mark_job_failed,
    mark_job_running,
    mark_job_succeeded,
)
from e_learning.infrastructure.persistence.catalog.repository import (
    SqlAlchemyChapterRepository,
    SqlAlchemyDocumentRepository,
    SqlAlchemyFormationRepository,
    SqlAlchemyJobRepository,
    SqlAlchemyVideoRepository,
)

logger = logging.getLogger("e_learning.worker")


@dataclass(slots=True)
class WorkerDeps:
    session_factory: async_sessionmaker[AsyncSession]
    settings: Settings
    catalog_storage: Any
    media_files: Any
    media_converter: Any
    embeddings: Any
    vector_store: Any
    publisher: JobPublisherPort


Handler = Callable[[WorkerDeps, ComputeJobMessage], Awaitable[None]]


async def handle_media_conversion(deps: WorkerDeps, message: ComputeJobMessage) -> None:
    logger.info(
        "Handler media_conversion démarré job=%s video_id=%s",
        message.job_id,
        message.video_id,
    )
    if not message.video_id:
        raise ValueError("media_conversion sans video_id")

    session_factory = deps.session_factory
    job_id = message.job_id

    async with session_factory() as session:
        videos = SqlAlchemyVideoRepository(session)
        video = await videos.get(VideoId.from_string(message.video_id))
        job = conversion_job_from_staging(
            video_id=str(video.id),
            relative_path=str(video.relative_path),
            kind=video.kind,
            job_id=job_id,
        )
        if job is None:
            video.mark_failed()
            await videos.save(video)
            await session.commit()
            await mark_job_failed(session_factory, job_id, "Staging manquant")
            return

    await mark_job_running(session_factory, job_id, message="Conversion…")
    reporter = DbJobProgressReporter(session_factory, job_id)
    loop = asyncio.get_running_loop()
    sync_cb = reporter.as_sync_callback(loop)

    logger.info(
        "Conversion média démarrée : %s (%s → %s, job=%s)",
        job.video_id,
        job.source_relative_path,
        job.target_relative_path,
        job_id,
    )

    async with session_factory() as session:
        try:
            use_case = CompleteMediaConversion(
                SqlAlchemyVideoRepository(session),
                deps.catalog_storage,
                deps.media_converter,
            )
            await use_case.execute(job, on_progress=sync_cb)
            await session.commit()
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
            await mark_job_failed(session_factory, job_id, str(exc))
            logger.exception("Échec conversion média : %s", job.video_id)
            raise


async def handle_transcription(deps: WorkerDeps, message: ComputeJobMessage) -> None:
    logger.info(
        "Handler transcription démarré job=%s video_id=%s",
        message.job_id,
        message.video_id,
    )
    if not message.video_id:
        raise ValueError("transcription sans video_id")

    session_factory = deps.session_factory
    video_id = message.video_id
    job_id = message.job_id

    await mark_job_running(session_factory, job_id, message="Transcription…")
    reporter = DbJobProgressReporter(session_factory, job_id)

    async with session_factory() as session:
        videos = SqlAlchemyVideoRepository(session)
        try:
            use_case = TranscribeVideo(
                videos,
                deps.catalog_storage,
                deps.media_files,
                WhisperTranscriptionAdapter(),
            )
            await use_case.execute(TranscribeCommand(video_id=video_id), progress=reporter)
            video = await videos.get(VideoId.from_string(video_id))
            video.set_transcription_status(Video.AI_READY)
            await videos.save(video)
            await session.commit()
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
            await mark_job_failed(session_factory, job_id, str(exc))
            logger.exception("Échec transcription : %s", video_id)
            raise

    await _enqueue_rag_index_video(deps, video_id)


async def handle_summary(deps: WorkerDeps, message: ComputeJobMessage) -> None:
    logger.info(
        "Handler summary démarré job=%s video_id=%s",
        message.job_id,
        message.video_id,
    )
    if not message.video_id:
        raise ValueError("summary sans video_id")

    session_factory = deps.session_factory
    settings = deps.settings
    video_id = message.video_id
    job_id = message.job_id

    summary_port: SummaryPort
    if settings.summary_strategy is SummaryStrategyName.GEMINI:
        summary_port = GeminiSummaryAdapter()
    else:
        summary_port = OpenAPISummaryAdapter(settings)

    await mark_job_running(session_factory, job_id, message="Génération du résumé…")
    reporter = DbJobProgressReporter(session_factory, job_id)

    async with session_factory() as session:
        videos = SqlAlchemyVideoRepository(session)
        try:
            use_case = GenerateSummary(videos, deps.media_files, summary_port)
            await use_case.execute(GenerateSummaryCommand(video_id=video_id), progress=reporter)
            video = await videos.get(VideoId.from_string(video_id))
            video.set_summary_status(Video.AI_READY)
            if video.transcription_status != Video.AI_READY:
                video.set_transcription_status(Video.AI_READY)
            await videos.save(video)
            await session.commit()
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
            await mark_job_failed(session_factory, job_id, str(exc))
            logger.exception("Échec génération résumé : %s", video_id)
            raise

    await _enqueue_rag_index_video(deps, video_id)


async def handle_rag_index_video(deps: WorkerDeps, message: ComputeJobMessage) -> None:
    logger.info(
        "Handler rag_index_video démarré job=%s video_id=%s",
        message.job_id,
        message.video_id,
    )
    if not message.video_id:
        raise ValueError("rag_index_video sans video_id")

    session_factory = deps.session_factory
    settings = deps.settings
    video_id = message.video_id
    job_id = message.job_id

    await mark_job_running(session_factory, job_id, message="Indexation RAG…")
    reporter = DbJobProgressReporter(session_factory, job_id)
    try:
        async with session_factory() as session:
            use_case = IndexVideoContent(
                SqlAlchemyVideoRepository(session),
                SqlAlchemyChapterRepository(session),
                SqlAlchemyFormationRepository(session),
                deps.media_files,
                deps.embeddings,
                deps.vector_store,
                chunk_size=settings.rag_chunk_size,
                chunk_overlap=settings.rag_chunk_overlap,
            )
            n = await use_case.execute(IndexVideoCommand(video_id=video_id), progress=reporter)
            await session.commit()
            await mark_job_succeeded(session_factory, job_id, message=f"{n} chunk(s) indexés")
            logger.info("Index RAG vidéo %s : %s chunk(s)", video_id, n)
    except Exception as exc:
        await mark_job_failed(session_factory, job_id, str(exc))
        logger.exception("Échec indexation RAG : %s", video_id)
        raise


async def handle_rag_index_formation(deps: WorkerDeps, message: ComputeJobMessage) -> None:
    logger.info(
        "Handler rag_index_formation démarré job=%s formation_id=%s",
        message.job_id,
        message.formation_id,
    )
    if not message.formation_id:
        raise ValueError("rag_index_formation sans formation_id")

    session_factory = deps.session_factory
    settings = deps.settings
    formation_id = message.formation_id
    job_id = message.job_id

    await mark_job_running(session_factory, job_id, message="Indexation formation…")
    reporter = DbJobProgressReporter(session_factory, job_id)
    try:
        async with session_factory() as session:
            videos = SqlAlchemyVideoRepository(session)
            formations = SqlAlchemyFormationRepository(session)
            chapters = SqlAlchemyChapterRepository(session)
            documents = SqlAlchemyDocumentRepository(session)
            index_video = IndexVideoContent(
                videos,
                chapters,
                formations,
                deps.media_files,
                deps.embeddings,
                deps.vector_store,
                chunk_size=settings.rag_chunk_size,
                chunk_overlap=settings.rag_chunk_overlap,
            )
            index_document = IndexDocumentContent(
                documents,
                chapters,
                formations,
                deps.catalog_storage,
                FilesystemDocumentTextExtractor(),
                deps.embeddings,
                deps.vector_store,
                chunk_size=settings.rag_chunk_size,
                chunk_overlap=settings.rag_chunk_overlap,
            )
            result = await IndexFormation(
                formations, videos, chapters, documents, index_video, index_document
            ).execute(
                IndexFormationCommand(formation_id=formation_id),
                progress=reporter,
            )
            await session.commit()
            await mark_job_succeeded(
                session_factory,
                job_id,
                message=(
                    f"{result.indexed_videos} vidéo(s), "
                    f"{result.indexed_documents} doc(s), "
                    f"{result.indexed_chunks} chunk(s)"
                ),
            )
            logger.info(
                "Index RAG formation %s : %s vidéo(s), %s doc(s), %s chunk(s)",
                formation_id,
                result.indexed_videos,
                result.indexed_documents,
                result.indexed_chunks,
            )
    except Exception as exc:
        await mark_job_failed(session_factory, job_id, str(exc))
        logger.exception("Échec indexation RAG formation : %s", formation_id)
        raise


HANDLERS: dict[str, Handler] = {
    Job.KIND_MEDIA_CONVERSION: handle_media_conversion,
    Job.KIND_TRANSCRIPTION: handle_transcription,
    Job.KIND_SUMMARY: handle_summary,
    Job.KIND_RAG_INDEX_VIDEO: handle_rag_index_video,
    Job.KIND_RAG_INDEX_FORMATION: handle_rag_index_formation,
}


async def dispatch(deps: WorkerDeps, message: ComputeJobMessage) -> None:
    handler = HANDLERS.get(message.kind)
    if handler is None:
        raise ValueError(f"Kind de job inconnu : {message.kind}")
    logger.info(
        "Dispatch kind=%s → %s (job_id=%s)",
        message.kind,
        handler.__name__,
        message.job_id,
    )
    await handler(deps, message)


async def _enqueue_rag_index_video(deps: WorkerDeps, video_id: str) -> None:
    """Après TX/summary : crée un job RAG et le publie (best-effort)."""
    try:
        async with deps.session_factory() as session:
            job_repo = SqlAlchemyJobRepository(session)
            existing = await job_repo.find_active(
                kind=Job.KIND_RAG_INDEX_VIDEO,
                video_id=VideoId.from_string(video_id),
            )
            if existing is not None:
                await session.commit()
                logger.info(
                    "RAG déjà actif pour vidéo %s (job=%s) — skip enqueue",
                    video_id,
                    existing.id,
                )
                return
            job_dto = await create_queued_job(
                job_repo,
                kind=Job.KIND_RAG_INDEX_VIDEO,
                video_id=video_id,
                message="Indexation RAG",
            )
            await session.commit()
        logger.info("Enqueue RAG vidéo %s → job %s", video_id, job_dto.id)
        await publish_compute_job(deps.publisher, job_dto)
    except Exception:
        logger.exception("Échec enqueue RAG après job IA : %s", video_id)


async def ensure_job_exists(session_factory: async_sessionmaker[AsyncSession], job_id: str) -> Job:
    async with session_factory() as session:
        jobs = SqlAlchemyJobRepository(session)
        return await jobs.get(JobId.from_string(job_id))


async def recover_and_republish(deps: WorkerDeps) -> None:
    """Au boot worker : répare les jobs stuck et republie les actifs restants."""
    session_factory = deps.session_factory
    media_files = deps.media_files
    to_publish: list[ComputeJobMessage] = []

    async with session_factory() as session:
        videos = SqlAlchemyVideoRepository(session)
        job_repo = SqlAlchemyJobRepository(session)

        # Conversions orphelines sans staging
        for video in await videos.list_media_processing():
            existing = await job_repo.find_active(kind=Job.KIND_MEDIA_CONVERSION, video_id=video.id)
            conversion = conversion_job_from_staging(
                video_id=str(video.id),
                relative_path=str(video.relative_path),
                kind=video.kind,
                job_id=str(existing.id) if existing else None,
            )
            if conversion is None:
                logger.warning(
                    "Vidéo processing sans staging — marquage failed : %s",
                    video.id,
                )
                video.mark_failed()
                await videos.save(video)
                if existing:
                    existing.mark_failed("Staging manquant après restart")
                    await job_repo.save(existing)
            elif existing is None:
                created = await create_queued_job(
                    job_repo,
                    kind=Job.KIND_MEDIA_CONVERSION,
                    video_id=str(video.id),
                    message="Reprise conversion",
                )
                to_publish.append(
                    ComputeJobMessage(
                        job_id=created.id,
                        kind=Job.KIND_MEDIA_CONVERSION,
                        video_id=str(video.id),
                    )
                )

        # IA stuck : sidecar présent → succeeded ; sinon laisser actif pour republish
        for job in await job_repo.list_active():
            if job.kind not in (Job.KIND_TRANSCRIPTION, Job.KIND_SUMMARY):
                continue
            if job.video_id is None:
                job.mark_failed("Job sans video_id")
                await job_repo.save(job)
                continue
            video = await videos.get(job.video_id)
            relative = str(video.relative_path)
            if job.kind == Job.KIND_TRANSCRIPTION:
                if media_files.transcription_path(relative).is_file():
                    video.set_transcription_status(Video.AI_READY)
                    await videos.save(video)
                    job.mark_succeeded(message="Récupéré (sidecar présent)")
                    await job_repo.save(job)
            elif job.kind == Job.KIND_SUMMARY and media_files.summary_path(relative).is_file():
                video.set_summary_status(Video.AI_READY)
                if (
                    video.transcription_status != Video.AI_READY
                    and media_files.transcription_path(relative).is_file()
                ):
                    video.set_transcription_status(Video.AI_READY)
                await videos.save(video)
                job.mark_succeeded(message="Récupéré (sidecar présent)")
                await job_repo.save(job)

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

        for job in await job_repo.list_active():
            if job.kind in (Job.KIND_RAG_INDEX_VIDEO, Job.KIND_RAG_INDEX_FORMATION):
                if job.kind == Job.KIND_RAG_INDEX_VIDEO and job.video_id is None:
                    job.mark_failed("Cible manquante")
                    await job_repo.save(job)
                    continue
                if job.kind == Job.KIND_RAG_INDEX_FORMATION and job.formation_id is None:
                    job.mark_failed("Cible manquante")
                    await job_repo.save(job)
                    continue
            if job.status in Job.ACTIVE_STATUSES:
                # Remettre running → queued pour reprise propre
                if job.status == Job.STATUS_RUNNING:
                    job.status = Job.STATUS_QUEUED
                    job.message = "Reprise après restart"
                    job.started_at = None
                    await job_repo.save(job)
                to_publish.append(
                    ComputeJobMessage(
                        job_id=str(job.id),
                        kind=job.kind,
                        video_id=str(job.video_id) if job.video_id else None,
                        formation_id=str(job.formation_id) if job.formation_id else None,
                    )
                )

        await session.commit()

    # Dédupliquer par job_id
    seen: set[str] = set()
    unique: list[ComputeJobMessage] = []
    for msg in to_publish:
        if msg.job_id in seen:
            continue
        seen.add(msg.job_id)
        unique.append(msg)

    if not unique:
        logger.info("Aucun job actif à republier")
        return

    logger.info("Republication de %s job(s) actifs", len(unique))
    for msg in unique:
        logger.info(
            "Republication job=%s kind=%s video_id=%s formation_id=%s",
            msg.job_id,
            msg.kind,
            msg.video_id,
            msg.formation_id,
        )
        await deps.publisher.publish(msg)
