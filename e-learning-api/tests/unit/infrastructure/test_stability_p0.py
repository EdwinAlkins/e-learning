"""Tests unitaires — correctifs stabilité P0."""

from __future__ import annotations

from pathlib import Path

import pytest

from e_learning.application.catalog.dto import CreateVideoCommand
from e_learning.application.catalog.use_cases.create_video import CreateVideo
from e_learning.application.catalog.use_cases.delete_video import DeleteVideo
from e_learning.application.catalog.use_cases.reconcile_catalog import ReconcileCatalog
from e_learning.application.shared.errors import StorageError
from e_learning.application.shared.storage import ScannedChapter, ScannedFormation
from e_learning.domain.catalog.entities import Chapter, Formation, Video
from e_learning.domain.catalog.value_objects import (
    ChapterName,
    DurationSeconds,
    FormationName,
    Position,
    RelativePath,
    VideoTitle,
)
from e_learning.infrastructure.storage.filesystem_catalog import FilesystemCatalogStorage
from e_learning.presentation.api.http_range import parse_bytes_range
from tests.unit.application._fakes import (
    FakeChapterRepository,
    FakeDocumentRepository,
    FakeFormationRepository,
    FakeJobRepository,
    FakeVideoRepository,
)
from tests.unit.application.test_use_cases import FakeCatalogStorage


def test_absolute_path_rejects_traversal(tmp_path: Path) -> None:
    root = tmp_path / "videos"
    root.mkdir()
    storage = FilesystemCatalogStorage(root)
    evil = tmp_path / "videos-evil"
    evil.mkdir()
    (evil / "secret.mp4").write_bytes(b"x")

    with pytest.raises(StorageError, match="hors racine"):
        storage.absolute_path("../videos-evil/secret.mp4")


def test_delete_file_removes_staging_siblings(tmp_path: Path) -> None:
    root = tmp_path / "videos"
    storage = FilesystemCatalogStorage(root)
    chapter = root / "f" / "c"
    chapter.mkdir(parents=True)
    (chapter / "intro.mp4").write_bytes(b"mp4")
    (chapter / "intro.src.mkv").write_bytes(b"src")
    (chapter / "intro.md").write_text("summary")
    (chapter / "intro.txt").write_text("tx")

    storage.delete_file("f/c/intro.mp4")
    assert not (chapter / "intro.mp4").exists()
    assert not (chapter / "intro.src.mkv").exists()
    assert not (chapter / "intro.md").exists()
    assert not (chapter / "intro.txt").exists()


def test_parse_bytes_range_valid() -> None:
    assert parse_bytes_range("bytes=0-99", 1000) == (0, 99)
    assert parse_bytes_range("bytes=100-", 1000) == (100, 999)
    assert parse_bytes_range("bytes=-50", 1000) == (0, 50)  # start empty → 0


def test_parse_bytes_range_unsatisfiable() -> None:
    assert parse_bytes_range("bytes=1000-2000", 1000) is None
    assert parse_bytes_range("bytes=50-10", 1000) is None
    assert parse_bytes_range("bytes=abc-10", 1000) is None
    assert parse_bytes_range("bytes=0-10", 0) is None
    assert parse_bytes_range("items=0-10", 1000) is None


async def test_create_video_avoids_filename_collision(tmp_path: Path) -> None:
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

    first = await CreateVideo(formations, chapters, videos, storage, FakeJobRepository()).execute(
        CreateVideoCommand(
            chapter_id=str(chapter.id),
            title="Intro",
            file_bytes=b"fake-mp4-1",
            filename="intro.mp4",
        )
    )
    second = await CreateVideo(formations, chapters, videos, storage, FakeJobRepository()).execute(
        CreateVideoCommand(
            chapter_id=str(chapter.id),
            title="Intro",
            file_bytes=b"fake-mp4-2",
            filename="intro.mp4",
        )
    )
    assert first.video.relative_path.endswith("intro.mp4")
    assert second.video.relative_path.endswith("intro-1.mp4")
    assert first.video.relative_path != second.video.relative_path


async def test_delete_video_db_then_fs(tmp_path: Path) -> None:
    videos = FakeVideoRepository()
    storage = FakeCatalogStorage(tmp_path)
    relative = "f/c/v1.mp4"
    storage.write_video(relative, b"data")
    video = Video.create(
        chapter_id=Chapter.create(
            formation_id=Formation.create(name=FormationName("F")).id,
            name=ChapterName("C"),
            position=Position(0),
        ).id,
        title=VideoTitle("V1"),
        filename="v1.mp4",
        relative_path=RelativePath(relative),
        position=Position(0),
        duration=DurationSeconds(1),
    )
    await videos.save(video)

    await DeleteVideo(videos, storage).execute(str(video.id))
    assert str(video.id) not in videos.items
    assert not storage.absolute_path(relative).is_file()


async def test_reconcile_deletes_orphan_chapters(tmp_path: Path) -> None:
    formations = FakeFormationRepository()
    chapters = FakeChapterRepository()
    videos = FakeVideoRepository()
    documents = FakeDocumentRepository()

    formation = Formation.create(name=FormationName("alive"))
    await formations.save(formation)
    alive = Chapter.create(
        formation_id=formation.id,
        name=ChapterName("alive-ch"),
        position=Position(0),
    )
    orphan = Chapter.create(
        formation_id=formation.id,
        name=ChapterName("orphan-ch"),
        position=Position(1),
    )
    await chapters.save(alive)
    await chapters.save(orphan)

    storage = FakeCatalogStorage(
        tmp_path,
        scanned=[
            ScannedFormation(
                slug=str(formation.slug),
                chapters=[
                    ScannedChapter(
                        slug=str(alive.slug),
                        videos=[],
                        documents=[],
                    )
                ],
            )
        ],
    )
    await ReconcileCatalog(formations, chapters, videos, documents, storage).execute()
    assert str(alive.id) in chapters.items
    assert str(orphan.id) not in chapters.items


def test_routers_have_no_session_commit() -> None:
    """Smoke : SessionDep est le seul commit HTTP."""
    routers_dir = (
        Path(__file__).resolve().parents[3]
        / "src"
        / "e_learning"
        / "presentation"
        / "api"
        / "v1"
        / "routers"
    )
    for path in routers_dir.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "session.commit(" not in text, f"commit trouvé dans {path.name}"


def test_session_dep_uses_function_scope() -> None:
    """Évite l'écrasement ready←processing après BackgroundTasks (scope request)."""
    from typing import get_args

    from e_learning.presentation.api.dependencies.session import SessionDep

    depends = get_args(SessionDep)[1]
    assert depends.scope == "function"
