"""Exceptions de base du domaine (shared kernel)."""

from __future__ import annotations


class DomainError(Exception):
    """Erreur métier générique. Racine de toute exception du domaine."""


class ValidationError(DomainError):
    """Une invariante de value object n'est pas respectée."""


class NotFoundError(DomainError):
    """Une ressource référencée par son identité est introuvable."""


class ConflictError(DomainError):
    """L'opération viole une contrainte d'unicité ou d'état."""
