"""Erreurs techniques (hors domaine métier) et not-found applicatifs."""

from __future__ import annotations

from e_learning.domain.shared.exceptions import NotFoundError


class InfrastructureError(Exception):
    """Dépendance technique indisponible ou en échec."""


class StorageError(InfrastructureError):
    """Erreur d'accès au système de fichiers."""


class TranscriptionError(InfrastructureError):
    """Échec de transcription."""


class SummaryGenerationError(InfrastructureError):
    """Échec de génération de résumé."""


class MediaConversionError(InfrastructureError):
    """Échec de conversion média."""


class RagError(InfrastructureError):
    """Échec RAG (embeddings, Qdrant, chat)."""


class RagEmptyIndexError(RagError):
    """Aucun chunk indexé pour la formation demandée."""


class SummaryNotFound(NotFoundError):
    """Fichier résumé (.md) introuvable pour une vidéo existante."""


class TranscriptionNotFound(NotFoundError):
    """Fichier transcription (.txt) introuvable pour une vidéo existante."""
