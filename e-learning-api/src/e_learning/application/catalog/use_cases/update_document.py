"""Use case : renommer / rattacher un document annexe."""

from __future__ import annotations

from e_learning.application.catalog.dto import DocumentDTO, UpdateDocumentCommand
from e_learning.domain.catalog.exceptions import ReorderInvalid
from e_learning.domain.catalog.repository import DocumentRepository, VideoRepository
from e_learning.domain.catalog.value_objects import DocumentId, DocumentTitle, VideoId


class UpdateDocument:
    def __init__(self, documents: DocumentRepository, videos: VideoRepository) -> None:
        self._documents = documents
        self._videos = videos

    async def execute(self, command: UpdateDocumentCommand) -> DocumentDTO:
        document = await self._documents.get(DocumentId.from_string(command.document_id))

        if command.title is not None:
            document.rename(DocumentTitle(command.title))

        if command.update_video_id:
            if command.video_id is None:
                document.attach_video(None)
            else:
                video = await self._videos.get(VideoId.from_string(command.video_id))
                if video.chapter_id != document.chapter_id:
                    raise ReorderInvalid("La vidéo n'appartient pas au chapitre du document.")
                document.attach_video(video.id)

        await self._documents.save(document)
        return DocumentDTO.from_entity(document)
