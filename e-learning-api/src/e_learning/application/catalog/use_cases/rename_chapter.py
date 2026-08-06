"""Use case : renommer un chapitre."""

from __future__ import annotations

from e_learning.application.catalog.dto import (
    ChapterDTO,
    DocumentDTO,
    RenameChapterCommand,
    VideoDTO,
)
from e_learning.application.shared.storage import CatalogStoragePort
from e_learning.domain.catalog.repository import (
    ChapterRepository,
    DocumentRepository,
    FormationRepository,
    VideoRepository,
)
from e_learning.domain.catalog.value_objects import ChapterId, ChapterName, Slug


class RenameChapter:
    def __init__(
        self,
        formations: FormationRepository,
        chapters: ChapterRepository,
        videos: VideoRepository,
        documents: DocumentRepository,
        storage: CatalogStoragePort,
    ) -> None:
        self._formations = formations
        self._chapters = chapters
        self._videos = videos
        self._documents = documents
        self._storage = storage

    async def execute(self, command: RenameChapterCommand) -> ChapterDTO:
        chapter = await self._chapters.get(ChapterId.from_string(command.chapter_id))
        formation = await self._formations.get(chapter.formation_id)
        name = ChapterName(command.name)
        new_slug = Slug.from_name(f"{chapter.position.value}-{name}")
        old_slug = str(chapter.slug)
        if old_slug != str(new_slug):
            self._storage.rename_chapter_dir(str(formation.slug), old_slug, str(new_slug))
        chapter.rename(name, slug=new_slug)
        await self._chapters.save(chapter)
        videos = [VideoDTO.from_entity(v) for v in await self._videos.list_by_chapter(chapter.id)]
        documents = [
            DocumentDTO.from_entity(d) for d in await self._documents.list_by_chapter(chapter.id)
        ]
        return ChapterDTO(
            id=str(chapter.id),
            name=str(chapter.name),
            slug=str(chapter.slug),
            position=chapter.position.value,
            videos=videos,
            documents=documents,
        )
