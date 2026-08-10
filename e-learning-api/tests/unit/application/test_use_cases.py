"""Tests unitaires — use cases application."""

from __future__ import annotations

from pathlib import Path

from e_learning.application.catalog.dto import (
    CreateDocumentCommand,
    ReorderChaptersCommand,
    ReorderVideosCommand,
    UpdateDocumentCommand,
)
from e_learning.application.catalog.use_cases.create_document import CreateDocument
from e_learning.application.catalog.use_cases.delete_document import DeleteDocument
from e_learning.application.catalog.use_cases.reconcile_catalog import ReconcileCatalog
from e_learning.application.catalog.use_cases.reorder_chapters import ReorderChapters
from e_learning.application.catalog.use_cases.reorder_videos import ReorderVideos
from e_learning.application.catalog.use_cases.update_document import UpdateDocument
from e_learning.application.learning.dto import CreateNoteCommand
from e_learning.application.learning.use_cases.create_note import CreateNote
from e_learning.application.shared.storage import (
    CatalogStoragePort,
    ScannedChapter,
    ScannedDocument,
    ScannedFormation,
    ScannedVideo,
)
from e_learning.application.user.use_cases.generate_user import GenerateUser
from e_learning.domain.catalog.entities import Chapter, Formation, Video
from e_learning.domain.catalog.value_objects import (
    ChapterName,
    DurationSeconds,
    FormationId,
    FormationName,
    Position,
    RelativePath,
    VideoTitle,
)
from tests.unit.application._fakes import (
    FakeChapterRepository,
    FakeDocumentRepository,
    FakeFormationRepository,
    FakeJobRepository,
    FakeNoteRepository,
    FakeUserRepository,
    FakeVideoRepository,
)


class FakeCatalogStorage(CatalogStoragePort):
    def __init__(self, root: Path, scanned: list[ScannedFormation] | None = None) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.written: list[str] = []
        self._scanned = scanned or []

    def absolute_path(self, relative_path: str) -> Path:
        return (self.root / relative_path).resolve()

    def scan(self) -> list[ScannedFormation]:
        return self._scanned

    def ensure_formation_dir(self, slug: str) -> None:
        (self.root / slug).mkdir(parents=True, exist_ok=True)

    def ensure_chapter_dir(self, formation_slug: str, chapter_slug: str) -> None:
        (self.root / formation_slug / chapter_slug).mkdir(parents=True, exist_ok=True)

    def rename_formation_dir(self, old_slug: str, new_slug: str) -> None:
        pass

    def rename_chapter_dir(self, formation_slug: str, old_slug: str, new_slug: str) -> None:
        pass

    def delete_formation_dir(self, slug: str) -> None:
        pass

    def delete_chapter_dir(self, formation_slug: str, chapter_slug: str) -> None:
        pass

    def delete_file(self, relative_path: str) -> None:
        path = self.absolute_path(relative_path)
        if path.exists():
            path.unlink()

    def write_video(self, relative_path: str, data: bytes) -> float:
        self.write_document(relative_path, data)
        return 0.0

    def write_document(self, relative_path: str, data: bytes) -> None:
        path = self.absolute_path(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        self.written.append(relative_path)

    def move_file(self, old_relative_path: str, new_relative_path: str) -> None:
        pass

    def file_exists(self, relative_path: str) -> bool:
        return self.absolute_path(relative_path).is_file()

    def probe_duration(self, relative_path: str) -> float:
        return 0.0


async def test_generate_user() -> None:
    users = FakeUserRepository()
    dto = await GenerateUser(users).execute()
    assert dto.id in users.items


async def test_create_note() -> None:
    users = FakeUserRepository()
    videos = FakeVideoRepository()
    notes = FakeNoteRepository()
    user = await GenerateUser(users).execute()
    chapter = Chapter.create(
        formation_id=FormationId.generate(),
        name=ChapterName("C1"),
        position=Position(0),
    )
    video = Video.create(
        chapter_id=chapter.id,
        title=VideoTitle("V1"),
        filename="v1.mp4",
        relative_path=RelativePath("f/c/v1.mp4"),
        position=Position(0),
        duration=DurationSeconds(60),
    )
    await videos.save(video)
    dto = await CreateNote(notes, users, videos).execute(
        CreateNoteCommand(
            user_id=user.id,
            video_id=str(video.id),
            timecode=12.5,
            content="Point clé",
        )
    )
    assert dto.content == "Point clé"
    assert dto.timecode == 12.5


async def test_reorder_videos() -> None:
    chapters = FakeChapterRepository()
    videos = FakeVideoRepository()
    documents = FakeDocumentRepository()
    chapter = Chapter.create(
        formation_id=FormationId.generate(),
        name=ChapterName("C1"),
        position=Position(0),
    )
    await chapters.save(chapter)
    v1 = Video.create(
        chapter_id=chapter.id,
        title=VideoTitle("A"),
        filename="a.mp4",
        relative_path=RelativePath("f/c/a.mp4"),
        position=Position(0),
        duration=DurationSeconds(1),
    )
    v2 = Video.create(
        chapter_id=chapter.id,
        title=VideoTitle("B"),
        filename="b.mp4",
        relative_path=RelativePath("f/c/b.mp4"),
        position=Position(1),
        duration=DurationSeconds(1),
    )
    await videos.save(v1)
    await videos.save(v2)
    dto = await ReorderVideos(chapters, videos, documents).execute(
        ReorderVideosCommand(chapter_id=str(chapter.id), video_ids=[str(v2.id), str(v1.id)])
    )
    assert [v.id for v in dto.videos] == [str(v2.id), str(v1.id)]
    assert videos.items[str(v2.id)].position.value == 0
    assert videos.items[str(v1.id)].position.value == 1


async def test_reorder_chapters() -> None:
    formations = FakeFormationRepository()
    chapters = FakeChapterRepository()
    videos = FakeVideoRepository()
    documents = FakeDocumentRepository()
    jobs = FakeJobRepository()

    formation = Formation.create(name=FormationName("Formation Test"))
    await formations.save(formation)
    c1 = Chapter.create(
        formation_id=formation.id,
        name=ChapterName("Chapitre 1"),
        position=Position(0),
    )
    c2 = Chapter.create(
        formation_id=formation.id,
        name=ChapterName("Chapitre 2"),
        position=Position(1),
    )
    await chapters.save(c1)
    await chapters.save(c2)

    dto = await ReorderChapters(formations, chapters, videos, documents, jobs).execute(
        ReorderChaptersCommand(
            formation_id=str(formation.id),
            chapter_ids=[str(c2.id), str(c1.id)],
        )
    )
    assert [c.id for c in dto.chapters] == [str(c2.id), str(c1.id)]
    assert chapters.items[str(c2.id)].position.value == 0
    assert chapters.items[str(c1.id)].position.value == 1


async def test_create_update_delete_document(tmp_path: Path) -> None:
    formations = FakeFormationRepository()
    chapters = FakeChapterRepository()
    videos = FakeVideoRepository()
    documents = FakeDocumentRepository()
    storage = FakeCatalogStorage(tmp_path)

    formation = Formation.create(name=FormationName("Formation Test"))
    await formations.save(formation)
    chapter = Chapter.create(
        formation_id=formation.id,
        name=ChapterName("Chapitre 1"),
        position=Position(0),
    )
    await chapters.save(chapter)
    video = Video.create(
        chapter_id=chapter.id,
        title=VideoTitle("Intro"),
        filename="intro.mp4",
        relative_path=RelativePath(f"{formation.slug}/{chapter.slug}/intro.mp4"),
        position=Position(0),
        duration=DurationSeconds(10),
    )
    await videos.save(video)

    created = await CreateDocument(formations, chapters, videos, documents, storage).execute(
        CreateDocumentCommand(
            chapter_id=str(chapter.id),
            title="Guide PDF",
            file_bytes=b"%PDF-1.4",
            filename="guide.pdf",
            video_id=str(video.id),
        )
    )
    assert created.title == "Guide PDF"
    assert created.filename.endswith(".pdf")
    assert created.video_id == str(video.id)
    assert storage.absolute_path(created.relative_path).is_file()

    updated = await UpdateDocument(documents, videos).execute(
        UpdateDocumentCommand(
            document_id=created.id,
            title="Guide mis à jour",
            video_id=None,
            update_video_id=True,
        )
    )
    assert updated.title == "Guide mis à jour"
    assert updated.video_id is None

    await DeleteDocument(documents, storage).execute(created.id)
    assert created.id not in documents.items
    assert not storage.absolute_path(created.relative_path).is_file()


async def test_create_document_auto_attaches_by_name(tmp_path: Path) -> None:
    formations = FakeFormationRepository()
    chapters = FakeChapterRepository()
    videos = FakeVideoRepository()
    documents = FakeDocumentRepository()
    storage = FakeCatalogStorage(tmp_path)

    formation = Formation.create(name=FormationName("Formation Test"))
    await formations.save(formation)
    chapter = Chapter.create(
        formation_id=formation.id,
        name=ChapterName("Chapitre 1"),
        position=Position(0),
    )
    await chapters.save(chapter)
    video = Video.create(
        chapter_id=chapter.id,
        title=VideoTitle("Les Fondations"),
        filename="1. Les Fondations.mp4",
        relative_path=RelativePath(f"{formation.slug}/{chapter.slug}/1. Les Fondations.mp4"),
        position=Position(0),
        duration=DurationSeconds(10),
    )
    await videos.save(video)

    matched = await CreateDocument(formations, chapters, videos, documents, storage).execute(
        CreateDocumentCommand(
            chapter_id=str(chapter.id),
            title="Les Fondations",
            file_bytes=b"docx",
            filename="1. Les Fondations.docx",
        )
    )
    assert matched.video_id == str(video.id)

    chapter_level = await CreateDocument(formations, chapters, videos, documents, storage).execute(
        CreateDocumentCommand(
            chapter_id=str(chapter.id),
            title="Fixation d'objectifs",
            file_bytes=b"xlsx",
            filename="2.Fixation d'objectifs.xlsx",
        )
    )
    assert chapter_level.video_id is None


async def test_reconcile_attaches_documents_by_name(tmp_path: Path) -> None:
    formations = FakeFormationRepository()
    chapters = FakeChapterRepository()
    videos = FakeVideoRepository()
    documents = FakeDocumentRepository()
    scanned = [
        ScannedFormation(
            slug="formation-test",
            chapters=[
                ScannedChapter(
                    slug="chapitre-1",
                    videos=[
                        ScannedVideo(
                            filename="1. Les Fondations.mp4",
                            relative_path="formation-test/chapitre-1/1. Les Fondations.mp4",
                            title="Les Fondations",
                            duration_seconds=60.0,
                        ),
                        ScannedVideo(
                            filename="2. La Projection.mp4",
                            relative_path="formation-test/chapitre-1/2. La Projection.mp4",
                            title="La Projection",
                            duration_seconds=60.0,
                        ),
                    ],
                    documents=[
                        ScannedDocument(
                            filename="1. Les Fondations.docx",
                            relative_path="formation-test/chapitre-1/1. Les Fondations.docx",
                            title="Les Fondations",
                            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        ),
                        ScannedDocument(
                            filename="2.Fixation d'objectifs.xlsx",
                            relative_path="formation-test/chapitre-1/2.Fixation d'objectifs.xlsx",
                            title="Fixation d'objectifs",
                            mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        ),
                    ],
                )
            ],
        )
    ]
    storage = FakeCatalogStorage(tmp_path, scanned=scanned)

    await ReconcileCatalog(formations, chapters, videos, documents, storage).execute()

    docs = list(documents.items.values())
    assert len(docs) == 2
    by_title = {str(d.title): d for d in docs}
    fondations = by_title["Les Fondations"]
    fixation = by_title["Fixation d'objectifs"]
    assert fondations.video_id is not None
    video = next(v for v in videos.items.values() if str(v.title) == "Les Fondations")
    assert fondations.video_id == video.id
    assert fixation.video_id is None

    # Second pass: existing docs get video_id updated when match appears/disappears
    await ReconcileCatalog(formations, chapters, videos, documents, storage).execute()
    assert documents.items[str(fondations.id)].video_id == video.id
    assert documents.items[str(fixation.id)].video_id is None


async def test_reconcile_sets_ai_status_from_sidecars(tmp_path: Path) -> None:
    formations = FakeFormationRepository()
    chapters = FakeChapterRepository()
    videos = FakeVideoRepository()
    documents = FakeDocumentRepository()
    rel = "formation-test/chapitre-1/1. Intro.mp4"
    media_path = tmp_path / rel
    media_path.parent.mkdir(parents=True, exist_ok=True)
    media_path.write_bytes(b"mp4")
    media_path.with_suffix(".txt").write_text("transcription", encoding="utf-8")
    media_path.with_suffix(".md").write_text("# résumé", encoding="utf-8")

    scanned = [
        ScannedFormation(
            slug="formation-test",
            chapters=[
                ScannedChapter(
                    slug="chapitre-1",
                    videos=[
                        ScannedVideo(
                            filename="1. Intro.mp4",
                            relative_path=rel,
                            title="Intro",
                            duration_seconds=12.0,
                        )
                    ],
                    documents=[],
                )
            ],
        )
    ]
    storage = FakeCatalogStorage(tmp_path, scanned=scanned)

    await ReconcileCatalog(formations, chapters, videos, documents, storage).execute()

    video = next(iter(videos.items.values()))
    assert video.transcription_status == Video.AI_READY
    assert video.summary_status == Video.AI_READY

    # Statut processing obsolète → ready si sidecar présent
    video.set_transcription_status(Video.AI_PROCESSING)
    video.set_summary_status(Video.AI_FAILED)
    await videos.save(video)
    await ReconcileCatalog(formations, chapters, videos, documents, storage).execute()
    video = await videos.get(video.id)
    assert video.transcription_status == Video.AI_READY
    assert video.summary_status == Video.AI_READY
