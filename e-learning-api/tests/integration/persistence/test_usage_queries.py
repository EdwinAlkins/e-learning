"""Tests d'intégration — journal et agrégats de consommation LLM."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from httpx import AsyncClient

from e_learning.domain.usage.entities import TokenUsage
from e_learning.domain.user.value_objects import UserId
from e_learning.infrastructure.persistence.usage.queries import SqlAlchemyUsageQueryService
from e_learning.infrastructure.persistence.usage.repository import (
    SqlAlchemyTokenUsageRepository,
)
from e_learning.infrastructure.persistence.user.models import UserModel


def _usage(user_id: Any, kind: str, model: str, prompt: int, completion: int, age: int):
    entry = TokenUsage.record(
        user_id=UserId(user_id) if user_id else None,
        kind=kind,
        model=model,
        prompt_tokens=prompt,
        completion_tokens=completion,
    )
    entry.created_at = datetime.now(UTC) - timedelta(days=age)
    return entry


async def test_usage_query_aggregates_window_and_all_time(app: Any) -> None:
    user_id = uuid4()
    other_id = uuid4()
    async with app.state.session_factory() as session:
        session.add_all([UserModel(id=user_id), UserModel(id=other_id)])
        await session.commit()

        repo = SqlAlchemyTokenUsageRepository(session)
        for entry in (
            _usage(user_id, TokenUsage.KIND_CHAT, "gpt-a", 100, 20, age=0),
            _usage(user_id, TokenUsage.KIND_CHAT, "gpt-a", 50, 10, age=0),
            _usage(user_id, TokenUsage.KIND_SUMMARY, "gpt-b", 1000, 200, age=2),
            _usage(user_id, TokenUsage.KIND_CHAT, "gpt-a", 7, 3, age=40),  # hors fenêtre
            _usage(other_id, TokenUsage.KIND_CHAT, "gpt-a", 999, 999, age=0),
            _usage(None, TokenUsage.KIND_SUMMARY, "gpt-b", 999, 999, age=0),
        ):
            await repo.add(entry)
        await session.commit()

        dto = await SqlAlchemyUsageQueryService(session).get_user_usage(
            user_id=str(user_id), days=7
        )

    assert dto.period.calls == 3
    assert dto.period.total_tokens == 1380
    assert dto.all_time.calls == 4
    assert dto.all_time.total_tokens == 1390
    assert [(b.key, b.totals.total_tokens) for b in dto.by_kind] == [
        ("summary", 1200),
        ("chat", 180),
    ]
    assert [b.key for b in dto.by_model] == ["gpt-b", "gpt-a"]
    assert len(dto.daily) == 7
    assert dto.daily[-1].day == datetime.now(UTC).date()
    assert dto.daily[-1].totals.total_tokens == 180
    assert dto.daily[-3].totals.total_tokens == 1200
    assert sum(d.totals.calls for d in dto.daily) == 3


async def test_usage_endpoint_requires_user_and_returns_empty_series(
    client: AsyncClient,
) -> None:
    assert (await client.get("/usage")).status_code == 401

    uid = (await client.post("/auth/generate")).json()["uid"]
    response = await client.get("/usage", params={"days": 14}, headers={"X-User-UID": uid})

    assert response.status_code == 200
    body = response.json()
    assert body["days"] == 14
    assert body["all_time"] == {
        "calls": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
    }
    assert len(body["daily"]) == 14
    assert body["by_kind"] == []
