"""Use case : renommer un chapitre."""

from __future__ import annotations

from e_learning.application.catalog.dto import (
    ChapterDTO,
    DocumentDTO,
    RenameChapterCommand,
    VideoDTO,
)
from e_learning.application.catalog.relative_paths import rewrite_path_prefix
from e_learning.application.shared.storage import CatalogStoragePort
from e_learning.domain.catalog.repository import (
    ChapterRepository,
    DocumentRepository,
    FormationRepository,
    VideoRepository,
)
from e_learning.domain.catalog.value_objects import ChapterId, ChapterName, RelativePath, Slug


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
            formation_slug = str(formation.slug)
            self._storage.rename_chapter_dir(formation_slug, old_slug, str(new_slug))
            await self._rewrite_media_paths(chapter.id, formation_slug, old_slug, str(new_slug))
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

    async def _rewrite_media_paths(
        self,
        chapter_id: ChapterId,
        formation_slug: str,
        old_chapter_slug: str,
        new_chapter_slug: str,
    ) -> None:
        old_prefix = f"{formation_slug}/{old_chapter_slug}"
        new_prefix = f"{formation_slug}/{new_chapter_slug}"
        for video in await self._videos.list_by_chapter(chapter_id):
            rewritten = rewrite_path_prefix(str(video.relative_path), old_prefix, new_prefix)
            if rewritten is None:
                continue
            video.update_relative_path(RelativePath(rewritten))
            await self._videos.save(video)
        for document in await self._documents.list_by_chapter(chapter_id):
            rewritten = rewrite_path_prefix(str(document.relative_path), old_prefix, new_prefix)
            if rewritten is None:
                continue
            document.update_relative_path(RelativePath(rewritten))
            await self._documents.save(document)
