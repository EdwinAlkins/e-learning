"""Tests — journal de consommation LLM par utilisateur."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from e_learning.application.content.dto import AskFormationCommand, GenerateSummaryCommand
from e_learning.application.content.use_cases.ask_formation import AskFormation
from e_learning.application.content.use_cases.generate_summary import GenerateSummary
from e_learning.application.content.use_cases.start_summary_generation import (
    StartSummaryGeneration,
)
from e_learning.application.jobs.dto import ComputeJobMessage
from e_learning.application.shared.llm import LlmCompletion, LlmUsage
from e_learning.application.shared.media import SummaryPort
from e_learning.application.shared.rag import RagHit
from e_learning.domain.catalog.entities import Formation, Video
from e_learning.domain.catalog.job import Job
from e_learning.domain.catalog.value_objects import FormationName
from e_learning.domain.usage.entities import TokenUsage
from e_learning.domain.usage.exceptions import InvalidTokenCount, InvalidUsageKind
from e_learning.domain.user.value_objects import UserId
from e_learning.infrastructure.ai.usage import usage_from_response
from tests.unit.application._fakes import (
    FakeFormationRepository,
    FakeJobRepository,
    FakeTokenUsageRepository,
    FakeVideoRepository,
    RecordingPublisher,
)
from tests.unit.application.test_ai_jobs import FakeMediaFiles, _seed_ready_video
from tests.unit.application.test_rag import FakeChat, FakeEmbeddings, FakeVectors

USER_ID = str(UserId.generate())
USAGE = LlmUsage(model="gpt-test", prompt_tokens=120, completion_tokens=30)


class FakeSummary(SummaryPort):
    def __init__(self, usage: LlmUsage | None) -> None:
        self._usage = usage

    async def generate(self, transcription: str) -> LlmCompletion:
        return LlmCompletion(text=f"# Résumé\n{transcription}", usage=self._usage)


async def _ask(chat: FakeChat, usage: FakeTokenUsageRepository, user_id: str | None) -> None:
    formations = FakeFormationRepository()
    formation = Formation.create(name=FormationName("Algo"))
    await formations.save(formation)
    fid = str(formation.id)
    hit = RagHit(
        formation_id=fid,
        chapter_id="ch-1",
        title="Intro",
        source="transcription",
        chunk_index=0,
        text="Les bases.",
        score=0.9,
        video_id="vid-1",
    )
    await AskFormation(
        formations,
        FakeEmbeddings(),
        FakeVectors(hits=[hit], count=1),
        chat,
        usage,
        top_k=6,
    ).execute(AskFormationCommand(formation_id=fid, question="Quoi ?", user_id=user_id))


async def test_ask_formation_records_chat_usage_for_user() -> None:
    usage = FakeTokenUsageRepository()

    await _ask(FakeChat(usage=USAGE), usage, USER_ID)

    [entry] = usage.items
    assert str(entry.user_id) == USER_ID
    assert entry.kind == TokenUsage.KIND_CHAT
    assert entry.model == "gpt-test"
    assert entry.total_tokens == 150


async def test_ask_formation_skips_when_provider_reports_no_usage() -> None:
    usage = FakeTokenUsageRepository()

    await _ask(FakeChat(usage=None), usage, USER_ID)

    assert usage.items == []


async def test_generate_summary_records_usage_for_requester(tmp_path: Path) -> None:
    videos = FakeVideoRepository()
    media = FakeMediaFiles(tmp_path)
    video = await _seed_ready_video(videos, transcription_status=Video.AI_READY)
    media.write_text(media.transcription_path(str(video.relative_path)), "texte")
    usage = FakeTokenUsageRepository()

    await GenerateSummary(videos, media, FakeSummary(USAGE), usage).execute(
        GenerateSummaryCommand(video_id=str(video.id), user_id=USER_ID)
    )

    [entry] = usage.items
    assert str(entry.user_id) == USER_ID
    assert entry.kind == TokenUsage.KIND_SUMMARY


async def test_generate_summary_without_user_is_unattributed(tmp_path: Path) -> None:
    videos = FakeVideoRepository()
    media = FakeMediaFiles(tmp_path)
    video = await _seed_ready_video(videos, transcription_status=Video.AI_READY)
    media.write_text(media.transcription_path(str(video.relative_path)), "texte")
    usage = FakeTokenUsageRepository()

    await GenerateSummary(videos, media, FakeSummary(USAGE), usage).execute(
        GenerateSummaryCommand(video_id=str(video.id))
    )

    assert usage.items[0].user_id is None


async def test_start_summary_propagates_user_to_job_and_message(tmp_path: Path) -> None:
    videos = FakeVideoRepository()
    jobs = FakeJobRepository()
    publisher = RecordingPublisher()
    media = FakeMediaFiles(tmp_path)
    video = await _seed_ready_video(videos, transcription_status=Video.AI_READY)
    media.write_text(media.transcription_path(str(video.relative_path)), "tx")

    await StartSummaryGeneration(videos, media, jobs, publisher).execute(
        str(video.id), user_id=USER_ID
    )

    [job] = await jobs.list_active()
    assert str(job.user_id) == USER_ID
    assert publisher.published[0].user_id == USER_ID


def test_compute_job_message_roundtrips_user_id() -> None:
    message = ComputeJobMessage(job_id="1", kind=Job.KIND_SUMMARY, video_id="v1", user_id=USER_ID)
    assert ComputeJobMessage.from_dict(message.to_dict()).user_id == USER_ID
    legacy = {"job_id": "1", "kind": Job.KIND_SUMMARY, "video_id": "v1"}
    assert ComputeJobMessage.from_dict(legacy).user_id is None


def test_token_usage_rejects_negative_counts_and_unknown_kind() -> None:
    with pytest.raises(InvalidTokenCount):
        TokenUsage.record(
            user_id=None,
            kind=TokenUsage.KIND_CHAT,
            model="m",
            prompt_tokens=-1,
            completion_tokens=0,
        )
    with pytest.raises(InvalidUsageKind):
        TokenUsage.record(
            user_id=None, kind="embedding", model="m", prompt_tokens=0, completion_tokens=0
        )


def test_usage_from_response_reads_openai_usage_block() -> None:
    response = SimpleNamespace(
        model="gpt-real",
        usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5, total_tokens=15),
    )
    assert usage_from_response(response, fallback_model="cfg") == LlmUsage(
        model="gpt-real", prompt_tokens=10, completion_tokens=5
    )
    assert usage_from_response(SimpleNamespace(usage=None), fallback_model="cfg") is None
