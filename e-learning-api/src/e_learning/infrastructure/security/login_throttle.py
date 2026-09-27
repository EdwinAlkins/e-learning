"""Adaptateur LoginThrottle — fenêtre glissante en mémoire du process."""

from __future__ import annotations

import time
from collections import deque
from collections.abc import Callable, Sequence

from e_learning.application.user.ports import LoginThrottle


class InMemoryLoginThrottle(LoginThrottle):
    """Compteurs locaux au process.

    Note — stratégie selon le déploiement. Le port ``LoginThrottle``
    (``retry_after``, ``record_failure``, ``reset``) ne change pas ;
    seul l'adaptateur change.

    - Un processus HTTP (Compose actuel : un service ``api``, Hypercorn
      sans ``--workers``). Cet adaptateur suffit. ``worker``, ``migrate``
      et ``front`` ne traitent pas le login ; ``APP_WORKER_PREFETCH``
      règle la concurrence des jobs, pas les processus HTTP.
    - Plusieurs workers Hypercorn (``--workers``) ou plusieurs répliques
      du service ``api``. Chaque processus a son compteur, le plafond
      d'échecs est multiplié par leur nombre. Remplacer cet adaptateur
      par un stockage partagé : Redis via ``limits``
      (``MovingWindowRateLimiter``) ou Postgres. Un limiteur de route
      (SlowAPI, fastapi-limiter) ne convient pas : il compte chaque
      requête, pas seulement les échecs, et ne réinitialise pas
      uniquement la clé email.
    """

    def __init__(
        self,
        *,
        max_failures: int,
        window_seconds: int,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._max_failures = max_failures
        self._window = window_seconds
        self._clock = clock
        self._failures: dict[str, deque[float]] = {}

    def _prune(self, key: str, now: float) -> deque[float] | None:
        failures = self._failures.get(key)
        if failures is None:
            return None
        while failures and failures[0] <= now - self._window:
            failures.popleft()
        if not failures:
            del self._failures[key]
            return None
        return failures

    async def retry_after(self, keys: Sequence[str]) -> int | None:
        now = self._clock()
        waits: list[float] = []
        for key in keys:
            failures = self._prune(key, now)
            if failures is not None and len(failures) >= self._max_failures:
                # Débloqué quand l'échec le plus ancien encore compté sort de la fenêtre.
                waits.append(failures[-self._max_failures] + self._window - now)
        if not waits:
            return None
        return max(1, int(max(waits)) + 1)

    async def record_failure(self, keys: Sequence[str]) -> None:
        now = self._clock()
        for key in keys:
            self._prune(key, now)
            self._failures.setdefault(key, deque()).append(now)

    async def reset(self, key: str) -> None:
        self._failures.pop(key, None)
