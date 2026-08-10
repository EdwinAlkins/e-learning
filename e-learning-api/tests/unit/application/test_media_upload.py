"""Tests — upload média audio/vidéo + conversion différée."""

from __future__ import annotations

from pathlib import Path

from e_learning.application.catalog.dto import CreateVideoCommand
from e_learning.application.catalog.media_kind import classify_media_kind, needs_auto_conversion
from e_learning.application.catalog.use_cases.create_video import CreateVideo
from e_learning.domain.catalog.entities import Chapter, Formation, Video
from e_learning.domain.catalog.value_objects import (
    ChapterName,
    DurationSeconds,
    FormationName,
    Position,
    RelativePath,
    VideoTitle,
)
from tests.unit.application._fakes import (
    FakeChapterRepository,
    FakeFormationRepository,
    FakeJobRepository,
    FakeVideoRepository,
    RecordingPublisher,
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

    result = await CreateVideo(formations, chapters, videos, storage, FakeJobRepository(), RecordingPublisher()).execute(
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

    result = await CreateVideo(formations, chapters, videos, storage, FakeJobRepository(), RecordingPublisher()).execute(
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


async def test_complete_conversion_migrates_src_sidecars(tmp_path: Path) -> None:
    """Après conversion, ``clip.src.txt`` / ``.md`` deviennent ``clip.txt`` / ``.md``."""
    from e_learning.application.catalog.dto import MediaConversionJob
    from e_learning.application.catalog.use_cases.complete_media_conversion import (
        CompleteMediaConversion,
    )
    from e_learning.application.shared.media import MediaConvertPort

    class _FakeConverter(MediaConvertPort):
        def needs_video_transcode(self, path: Path) -> bool:
            return True

        def needs_audio_transcode(self, path: Path) -> bool:
            return True

        def convert_to_mp4(
            self,
            source: Path,
            destination: Path,
            *,
            on_progress=None,
        ) -> None:
            destination.write_bytes(b"converted-mp4")

        def convert_to_mp3(
            self,
            source: Path,
            destination: Path,
            *,
            on_progress=None,
        ) -> None:
            destination.write_bytes(b"converted-mp3")

    videos = FakeVideoRepository()
    storage = FakeCatalogStorage(tmp_path)

    chapter_dir = tmp_path / "f" / "c"
    chapter_dir.mkdir(parents=True)
    source_rel = "f/c/clip.src.mkv"
    target_rel = "f/c/clip.mp4"
    (chapter_dir / "clip.src.mkv").write_bytes(b"src-media")
    (chapter_dir / "clip.src.txt").write_text("transcription", encoding="utf-8")
    (chapter_dir / "clip.src.md").write_text("# résumé", encoding="utf-8")

    formation = Formation.create(name=FormationName("Formation Test"))
    chapter = Chapter.create(
        formation_id=formation.id,
        name=ChapterName("Chapitre 1"),
        position=Position(0),
    )
    video = Video.create(
        chapter_id=chapter.id,
        title=VideoTitle("Clip"),
        filename="clip.src.mkv",
        relative_path=RelativePath(source_rel),
        position=Position(0),
        duration=DurationSeconds(1),
        processing_status=Video.STATUS_PROCESSING,
        transcription_status=Video.AI_READY,
    )
    await videos.save(video)

    await CompleteMediaConversion(videos, storage, _FakeConverter()).execute(
        MediaConversionJob(
            video_id=str(video.id),
            source_relative_path=source_rel,
            target_relative_path=target_rel,
            kind=Video.KIND_VIDEO,
        )
    )

    updated = await videos.get(video.id)
    assert str(updated.relative_path) == target_rel
    assert updated.processing_status == Video.STATUS_READY
    assert (chapter_dir / "clip.mp4").is_file()
    assert (chapter_dir / "clip.txt").read_text(encoding="utf-8") == "transcription"
    assert (chapter_dir / "clip.md").read_text(encoding="utf-8") == "# résumé"
    assert not (chapter_dir / "clip.src.mkv").exists()
    assert not (chapter_dir / "clip.src.txt").exists()
    assert not (chapter_dir / "clip.src.md").exists()
