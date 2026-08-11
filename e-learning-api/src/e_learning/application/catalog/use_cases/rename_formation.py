"""Use case : renommer une formation."""

from __future__ import annotations

from e_learning.application.catalog.dto import FormationDTO, RenameFormationCommand
from e_learning.application.catalog.relative_paths import rewrite_path_prefix
from e_learning.application.catalog.use_cases.get_formation import GetFormation
from e_learning.application.shared.storage import CatalogStoragePort
from e_learning.domain.catalog.exceptions import FormationNameAlreadyUsed, FormationSlugAlreadyUsed
from e_learning.domain.catalog.repository import (
    ChapterRepository,
    DocumentRepository,
    FormationRepository,
    JobRepository,
    VideoRepository,
)
from e_learning.domain.catalog.value_objects import FormationId, FormationName, RelativePath, Slug


class RenameFormation:
    def __init__(
        self,
        formations: FormationRepository,
        chapters: ChapterRepository,
        videos: VideoRepository,
        documents: DocumentRepository,
        storage: CatalogStoragePort,
        jobs: JobRepository,
    ) -> None:
        self._formations = formations
        self._chapters = chapters
        self._videos = videos
        self._documents = documents
        self._storage = storage
        self._get = GetFormation(formations, chapters, videos, documents, jobs)

    async def execute(self, command: RenameFormationCommand) -> FormationDTO:
        formation = await self._formations.get(FormationId.from_string(command.formation_id))
        name = FormationName(command.name)
        existing = await self._formations.find_by_name(str(name))
        if existing is not None and existing.id != formation.id:
            raise FormationNameAlreadyUsed(str(name))
        new_slug = Slug.from_name(str(name))
        slug_owner = await self._formations.find_by_slug(str(new_slug))
        if slug_owner is not None and slug_owner.id != formation.id:
            raise FormationSlugAlreadyUsed(str(new_slug))
        old_slug = str(formation.slug)
        if old_slug != str(new_slug):
            self._storage.rename_formation_dir(old_slug, str(new_slug))
            await self._rewrite_media_paths(formation.id, old_slug, str(new_slug))
        formation.rename(name, slug=new_slug)
        await self._formations.save(formation)
        return await self._get.execute(str(formation.id))

    async def _rewrite_media_paths(
        self, formation_id: FormationId, old_slug: str, new_slug: str
    ) -> None:
        for video in await self._videos.list_by_formation(formation_id):
            rewritten = rewrite_path_prefix(str(video.relative_path), old_slug, new_slug)
            if rewritten is None:
                continue
            video.update_relative_path(RelativePath(rewritten))
            await self._videos.save(video)

        for chapter in await self._chapters.list_by_formation(formation_id):
            for document in await self._documents.list_by_chapter(chapter.id):
                rewritten = rewrite_path_prefix(str(document.relative_path), old_slug, new_slug)
                if rewritten is None:
                    continue
                document.update_relative_path(RelativePath(rewritten))
                await self._documents.save(document)
