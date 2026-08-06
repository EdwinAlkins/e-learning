"""Tests — whitelist d'extensions documents / médias."""

from __future__ import annotations

from pathlib import Path

import pytest

from e_learning.application.catalog.document_ext import (
    DOCUMENT_EXTS,
    assert_allowed_document_extension,
)
from e_learning.application.catalog.dto import CreateDocumentCommand, CreateVideoCommand
from e_learning.application.catalog.media_kind import (
    MEDIA_EXTS,
    assert_allowed_media_extension,
    classify_media_kind,
)
from e_learning.application.catalog.use_cases.create_document import CreateDocument
from e_learning.application.catalog.use_cases.create_video import CreateVideo
from e_learning.domain.catalog.entities import Chapter, Formation, Video
from e_learning.domain.catalog.exceptions import UnsupportedFileExtension
from e_learning.domain.catalog.value_objects import ChapterName, FormationName, Position
from tests.unit.application._fakes import (
    FakeChapterRepository,
    FakeDocumentRepository,
    FakeFormationRepository,
    FakeJobRepository,
    FakeVideoRepository,
)
from tests.unit.application.test_use_cases import FakeCatalogStorage


def test_document_extension_whitelist() -> None:
    assert assert_allowed_document_extension("guide.PDF") == ".pdf"
    with pytest.raises(UnsupportedFileExtension):
        assert_allowed_document_extension("malware.exe")
    with pytest.raises(UnsupportedFileExtension):
        assert_allowed_document_extension("sans_extension")
    with pytest.raises(UnsupportedFileExtension):
        assert_allowed_document_extension("script.sh")
    assert ".bin" not in DOCUMENT_EXTS


def test_media_extension_whitelist() -> None:
    assert classify_media_kind("clip.MP4") == Video.KIND_VIDEO
    assert classify_media_kind("track.wav") == Video.KIND_AUDIO
    with pytest.raises(UnsupportedFileExtension):
        assert_allowed_media_extension("payload.exe")
    with pytest.raises(UnsupportedFileExtension):
        assert_allowed_media_extension("video")
    assert ".bin" not in MEDIA_EXTS


async def test_create_document_rejects_bad_extension(tmp_path: Path) -> None:
    formations = FakeFormationRepository()
    chapters = FakeChapterRepository()
    videos = FakeVideoRepository()
    documents = FakeDocumentRepository()
    storage = FakeCatalogStorage(tmp_path)
    formation = Formation.create(name=FormationName("F"))
    await formations.save(formation)
    chapter = Chapter.create(
        formation_id=formation.id, name=ChapterName("C"), position=Position(0)
    )
    await chapters.save(chapter)

    with pytest.raises(UnsupportedFileExtension):
        await CreateDocument(formations, chapters, videos, documents, storage).execute(
            CreateDocumentCommand(
                chapter_id=str(chapter.id),
                title="Bad",
                file_bytes=b"MZ",
                filename="virus.exe",
            )
        )


async def test_create_video_rejects_bad_extension(tmp_path: Path) -> None:
    formations = FakeFormationRepository()
    chapters = FakeChapterRepository()
    videos = FakeVideoRepository()
    jobs = FakeJobRepository()
    storage = FakeCatalogStorage(tmp_path)
    formation = Formation.create(name=FormationName("F"))
    await formations.save(formation)
    chapter = Chapter.create(
        formation_id=formation.id, name=ChapterName("C"), position=Position(0)
    )
    await chapters.save(chapter)

    with pytest.raises(UnsupportedFileExtension):
        await CreateVideo(formations, chapters, videos, storage, jobs).execute(
            CreateVideoCommand(
                chapter_id=str(chapter.id),
                title="Bad",
                file_bytes=b"MZ",
                filename="clip.exe",
            )
        )
