"""Injection du publisher de jobs."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from e_learning.application.shared.messaging import JobPublisherPort
from e_learning.infrastructure.messaging.deferred import DeferredJobPublisher


def get_job_publisher(request: Request) -> JobPublisherPort:
    """Publisher différé par requête : flush après commit session."""
    existing = getattr(request.state, "deferred_publisher", None)
    if existing is not None:
        return existing
    inner: JobPublisherPort = request.app.state.job_publisher
    deferred = DeferredJobPublisher(inner)
    request.state.deferred_publisher = deferred
    return deferred


JobPublisherDep = Annotated[JobPublisherPort, Depends(get_job_publisher)]
