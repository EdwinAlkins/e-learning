"""Use case : uploader un document annexe dans un chapitre."""

from __future__ import annotations

import asyncio
import mimetypes
from pathlib import PurePosixPath

from e_learning.application.catalog.document_ext import assert_allowed_document_extension
from e_learning.application.catalog.dto import CreateDocumentCommand, DocumentDTO
from e_learning.application.catalog.name_match import find_matching_video
from e_learning.application.shared.storage import CatalogStoragePort
from e_learning.domain.catalog.entities import Document
from e_learning.domain.catalog.exceptions import ReorderInvalid
from e_learning.domain.catalog.repository import (
    ChapterRepository,
    DocumentRepository,
    FormationRepository,
    VideoRepository,
)
from e_learning.domain.catalog.value_objects import (
    ChapterId,
    DocumentTitle,
    Position,
    RelativePath,
    VideoId,
    slugify,
)


class CreateDocument:
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

    async def execute(self, command: CreateDocumentCommand) -> DocumentDTO:
        chapter = await self._chapters.get(ChapterId.from_string(command.chapter_id))
        formation = await self._formations.get(chapter.formation_id)
        title = DocumentTitle(command.title)

        video_id: VideoId | None = None
        if command.video_id:
            video = await self._videos.get(VideoId.from_string(command.video_id))
            if video.chapter_id != chapter.id:
                raise ReorderInvalid("La vidéo n'appartient pas à ce chapitre.")
            video_id = video.id

        original = PurePosixPath(command.filename)
        if video_id is None:
            chapter_videos = await self._videos.list_by_chapter(chapter.id)
            matched = find_matching_video(chapter_videos, str(title))
            if matched is None:
                matched = find_matching_video(chapter_videos, original.stem)
            if matched is not None:
                video_id = matched.id

        ext = assert_allowed_document_extension(command.filename)
        stem = slugify(str(title)) or slugify(original.stem) or "document"
        filename = f"{stem}{ext}"
        relative = RelativePath(
            str(PurePosixPath(str(formation.slug)) / str(chapter.slug) / filename)
        )
        counter = 1
        while self._storage.file_exists(
            str(relative)
        ) or await self._documents.find_by_relative_path(relative):
            filename = f"{stem}-{counter}{ext}"
            relative = RelativePath(
                str(PurePosixPath(str(formation.slug)) / str(chapter.slug) / filename)
            )
            counter += 1

        await asyncio.to_thread(self._storage.write_document, str(relative), command.file_bytes)
        mime, _ = mimetypes.guess_type(filename)
        document = Document.create(
            chapter_id=chapter.id,
            title=title,
            filename=filename,
            relative_path=relative,
            position=Position(await self._documents.next_position(chapter.id)),
            mime_type=mime,
            video_id=video_id,
        )
        await self._documents.save(document)
        return DocumentDTO.from_entity(document)
