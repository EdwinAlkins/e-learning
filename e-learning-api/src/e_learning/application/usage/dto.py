"""DTO — contexte ``usage``."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class TokenTotalsDTO:
    calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@dataclass(frozen=True, slots=True)
class TokenBreakdownDTO:
    key: str
    totals: TokenTotalsDTO


@dataclass(frozen=True, slots=True)
class DailyTokenUsageDTO:
    day: date
    totals: TokenTotalsDTO


@dataclass(frozen=True, slots=True)
class UserTokenUsageDTO:
    """Consommation d'un utilisateur : fenêtre de ``days`` jours + cumul global."""

    days: int
    period: TokenTotalsDTO
    all_time: TokenTotalsDTO
    by_kind: list[TokenBreakdownDTO]
    by_model: list[TokenBreakdownDTO]
    daily: list[DailyTokenUsageDTO]
