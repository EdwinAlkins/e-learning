"""Whitelist d'extensions pour les documents annexes."""

from __future__ import annotations

from pathlib import PurePosixPath

from e_learning.domain.catalog.exceptions import UnsupportedFileExtension

# Aligné avec le studio front + formats e-learning courants (pas d'exécutables).
DOCUMENT_EXTS = frozenset(
    {
        ".pdf",
        ".md",
        ".txt",
        ".csv",
        ".doc",
        ".docx",
        ".ppt",
        ".pptx",
        ".xls",
        ".xlsx",
        ".odt",
        ".ods",
        ".odp",
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
        ".gif",
        ".svg",
    }
)


def normalize_extension(filename: str) -> str:
    """Retourne le suffixe lower-case (ex. ``.pdf``) ou ``""`` si absent."""
    return PurePosixPath(filename).suffix.lower()


def assert_allowed_document_extension(filename: str) -> str:
    """Valide l'extension ; lève ``UnsupportedFileExtension`` sinon.

    Retourne le suffixe normalisé (toujours non vide).
    """
    ext = normalize_extension(filename)
    if not ext or ext not in DOCUMENT_EXTS:
        raise UnsupportedFileExtension(filename or "(sans nom)", allowed=DOCUMENT_EXTS)
    return ext
