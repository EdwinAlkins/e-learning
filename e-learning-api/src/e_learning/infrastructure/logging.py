"""Configuration du logging applicatif."""

from __future__ import annotations

import logging

from e_learning.infrastructure.config import LogLevel


def configure_logging(level: LogLevel) -> None:
    logging.basicConfig(
        level=level.value,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
