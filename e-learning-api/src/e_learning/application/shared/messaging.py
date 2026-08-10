"""Port de publication de jobs vers un broker de messages asynchrone."""

from __future__ import annotations

from abc import ABC, abstractmethod

from e_learning.application.jobs.dto import ComputeJobMessage


class JobPublisherPort(ABC):
    """Contrat fonctionnel de publication ; l'adaptateur gère son propre cycle de vie.

    Le port n'expose que ``publish`` avec un ``ComputeJobMessage`` validé :
    ``connect`` / ``close`` et la sérialisation JSON sont des détails
    d'infrastructure.
    """

    @abstractmethod
    async def publish(self, message: ComputeJobMessage) -> None: ...
