"""Parsing des en-têtes HTTP Range (bytes)."""

from __future__ import annotations


def parse_bytes_range(range_header: str, file_size: int) -> tuple[int, int] | None:
    """Parse ``bytes=start-end`` ; retourne (start, end) inclusifs ou ``None`` → 416."""
    if not range_header.startswith("bytes="):
        return None
    try:
        start_s, _, end_s = range_header.removeprefix("bytes=").partition("-")
        start = int(start_s) if start_s else 0
        end = int(end_s) if end_s else file_size - 1
    except ValueError:
        return None
    if file_size == 0 or start < 0 or start >= file_size or start > end:
        return None
    return start, min(end, file_size - 1)
