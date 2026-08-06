"""Use case : déplacer une vidéo entre chapitres."""

from __future__ import annotations

from pathlib import PurePosixPath

from e_learning.application.catalog.dto import FormationDTO, MoveVideoCommand
from e_learning.application.catalog.use_cases.get_formation import GetFormation
from e_learning.application.shared.storage import CatalogStoragePort
from e_learning.domain.catalog.exceptions import ReorderInvalid
from e_learning.domain.catalog.repository import (
    ChapterRepository,
    DocumentRepository,
    FormationRepository,
    JobRepository,
    VideoRepository,
)
from e_learning.domain.catalog.value_objects import ChapterId, Position, RelativePath, VideoId


class MoveVideo:
    def __init__(
        self,
        formations: FormationRepository,
        chapters: ChapterRepository,
        videos: VideoRepository,
        documents: DocumentRepository,
        storage: CatalogStoragePort,
        jobs: JobRepository,
    ) -> None:
        self._chapters = chapters
        self._videos = videos
        self._storage = storage
        self._get = GetFormation(formations, chapters, videos, documents, jobs)

    async def execute(self, command: MoveVideoCommand) -> FormationDTO:
        video = await self._videos.get(VideoId.from_string(command.video_id))
        source = await self._chapters.get(ChapterId.from_string(command.source_chapter_id))
        target = await self._chapters.get(ChapterId.from_string(command.target_chapter_id))
        if video.chapter_id != source.id:
            raise ReorderInvalid("La vidéo n'appartient pas au chapitre source.")
        formation = await self._get._formations.get(target.formation_id)

        target_videos = await self._videos.list_by_chapter(target.id)
        if command.after_video_id is not None and command.position is not None:
            raise ReorderInvalid("Fournir position ou after_video_id, pas les deux.")
        if command.after_video_id is not None:
            ids = [str(v.id) for v in target_videos]
            if command.after_video_id not in ids:
                raise ReorderInvalid("after_video_id inconnu dans le chapitre cible.")
            insert_at = ids.index(command.after_video_id) + 1
        elif command.position is not None:
            insert_at = max(0, min(command.position, len(target_videos)))
        else:
            insert_at = len(target_videos)

        new_rel = RelativePath(
            str(PurePosixPath(str(formation.slug)) / str(target.slug) / video.filename)
        )
        if str(new_rel) != str(video.relative_path):
            self._storage.move_file(str(video.relative_path), str(new_rel))

        if source.id != target.id:
            remaining = [
                v for v in await self._videos.list_by_chapter(source.id) if v.id != video.id
            ]
            for index, v in enumerate(remaining):
                v.move_to(Position(index))
            await self._videos.save_ordered(remaining)

        ordered = [v for v in target_videos if v.id != video.id]
        ordered.insert(insert_at, video)
        for index, v in enumerate(ordered):
            if v.id == video.id:
                v.relocate(
                    chapter_id=target.id,
                    position=Position(index),
                    relative_path=new_rel,
                    filename=video.filename,
                )
            else:
                v.move_to(Position(index))
        await self._videos.save_ordered(ordered)

        return await self._get.execute(str(target.formation_id))
