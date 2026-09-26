"""Schémas Pydantic — consommation LLM."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from e_learning.application.usage.dto import (
    TokenBreakdownDTO,
    TokenTotalsDTO,
    UserTokenUsageDTO,
)


class TokenTotalsResponse(BaseModel):
    calls: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    @classmethod
    def from_dto(cls, dto: TokenTotalsDTO) -> TokenTotalsResponse:
        return cls(
            calls=dto.calls,
            prompt_tokens=dto.prompt_tokens,
            completion_tokens=dto.completion_tokens,
            total_tokens=dto.total_tokens,
        )


class TokenBreakdownResponse(TokenTotalsResponse):
    key: str

    @classmethod
    def from_breakdown(cls, dto: TokenBreakdownDTO) -> TokenBreakdownResponse:
        totals = TokenTotalsResponse.from_dto(dto.totals)
        return cls(key=dto.key, **totals.model_dump())


class DailyTokenUsageResponse(TokenTotalsResponse):
    day: date


class UserTokenUsageResponse(BaseModel):
    days: int
    period: TokenTotalsResponse
    all_time: TokenTotalsResponse
    by_kind: list[TokenBreakdownResponse]
    by_model: list[TokenBreakdownResponse]
    daily: list[DailyTokenUsageResponse]

    @classmethod
    def from_dto(cls, dto: UserTokenUsageDTO) -> UserTokenUsageResponse:
        return cls(
            days=dto.days,
            period=TokenTotalsResponse.from_dto(dto.period),
            all_time=TokenTotalsResponse.from_dto(dto.all_time),
            by_kind=[TokenBreakdownResponse.from_breakdown(b) for b in dto.by_kind],
            by_model=[TokenBreakdownResponse.from_breakdown(b) for b in dto.by_model],
            daily=[
                DailyTokenUsageResponse(
                    day=d.day, **TokenTotalsResponse.from_dto(d.totals).model_dump()
                )
                for d in dto.daily
            ],
        )
