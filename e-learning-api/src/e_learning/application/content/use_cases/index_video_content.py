"""Use case : indexer transcription + résumé d'une vidéo dans Qdrant."""

from __future__ import annotations

from e_learning.application.content.chunker import chunk_point_id, chunk_text
from e_learning.application.content.dto import IndexVideoCommand
from e_learning.application.jobs.progress import NullProgressReporter, ProgressReporter
from e_learning.application.shared.media import MediaFilePort
from e_learning.application.shared.rag import EmbeddingPort, RagChunk, VectorStorePort
from e_learning.domain.catalog.repository import (
    ChapterRepository,
    FormationRepository,
    VideoRepository,
)
from e_learning.domain.catalog.value_objects import VideoId


class IndexVideoContent:
    def __init__(
        self,
        videos: VideoRepository,
        chapters: ChapterRepository,
        formations: FormationRepository,
        media_files: MediaFilePort,
        embeddings: EmbeddingPort,
        vectors: VectorStorePort,
        *,
        chunk_size: int,
        chunk_overlap: int,
    ) -> None:
        self._videos = videos
        self._chapters = chapters
        self._formations = formations
        self._media_files = media_files
        self._embeddings = embeddings
        self._vectors = vectors
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    async def execute(
        self,
        command: IndexVideoCommand,
        *,
        progress: ProgressReporter | None = None,
    ) -> int:
        reporter = progress or NullProgressReporter()
        video = await self._videos.get(VideoId.from_string(command.video_id))
        chapter = await self._chapters.get(video.chapter_id)
        await self._formations.get(chapter.formation_id)

        await reporter.set(5, "Découpage du contenu…")
        pieces: list[tuple[str, str]] = []
        relative = str(video.relative_path)
        tx = self._media_files.read_text(self._media_files.transcription_path(relative))
        if tx:
            for part in chunk_text(tx, chunk_size=self._chunk_size, overlap=self._chunk_overlap):
                pieces.append(("transcription", part))
        summary = self._media_files.read_text(self._media_files.summary_path(relative))
        if summary:
            for part in chunk_text(
                summary, chunk_size=self._chunk_size, overlap=self._chunk_overlap
            ):
                pieces.append(("summary", part))

        await self._vectors.delete_by_video(str(video.id))
        if not pieces:
            await reporter.set(100, "Rien à indexer")
            return 0

        total = len(pieces)
        await reporter.set(15, f"Embeddings 0/{total}")
        # Batch embeddings (API) puis progression par chunks upsert
        vectors = await self._embeddings.embed([text for _, text in pieces])
        await reporter.set(55, f"Embeddings {total}/{total}")

        source_counters: dict[str, int] = {}
        chunks: list[RagChunk] = []
        for (source, text), vector in zip(pieces, vectors, strict=True):
            idx = source_counters.get(source, 0)
            source_counters[source] = idx + 1
            chunks.append(
                RagChunk(
                    id=chunk_point_id(str(video.id), source, idx),
                    formation_id=str(chapter.formation_id),
                    chapter_id=str(chapter.id),
                    video_id=str(video.id),
                    title=str(video.title),
                    source=source,
                    chunk_index=idx,
                    text=text,
                    vector=vector,
                )
            )
        await reporter.set(75, f"Indexation {total} chunk(s)…")
        await self._vectors.upsert_chunks(chunks)
        await reporter.set(100, f"{total} chunk(s) indexés")
        return len(chunks)
