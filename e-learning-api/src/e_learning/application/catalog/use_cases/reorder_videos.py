"""Use case : réordonner les vidéos d'un chapitre (positions DB)."""

from __future__ import annotations

from e_learning.application.catalog.dto import (
    ChapterDTO,
    DocumentDTO,
    ReorderVideosCommand,
    VideoDTO,
)
from e_learning.domain.catalog.exceptions import ReorderInvalid
from e_learning.domain.catalog.repository import (
    ChapterRepository,
    DocumentRepository,
    VideoRepository,
)
from e_learning.domain.catalog.value_objects import ChapterId, Position


class ReorderVideos:
    def __init__(
        self,
        chapters: ChapterRepository,
        videos: VideoRepository,
        documents: DocumentRepository,
    ) -> None:
        self._chapters = chapters
        self._videos = videos
        self._documents = documents

    async def execute(self, command: ReorderVideosCommand) -> ChapterDTO:
        chapter = await self._chapters.get(ChapterId.from_string(command.chapter_id))
        current = await self._videos.list_by_chapter(chapter.id)
        current_ids = {str(v.id) for v in current}
        if len(command.video_ids) != len(current_ids):
            raise ReorderInvalid("La liste doit contenir exactement toutes les vidéos du chapitre.")
        if len(set(command.video_ids)) != len(command.video_ids):
            raise ReorderInvalid("La liste contient des doublons.")
        if set(command.video_ids) != current_ids:
            raise ReorderInvalid("La liste contient des identifiants inconnus ou hors chapitre.")
        by_id = {str(v.id): v for v in current}
        ordered: list = []
        for index, vid in enumerate(command.video_ids):
            video = by_id[vid]
            video.move_to(Position(index))
            ordered.append(video)
        await self._videos.save_ordered(ordered)
        videos = [VideoDTO.from_entity(v) for v in ordered]
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
