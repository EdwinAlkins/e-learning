"""Adaptateur de publication de jobs via RabbitMQ."""

from __future__ import annotations

import logging
from types import TracebackType

import aio_pika
import orjson

from e_learning.application.jobs.dto import ComputeJobMessage
from e_learning.application.shared.messaging import JobPublisherPort

logger = logging.getLogger(__name__)

COMPUTE_QUEUE_NAME = "compute_jobs"
DLX_NAME = "compute_jobs.dlx"
DLQ_NAME = "compute_jobs.dlq"

ALL_ROUTING_KEYS = (
    "job.media_conversion",
    "job.transcription",
    "job.summary",
    "job.rag_index_video",
    "job.rag_index_formation",
)


class RabbitMQMessageAdapter(JobPublisherPort):
    """Adaptateur aio-pika pour publier des jobs de calcul."""

    def __init__(self, amqp_url: str, exchange_name: str = "elearning_jobs") -> None:
        self._amqp_url = amqp_url
        self._exchange_name = exchange_name
        self._connection: aio_pika.abc.AbstractRobustConnection | None = None
        self._channel: aio_pika.abc.AbstractChannel | None = None

    async def connect(self) -> None:
        self._connection = await aio_pika.connect_robust(self._amqp_url)
        self._channel = await self._connection.channel()
        await self._channel.declare_exchange(
            self._exchange_name, aio_pika.ExchangeType.DIRECT, durable=True
        )
        logger.info("Connecté à RabbitMQ (exchange=%s)", self._exchange_name)

    async def publish(self, message: ComputeJobMessage) -> None:
        if not self._channel:
            raise RuntimeError("RabbitMQ non connecté")
        exchange = await self._channel.get_exchange(self._exchange_name)
        body = orjson.dumps(message.to_dict())
        amqp_message = aio_pika.Message(
            body=body,
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            content_type="application/json",
        )
        await exchange.publish(amqp_message, routing_key=message.routing_key)
        logger.info(
            "Publié job %s kind=%s routing_key=%s video_id=%s formation_id=%s (%s octets)",
            message.job_id,
            message.kind,
            message.routing_key,
            message.video_id,
            message.formation_id,
            len(body),
        )

    async def close(self) -> None:
        if self._connection:
            await self._connection.close()
        self._connection = None
        self._channel = None
        logger.info("Déconnecté de RabbitMQ")

    async def __aenter__(self) -> RabbitMQMessageAdapter:
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.close()
