"""Point d'entrée du worker de jobs de calcul (consumer RabbitMQ)."""

from __future__ import annotations

import asyncio
import logging
import signal
import time

import aio_pika
import orjson

from e_learning.application.jobs.dto import ComputeJobMessage
from e_learning.domain.catalog.exceptions import JobNotFound
from e_learning.infrastructure.ai.embeddings import OpenAIEmbeddingAdapter
from e_learning.infrastructure.ai.media_files import FilesystemMediaFiles
from e_learning.infrastructure.ai.qdrant_store import QdrantVectorStore
from e_learning.infrastructure.config import get_settings
from e_learning.infrastructure.logging import configure_logging
from e_learning.infrastructure.media.ffmpeg_convert import FfmpegConvertAdapter
from e_learning.infrastructure.messaging.rabbitmq import (
    ALL_ROUTING_KEYS,
    COMPUTE_QUEUE_NAME,
    DLQ_NAME,
    DLX_NAME,
    RabbitMQMessageAdapter,
)
from e_learning.infrastructure.persistence.database import create_engine, create_session_factory
from e_learning.infrastructure.storage.filesystem_catalog import FilesystemCatalogStorage
from e_learning.presentation.worker.handlers import (
    WorkerDeps,
    dispatch,
    ensure_job_exists,
    recover_and_republish,
)

logger = logging.getLogger("e_learning.worker")


async def process_message(
    incoming: aio_pika.abc.AbstractIncomingMessage,
    deps: WorkerDeps,
) -> None:
    delivery_tag = incoming.delivery_tag
    routing_key = incoming.routing_key
    started = time.perf_counter()

    async with incoming.process(requeue=False):
        raw = incoming.body
        logger.info(
            "Message reçu delivery_tag=%s routing_key=%s size=%s octets redelivered=%s",
            delivery_tag,
            routing_key,
            len(raw),
            incoming.redelivered,
        )

        try:
            payload = orjson.loads(raw)
        except orjson.JSONDecodeError:
            logger.exception(
                "Payload JSON invalide delivery_tag=%s routing_key=%s",
                delivery_tag,
                routing_key,
            )
            raise

        try:
            message = ComputeJobMessage.from_dict(payload)
        except (ValueError, TypeError, KeyError):
            logger.exception(
                "Payload job invalide delivery_tag=%s routing_key=%s body=%s",
                delivery_tag,
                routing_key,
                payload,
            )
            raise

        logger.info(
            "Job décodé id=%s kind=%s video_id=%s formation_id=%s",
            message.job_id,
            message.kind,
            message.video_id,
            message.formation_id,
        )

        # Tolère un léger décalage commit API → consommation
        for attempt in range(5):
            try:
                await ensure_job_exists(deps.session_factory, message.job_id)
                if attempt > 0:
                    logger.info(
                        "Job %s trouvé en DB après %s tentative(s)",
                        message.job_id,
                        attempt + 1,
                    )
                break
            except JobNotFound:
                logger.warning(
                    "Job %s absent en DB (tentative %s/5) — attente commit API…",
                    message.job_id,
                    attempt + 1,
                )
                if attempt == 4:
                    logger.error(
                        "Job %s introuvable après retries — rejet DLQ",
                        message.job_id,
                    )
                    raise
                await asyncio.sleep(0.2 * (attempt + 1))

        logger.info("Exécution job %s (%s)…", message.job_id, message.kind)
        await dispatch(deps, message)
        elapsed_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "Job %s (%s) terminé avec succès en %.0f ms",
            message.job_id,
            message.kind,
            elapsed_ms,
        )


async def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    logger.info(
        "Démarrage worker — prefetch=%s exchange=%s queue=%s videos_path=%s",
        settings.worker_prefetch,
        settings.rabbitmq_exchange,
        COMPUTE_QUEUE_NAME,
        settings.videos_path,
    )

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    def _request_stop() -> None:
        logger.info("Signal d'arrêt reçu, arrêt du worker…")
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _request_stop)

    engine = create_engine(
        settings.database_url,
        echo=settings.echo_sql,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
    )
    session_factory = create_session_factory(engine)
    catalog_storage = FilesystemCatalogStorage(settings.videos_path)
    media_files = FilesystemMediaFiles(settings.videos_path)
    media_converter = FfmpegConvertAdapter()
    embeddings = OpenAIEmbeddingAdapter(settings)
    vector_store = QdrantVectorStore(settings)
    publisher = RabbitMQMessageAdapter(
        settings.rabbitmq_url.get_secret_value(),
        exchange_name=settings.rabbitmq_exchange,
    )
    await publisher.connect()
    logger.info("Publisher RabbitMQ prêt")

    deps = WorkerDeps(
        session_factory=session_factory,
        settings=settings,
        catalog_storage=catalog_storage,
        media_files=media_files,
        media_converter=media_converter,
        embeddings=embeddings,
        vector_store=vector_store,
        publisher=publisher,
    )

    connection = await aio_pika.connect_robust(settings.rabbitmq_url.get_secret_value())
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=settings.worker_prefetch)
    logger.info("QoS prefetch_count=%s", settings.worker_prefetch)

    exchange = await channel.declare_exchange(
        settings.rabbitmq_exchange, aio_pika.ExchangeType.DIRECT, durable=True
    )
    dlx = await channel.declare_exchange(DLX_NAME, aio_pika.ExchangeType.FANOUT, durable=True)
    dlq = await channel.declare_queue(DLQ_NAME, durable=True)
    await dlq.bind(dlx)
    queue = await channel.declare_queue(
        COMPUTE_QUEUE_NAME,
        durable=True,
        arguments={"x-dead-letter-exchange": DLX_NAME},
    )
    for routing_key in ALL_ROUTING_KEYS:
        await queue.bind(exchange, routing_key=routing_key)
        logger.debug("Bind queue %s ← %s", COMPUTE_QUEUE_NAME, routing_key)

    logger.info(
        "Topologie prête : exchange=%s queue=%s dlq=%s keys=%s",
        settings.rabbitmq_exchange,
        COMPUTE_QUEUE_NAME,
        DLQ_NAME,
        ", ".join(ALL_ROUTING_KEYS),
    )

    logger.info("Recovery des jobs DB actifs…")
    await recover_and_republish(deps)
    logger.info("Recovery terminée")

    async def wrapper(incoming: aio_pika.abc.AbstractIncomingMessage) -> None:
        try:
            await process_message(incoming, deps)
        except Exception:
            logger.exception(
                "Échec traitement message delivery_tag=%s routing_key=%s — rejet vers DLQ",
                incoming.delivery_tag,
                incoming.routing_key,
            )
            raise

    consumer_tag = await queue.consume(wrapper)
    logger.info(
        "Worker en écoute (prefetch=%s, queue=%s, consumer_tag=%s)…",
        settings.worker_prefetch,
        COMPUTE_QUEUE_NAME,
        consumer_tag,
    )

    try:
        await stop_event.wait()
    finally:
        logger.info("Arrêt en cours (cancel consumer, fermeture connexions)…")
        await queue.cancel(consumer_tag)
        await publisher.close()
        await connection.close()
        await engine.dispose()
        logger.info("Worker arrêté proprement")


def run() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    run()
