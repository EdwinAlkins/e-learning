"""Projections SQLAlchemy read-only de la consommation LLM."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.types import Date

from e_learning.application.usage.dto import (
    DailyTokenUsageDTO,
    TokenBreakdownDTO,
    TokenTotalsDTO,
    UserTokenUsageDTO,
)
from e_learning.application.usage.queries import UsageQueryPort
from e_learning.domain.user.exceptions import InvalidUserId
from e_learning.infrastructure.persistence.usage.models import TokenUsageModel

_TOTALS = (
    func.count(TokenUsageModel.id).label("calls"),
    func.coalesce(func.sum(TokenUsageModel.prompt_tokens), 0).label("prompt_tokens"),
    func.coalesce(func.sum(TokenUsageModel.completion_tokens), 0).label("completion_tokens"),
)


def _totals(row: Any) -> TokenTotalsDTO:
    return TokenTotalsDTO(
        calls=int(row.calls),
        prompt_tokens=int(row.prompt_tokens),
        completion_tokens=int(row.completion_tokens),
    )


class SqlAlchemyUsageQueryService(UsageQueryPort):
    """Agrégats calculés par PostgreSQL ; jours découpés en UTC."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_user_usage(self, *, user_id: str, days: int) -> UserTokenUsageDTO:
        try:
            uid = UUID(user_id)
        except ValueError as exc:
            raise InvalidUserId(user_id) from exc

        today = datetime.now(UTC).date()
        first_day = today - timedelta(days=days - 1)
        since = datetime.combine(first_day, time.min, tzinfo=UTC)
        of_user = TokenUsageModel.user_id == uid
        in_period = (of_user, TokenUsageModel.created_at >= since)

        all_time = (await self._session.execute(select(*_TOTALS).where(of_user))).one()
        period = (await self._session.execute(select(*_TOTALS).where(*in_period))).one()

        by_kind = await self._breakdown(TokenUsageModel.kind, in_period)
        by_model = await self._breakdown(TokenUsageModel.model, in_period)

        day_col = cast(func.timezone("UTC", TokenUsageModel.created_at), Date).label("day")
        daily_rows = (
            await self._session.execute(
                select(day_col, *_TOTALS).where(*in_period).group_by(day_col)
            )
        ).all()
        per_day: dict[date, TokenTotalsDTO] = {row.day: _totals(row) for row in daily_rows}
        daily = [
            DailyTokenUsageDTO(day=d, totals=per_day.get(d, TokenTotalsDTO()))
            for d in (first_day + timedelta(days=i) for i in range(days))
        ]

        return UserTokenUsageDTO(
            days=days,
            period=_totals(period),
            all_time=_totals(all_time),
            by_kind=by_kind,
            by_model=by_model,
            daily=daily,
        )

    async def _breakdown(self, column: Any, where: tuple[Any, ...]) -> list[TokenBreakdownDTO]:
        total = func.sum(TokenUsageModel.prompt_tokens) + func.sum(
            TokenUsageModel.completion_tokens
        )
        rows = (
            await self._session.execute(
                select(column.label("key"), *_TOTALS)
                .where(*where)
                .group_by(column)
                .order_by(total.desc())
            )
        ).all()
        return [TokenBreakdownDTO(key=row.key, totals=_totals(row)) for row in rows]
