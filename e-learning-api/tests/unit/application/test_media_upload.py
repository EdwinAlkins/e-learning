"""Tests — upload média audio/vidéo + conversion différée."""

from __future__ import annotations

from pathlib import Path

from e_learning.application.catalog.dto import CreateVideoCommand
from e_learning.application.catalog.media_kind import classify_media_kind, needs_auto_conversion
from e_learning.application.catalog.use_cases.create_video import CreateVideo
from e_learning.domain.catalog.entities import Chapter, Formation, Video
from e_learning.domain.catalog.value_objects import (
    ChapterName,
    FormationName,
    Position,
)
from tests.unit.application._fakes import (
    FakeChapterRepository,
    FakeFormationRepository,
    FakeJobRepository,
    FakeVideoRepository,
)
from tests.unit.application.test_use_cases import FakeCatalogStorage


def test_classify_media_kind() -> None:
    assert classify_media_kind("track.mp3") == Video.KIND_AUDIO
    assert classify_media_kind("clip.wav") == Video.KIND_AUDIO
    assert classify_media_kind("lesson.mp4") == Video.KIND_VIDEO
    assert classify_media_kind("lesson.mkv") == Video.KIND_VIDEO


def test_needs_auto_conversion_by_container_only() -> None:
    assert needs_auto_conversion("clip.mp4", Video.KIND_VIDEO) is False
    assert needs_auto_conversion("clip.mkv", Video.KIND_VIDEO) is True
    assert needs_auto_conversion("track.mp3", Video.KIND_AUDIO) is False
    assert needs_auto_conversion("track.wav", Video.KIND_AUDIO) is True


def test_conversion_job_from_staging() -> None:
    from e_learning.application.catalog.use_cases.start_media_conversion import (
        conversion_job_from_staging,
    )

    job = conversion_job_from_staging(
        video_id="vid-1",
        relative_path="f/c/enquete.src.mp4",
        kind="video",
    )
    assert job is not None
    assert job.source_relative_path == "f/c/enquete.src.mp4"
    assert job.target_relative_path == "f/c/enquete.mp4"
    assert job.kind == "video"
    assert (
        conversion_job_from_staging(video_id="vid-1", relative_path="f/c/enquete.mp4", kind="video")
        is None
    )


async def test_create_mp4_skips_conversion(tmp_path: Path) -> None:
    """Un .mp4 est accepté tel quel à l'upload (pas de probe codec)."""
    formations = FakeFormationRepository()
    chapters = FakeChapterRepository()
    videos = FakeVideoRepository()
    storage = FakeCatalogStorage(tmp_path)

    formation = Formation.create(name=FormationName("Formation Test"))
    await formations.save(formation)
    chapter = Chapter.create(
        formation_id=formation.id,
        name=ChapterName("Chapitre 1"),
        position=Position(0),
    )
    await chapters.save(chapter)

    result = await CreateVideo(formations, chapters, videos, storage, FakeJobRepository()).execute(
        CreateVideoCommand(
            chapter_id=str(chapter.id),
            title="Intro",
            file_bytes=b"fake-mp4",
            filename="intro.mp4",
        )
    )
    assert result.conversion is None
    assert result.video.kind == "video"
    assert result.video.processing_status == "ready"
    assert result.video.relative_path.endswith(".mp4")


async def test_create_audio_wav_enqueues_conversion(tmp_path: Path) -> None:
    formations = FakeFormationRepository()
    chapters = FakeChapterRepository()
    videos = FakeVideoRepository()
    storage = FakeCatalogStorage(tmp_path)

    formation = Formation.create(name=FormationName("Formation Test"))
    await formations.save(formation)
    chapter = Chapter.create(
        formation_id=formation.id,
        name=ChapterName("Chapitre 1"),
        position=Position(0),
    )
    await chapters.save(chapter)

    result = await CreateVideo(formations, chapters, videos, storage, FakeJobRepository()).execute(
        CreateVideoCommand(
            chapter_id=str(chapter.id),
            title="Podcast",
            file_bytes=b"fake-wav",
            filename="podcast.wav",
        )
    )
    assert result.conversion is not None
    assert result.video.kind == "audio"
    assert result.video.processing_status == "processing"
    assert ".src.wav" in result.video.relative_path
    assert result.conversion.target_relative_path.endswith(".mp3")
