"""Association document ↔ vidéo par similarité de nom normalisé."""

from __future__ import annotations

import re
from collections.abc import Sequence
from pathlib import PurePosixPath

from e_learning.domain.catalog.entities import Video

_ORDER_PREFIX = re.compile(r"^(\d+)[.\-_\s]+(.+)$")
_WHITESPACE = re.compile(r"\s+")


def strip_order_prefix(name: str) -> str:
    match = _ORDER_PREFIX.match(name)
    return match.group(2) if match else name


def normalize_media_name(name: str) -> str:
    """Retire le préfixe d'ordre, normalise casse et espaces."""
    stripped = strip_order_prefix(name.strip())
    return _WHITESPACE.sub(" ", stripped).casefold().strip()


def find_matching_video(videos: Sequence[Video], document_title_or_stem: str) -> Video | None:
    """Retourne la première vidéo du chapitre dont le titre/stem correspond."""
    key = normalize_media_name(document_title_or_stem)
    if not key:
        return None
    for video in videos:
        if normalize_media_name(str(video.title)) == key:
            return video
        if normalize_media_name(PurePosixPath(video.filename).stem) == key:
            return video
    return None
