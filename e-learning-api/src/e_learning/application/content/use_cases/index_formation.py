"""Use case : indexer vidéos + documents extractibles d'une formation."""

from __future__ import annotations

from e_learning.application.content.dto import (
    IndexDocumentCommand,
    IndexFormationCommand,
    IndexFormationResult,
    IndexVideoCommand,
)
from e_learning.application.content.use_cases.index_document_content import IndexDocumentContent
from e_learning.application.content.use_cases.index_video_content import IndexVideoContent
from e_learning.application.jobs.progress import NullProgressReporter, ProgressReporter
from e_learning.domain.catalog.entities import Video
from e_learning.domain.catalog.repository import (
    ChapterRepository,
    DocumentRepository,
    FormationRepository,
    VideoRepository,
)
from e_learning.domain.catalog.value_objects import FormationId


class IndexFormation:
    def __init__(
        self,
        formations: FormationRepository,
        videos: VideoRepository,
        chapters: ChapterRepository,
        documents: DocumentRepository,
        index_video: IndexVideoContent,
        index_document: IndexDocumentContent,
    ) -> None:
        self._formations = formations
        self._videos = videos
        self._chapters = chapters
        self._documents = documents
        self._index_video = index_video
        self._index_document = index_document

    async def execute(
        self,
        command: IndexFormationCommand,
        *,
        progress: ProgressReporter | None = None,
    ) -> IndexFormationResult:
        reporter = progress or NullProgressReporter()
        formation = await self._formations.get(FormationId.from_string(command.formation_id))
        videos = await self._videos.list_by_formation(formation.id)
        eligible_videos = [
            v
            for v in videos
            if v.transcription_status == Video.AI_READY or v.summary_status == Video.AI_READY
        ]

        chapters = await self._chapters.list_by_formation(formation.id)
        documents = []
        for chapter in chapters:
            documents.extend(await self._documents.list_by_chapter(chapter.id))

        indexed_videos = 0
        indexed_documents = 0
        indexed_chunks = 0
        total_steps = max(len(eligible_videos) + len(documents), 1)
        step = 0

        for video in eligible_videos:
            pct = int(step / total_steps * 90)
            await reporter.set(
                pct, f"Indexation vidéo {step + 1}/{len(eligible_videos)}…"
            )
            n = await self._index_video.execute(IndexVideoCommand(video_id=str(video.id)))
            if n > 0:
                indexed_videos += 1
                indexed_chunks += n
            step += 1

        for document in documents:
            pct = int(step / total_steps * 90)
            await reporter.set(pct, f"Indexation document {document.title}…")
            n = await self._index_document.execute(
                IndexDocumentCommand(document_id=str(document.id))
            )
            if n > 0:
                indexed_documents += 1
                indexed_chunks += n
            step += 1

        await reporter.set(
            100,
            f"{indexed_videos} vidéo(s), {indexed_documents} doc(s), {indexed_chunks} chunk(s)",
        )
        return IndexFormationResult(
            indexed_videos=indexed_videos,
            indexed_documents=indexed_documents,
            indexed_chunks=indexed_chunks,
        )
