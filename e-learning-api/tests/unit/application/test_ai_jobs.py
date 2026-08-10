"""Tests — jobs transcription / résumé asynchrones."""

from __future__ import annotations

from pathlib import Path

import pytest

from e_learning.application.content.dto import TranscribeCommand, UpdateSummaryCommand
from e_learning.application.content.use_cases.start_summary_generation import (
    StartSummaryGeneration,
)
from e_learning.application.content.use_cases.start_transcription import StartTranscription
from e_learning.application.content.use_cases.transcribe_video import TranscribeVideo
from e_learning.application.content.use_cases.update_summary import UpdateSummary
from e_learning.application.shared.media import MediaFilePort, TranscriptionPort
from e_learning.domain.catalog.entities import Chapter, Formation, Video
from e_learning.domain.catalog.exceptions import (
    AiJobConflict,
    MediaNotReady,
    TranscriptionNotReady,
)
from e_learning.domain.catalog.value_objects import (
    ChapterName,
    DurationSeconds,
    FormationName,
    Position,
    RelativePath,
    VideoTitle,
)
from tests.unit.application._fakes import FakeJobRepository, FakeVideoRepository, RecordingPublisher
from tests.unit.application.test_use_cases import FakeCatalogStorage


class FakeMediaFiles(MediaFilePort):
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def summary_path(self, video_relative_path: str) -> Path:
        return self.root / Path(video_relative_path).with_suffix(".md")

    def transcription_path(self, video_relative_path: str) -> Path:
        return self.root / Path(video_relative_path).with_suffix(".txt")

    def read_text(self, path: Path) -> str | None:
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    def write_text(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


class FakeTranscription(TranscriptionPort):
    def __init__(self, text: str = "hello world") -> None:
        self.text = text
        self.calls: list[Path] = []

    async def transcribe(
        self,
        video_path: Path,
        *,
        model: str = "base",
        language: str | None = None,
        with_timecodes: bool = False,
    ) -> str:
        self.calls.append(video_path)
        return self.text


async def _seed_ready_video(
    videos: FakeVideoRepository,
    *,
    processing_status: str = Video.STATUS_READY,
    transcription_status: str = Video.AI_NONE,
    summary_status: str = Video.AI_NONE,
    relative_path: str = "formation/chapitre/intro.mp4",
) -> Video:
    formation = Formation.create(name=FormationName("Formation Test"))
    chapter = Chapter.create(
        formation_id=formation.id,
        name=ChapterName("Chapitre 1"),
        position=Position(0),
    )
    video = Video.create(
        chapter_id=chapter.id,
        title=VideoTitle("Intro"),
        filename="intro.mp4",
        relative_path=RelativePath(relative_path),
        position=Position(0),
        duration=DurationSeconds(10),
        processing_status=processing_status,
        transcription_status=transcription_status,
        summary_status=summary_status,
    )
    await videos.save(video)
    return video


async def test_start_transcription_sets_processing(tmp_path: Path) -> None:
    videos = FakeVideoRepository()
    media = FakeMediaFiles(tmp_path)
    video = await _seed_ready_video(videos)

    dto = await StartTranscription(videos, media, FakeJobRepository(), RecordingPublisher()).execute(str(video.id))

    assert dto.transcription_status == Video.AI_PROCESSING
    stored = await videos.get(video.id)
    assert stored.transcription_status == Video.AI_PROCESSING


async def test_start_transcription_skips_when_txt_exists(tmp_path: Path) -> None:
    videos = FakeVideoRepository()
    media = FakeMediaFiles(tmp_path)
    video = await _seed_ready_video(videos)
    media.write_text(media.transcription_path(str(video.relative_path)), "déjà là")

    dto = await StartTranscription(videos, media, FakeJobRepository(), RecordingPublisher()).execute(str(video.id))

    assert dto.transcription_status == Video.AI_READY
    assert (await videos.get(video.id)).transcription_status == Video.AI_READY


async def test_start_transcription_conflict_when_already_processing(tmp_path: Path) -> None:
    videos = FakeVideoRepository()
    media = FakeMediaFiles(tmp_path)
    video = await _seed_ready_video(videos, transcription_status=Video.AI_PROCESSING)

    with pytest.raises(AiJobConflict):
        await StartTranscription(videos, media, FakeJobRepository(), RecordingPublisher()).execute(str(video.id))


async def test_start_transcription_requires_media_ready(tmp_path: Path) -> None:
    videos = FakeVideoRepository()
    media = FakeMediaFiles(tmp_path)
    video = await _seed_ready_video(videos, processing_status=Video.STATUS_PROCESSING)

    with pytest.raises(MediaNotReady):
        await StartTranscription(videos, media, FakeJobRepository(), RecordingPublisher()).execute(str(video.id))


async def test_start_summary_without_transcription_raises(tmp_path: Path) -> None:
    videos = FakeVideoRepository()
    media = FakeMediaFiles(tmp_path)
    video = await _seed_ready_video(videos)

    with pytest.raises(TranscriptionNotReady):
        await StartSummaryGeneration(videos, media, FakeJobRepository(), RecordingPublisher()).execute(str(video.id))


async def test_start_summary_sets_processing_when_transcription_ready(tmp_path: Path) -> None:
    videos = FakeVideoRepository()
    media = FakeMediaFiles(tmp_path)
    video = await _seed_ready_video(videos, transcription_status=Video.AI_READY)
    media.write_text(media.transcription_path(str(video.relative_path)), "texte")

    dto = await StartSummaryGeneration(videos, media, FakeJobRepository(), RecordingPublisher()).execute(str(video.id))

    assert dto.summary_status == Video.AI_PROCESSING


async def test_transcribe_video_writes_sidecar_and_marks_ready(tmp_path: Path) -> None:
    """Simule le runner : TranscribeVideo puis statut ready."""
    videos = FakeVideoRepository()
    storage = FakeCatalogStorage(tmp_path)
    media = FakeMediaFiles(tmp_path)
    transcription = FakeTranscription("contenu transcript")

    relative = "formation/chapitre/intro.mp4"
    abs_path = storage.absolute_path(relative)
    abs_path.parent.mkdir(parents=True, exist_ok=True)
    abs_path.write_bytes(b"fake-video")

    video = await _seed_ready_video(
        videos,
        relative_path=relative,
        transcription_status=Video.AI_PROCESSING,
    )

    text = await TranscribeVideo(videos, storage, media, transcription).execute(
        TranscribeCommand(video_id=str(video.id))
    )
    assert text == "contenu transcript"

    out = media.transcription_path(relative)
    assert out.exists()
    assert out.read_text(encoding="utf-8") == "contenu transcript"

    video = await videos.get(video.id)
    video.set_transcription_status(Video.AI_READY)
    await videos.save(video)
    assert (await videos.get(video.id)).transcription_status == Video.AI_READY


async def test_update_summary_creates_md_if_absent(tmp_path: Path) -> None:
    videos = FakeVideoRepository()
    media = FakeMediaFiles(tmp_path)
    video = await _seed_ready_video(videos)

    dto = await UpdateSummary(videos, media).execute(
        UpdateSummaryCommand(video_id=str(video.id), summary="Résumé manuel")
    )

    assert dto.summary == "Résumé manuel"
    path = media.summary_path(str(video.relative_path))
    assert path.exists()
    assert path.read_text(encoding="utf-8") == "Résumé manuel"


async def test_start_summary_syncs_when_md_exists_without_llm(tmp_path: Path) -> None:
    videos = FakeVideoRepository()
    media = FakeMediaFiles(tmp_path)
    video = await _seed_ready_video(videos)
    media.write_text(media.transcription_path(str(video.relative_path)), "tx")
    media.write_text(media.summary_path(str(video.relative_path)), "# Résumé")

    dto = await StartSummaryGeneration(videos, media, FakeJobRepository(), RecordingPublisher()).execute(str(video.id))

    assert dto.summary_status == Video.AI_READY
    assert dto.transcription_status == Video.AI_READY


async def test_start_summary_heals_processing_when_md_exists(tmp_path: Path) -> None:
    """DB processing + .md déjà là → ready (pas de conflit, pas de re-job)."""
    videos = FakeVideoRepository()
    media = FakeMediaFiles(tmp_path)
    video = await _seed_ready_video(
        videos,
        transcription_status=Video.AI_READY,
        summary_status=Video.AI_PROCESSING,
    )
    media.write_text(media.transcription_path(str(video.relative_path)), "tx")
    media.write_text(media.summary_path(str(video.relative_path)), "# Résumé")

    dto = await StartSummaryGeneration(videos, media, FakeJobRepository(), RecordingPublisher()).execute(str(video.id))

    assert dto.summary_status == Video.AI_READY
    assert (await videos.get(video.id)).summary_status == Video.AI_READY


async def test_start_summary_rejects_ready_without_txt_file(tmp_path: Path) -> None:
    """Statut ready fantôme (sidecar perdu / resté en *.src.txt) → TranscriptionNotReady."""
    videos = FakeVideoRepository()
    media = FakeMediaFiles(tmp_path)
    video = await _seed_ready_video(videos, transcription_status=Video.AI_READY)

    with pytest.raises(TranscriptionNotReady):
        await StartSummaryGeneration(videos, media, FakeJobRepository(), RecordingPublisher()).execute(str(video.id))

    assert (await videos.get(video.id)).transcription_status == Video.AI_NONE
