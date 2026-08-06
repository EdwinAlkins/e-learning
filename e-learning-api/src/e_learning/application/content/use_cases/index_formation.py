"""Use case : indexer toutes les vidéos prêtées d'une formation."""

from __future__ import annotations

from e_learning.application.content.dto import (
    IndexFormationCommand,
    IndexFormationResult,
    IndexVideoCommand,
)
from e_learning.application.content.use_cases.index_video_content import IndexVideoContent
from e_learning.application.jobs.progress import NullProgressReporter, ProgressReporter
from e_learning.domain.catalog.entities import Video
from e_learning.domain.catalog.repository import FormationRepository, VideoRepository
from e_learning.domain.catalog.value_objects import FormationId


class IndexFormation:
    def __init__(
        self,
        formations: FormationRepository,
        videos: VideoRepository,
        index_video: IndexVideoContent,
    ) -> None:
        self._formations = formations
        self._videos = videos
        self._index_video = index_video

    async def execute(
        self,
        command: IndexFormationCommand,
        *,
        progress: ProgressReporter | None = None,
    ) -> IndexFormationResult:
        reporter = progress or NullProgressReporter()
        formation = await self._formations.get(FormationId.from_string(command.formation_id))
        videos = await self._videos.list_by_formation(formation.id)
        eligible = [
            v
            for v in videos
            if v.transcription_status == Video.AI_READY or v.summary_status == Video.AI_READY
        ]
        indexed_videos = 0
        indexed_chunks = 0
        total = max(len(eligible), 1)
        for i, video in enumerate(eligible):
            pct = int(i / total * 90)
            await reporter.set(pct, f"Indexation vidéo {i + 1}/{len(eligible)}…")
            n = await self._index_video.execute(IndexVideoCommand(video_id=str(video.id)))
            if n > 0:
                indexed_videos += 1
                indexed_chunks += n
        await reporter.set(100, f"{indexed_videos} vidéo(s), {indexed_chunks} chunk(s)")
        return IndexFormationResult(
            indexed_videos=indexed_videos,
            indexed_chunks=indexed_chunks,
        )
