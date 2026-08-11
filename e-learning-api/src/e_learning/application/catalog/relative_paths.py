"""Helpers pour réécrire les ``relative_path`` après renommage FS."""

from __future__ import annotations

from pathlib import PurePosixPath


def rewrite_path_prefix(relative_path: str, old_prefix: str, new_prefix: str) -> str | None:
    """Réécrit ``relative_path`` si son préfixe vaut ``old_prefix``, sinon ``None``."""
    parts = PurePosixPath(relative_path).parts
    old_parts = PurePosixPath(old_prefix).parts
    if not old_parts or parts[: len(old_parts)] != old_parts:
        return None
    return str(PurePosixPath(new_prefix, *parts[len(old_parts) :]))
