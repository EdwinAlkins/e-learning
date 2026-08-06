"""Use case : progression agrégée d'une formation."""

from __future__ import annotations

from e_learning.application.learning.dto import (
    ChapterProgressDTO,
    FormationProgressDTO,
    VideoProgressDTO,
)
from e_learning.domain.catalog.repository import (
    ChapterRepository,
    FormationRepository,
    VideoRepository,
)
from e_learning.domain.catalog.value_objects import FormationId
from e_learning.domain.learning.repository import ProgressRepository
from e_learning.domain.user.value_objects import UserId


def progress_percentage(position: float, duration: float) -> float:
    if duration <= 0:
        return 0.0
    return min(100.0, max(0.0, (position / duration) * 100.0))


class GetFormationProgress:
    def __init__(
        self,
        formations: FormationRepository,
        chapters: ChapterRepository,
        videos: VideoRepository,
        progress: ProgressRepository,
    ) -> None:
        self._formations = formations
        self._chapters = chapters
        self._videos = videos
        self._progress = progress

    async def execute(self, *, user_id: str, formation_id: str) -> FormationProgressDTO:
        formation = await self._formations.get(FormationId.from_string(formation_id))
        uid = UserId.from_string(user_id)
        chapters = await self._chapters.list_by_formation(formation.id)
        all_videos = await self._videos.list_by_formation(formation.id)
        by_chapter: dict[str, list] = {}
        for video in all_videos:
            by_chapter.setdefault(str(video.chapter_id), []).append(video)
        progress_list = await self._progress.list_by_user_and_videos(
            uid, [v.id for v in all_videos]
        )
        pos_by_video = {str(p.video_id): p.last_position.value for p in progress_list}

        chapter_dtos: list[ChapterProgressDTO] = []
        chapter_pcts: list[float] = []
        for chapter in chapters:
            videos = by_chapter.get(str(chapter.id), [])
            video_dtos: list[VideoProgressDTO] = []
            video_pcts: list[float] = []
            for video in videos:
                pct = progress_percentage(
                    pos_by_video.get(str(video.id), 0.0), video.duration.value
                )
                video_pcts.append(pct)
                video_dtos.append(
                    VideoProgressDTO(
                        id=str(video.id), title=str(video.title), progress_percentage=pct
                    )
                )
            chapter_pct = sum(video_pcts) / len(video_pcts) if video_pcts else 0.0
            chapter_pcts.append(chapter_pct)
            chapter_dtos.append(
                ChapterProgressDTO(
                    name=str(chapter.name),
                    videos=video_dtos,
                    progress_percentage=chapter_pct,
                )
            )
        formation_pct = sum(chapter_pcts) / len(chapter_pcts) if chapter_pcts else 0.0
        return FormationProgressDTO(
            name=str(formation.name),
            chapters=chapter_dtos,
            progress_percentage=formation_pct,
        )
