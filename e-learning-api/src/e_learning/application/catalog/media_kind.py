"""Classification média (audio vs vidéo) et extensions."""

from __future__ import annotations

from pathlib import PurePosixPath

from e_learning.domain.catalog.entities import Video
from e_learning.domain.catalog.exceptions import UnsupportedFileExtension

AUDIO_EXTS = frozenset({".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".wma", ".opus"})
VIDEO_EXTS = frozenset({".mp4", ".webm", ".mkv", ".avi", ".mov", ".m4v", ".wmv", ".flv"})
MEDIA_EXTS = AUDIO_EXTS | VIDEO_EXTS


def normalize_media_extension(filename: str) -> str:
    return PurePosixPath(filename).suffix.lower()


def assert_allowed_media_extension(filename: str) -> str:
    """Valide l'extension média ; lève ``UnsupportedFileExtension`` sinon."""
    ext = normalize_media_extension(filename)
    if not ext or ext not in MEDIA_EXTS:
        raise UnsupportedFileExtension(filename or "(sans nom)", allowed=MEDIA_EXTS)
    return ext


def classify_media_kind(filename: str) -> str:
    suffix = assert_allowed_media_extension(filename)
    if suffix in AUDIO_EXTS:
        return Video.KIND_AUDIO
    return Video.KIND_VIDEO


def target_extension(kind: str) -> str:
    return ".mp3" if kind == Video.KIND_AUDIO else ".mp4"


def needs_auto_conversion(filename: str, kind: str) -> bool:
    """True si le conteneur n'est pas déjà le format cible (mp4 / mp3).

    On ne regarde **pas** les codecs : un MP4 HEVC ou un MP3 exotique
    reste accepté à l'upload ; la conversion manuelle reste possible au studio.
    """
    suffix = normalize_media_extension(filename)
    return suffix != target_extension(kind)


def source_staging_filename(stem: str, original_filename: str) -> str:
    suffix = assert_allowed_media_extension(original_filename)
    return f"{stem}.src{suffix}"
