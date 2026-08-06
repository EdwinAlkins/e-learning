"""Use case : progression de toutes les formations."""

from __future__ import annotations

from collections import defaultdict

from e_learning.application.learning.dto import (
    ChapterProgressDTO,
    FormationProgressDTO,
    VideoProgressDTO,
)
from e_learning.application.learning.use_cases.get_formation_progress import progress_percentage
from e_learning.domain.catalog.repository import (
    ChapterRepository,
    FormationRepository,
    VideoRepository,
)
from e_learning.domain.learning.repository import ProgressRepository
from e_learning.domain.user.value_objects import UserId


class ListFormationsProgress:
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

    async def execute(self, *, user_id: str) -> dict[str, FormationProgressDTO]:
        uid = UserId.from_string(user_id)
        formations = await self._formations.list_all()
        chapters = await self._chapters.list_all()
        videos = await self._videos.list_all()
        progress_list = await self._progress.list_by_user_and_videos(uid, [v.id for v in videos])
        pos_by_video = {str(p.video_id): p.last_position.value for p in progress_list}

        chapters_by_formation: dict[str, list] = defaultdict(list)
        for chapter in chapters:
            chapters_by_formation[str(chapter.formation_id)].append(chapter)
        for group in chapters_by_formation.values():
            group.sort(key=lambda c: c.position.value)

        videos_by_chapter: dict[str, list] = defaultdict(list)
        for video in videos:
            videos_by_chapter[str(video.chapter_id)].append(video)
        for group in videos_by_chapter.values():
            group.sort(key=lambda v: v.position.value)

        result: dict[str, FormationProgressDTO] = {}
        for formation in formations:
            chapter_dtos: list[ChapterProgressDTO] = []
            chapter_pcts: list[float] = []
            for chapter in chapters_by_formation.get(str(formation.id), []):
                chapter_videos = videos_by_chapter.get(str(chapter.id), [])
                video_dtos: list[VideoProgressDTO] = []
                video_pcts: list[float] = []
                for video in chapter_videos:
                    pct = progress_percentage(
                        pos_by_video.get(str(video.id), 0.0), video.duration.value
                    )
                    video_pcts.append(pct)
                    video_dtos.append(
                        VideoProgressDTO(
                            id=str(video.id),
                            title=str(video.title),
                            progress_percentage=pct,
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
            result[str(formation.id)] = FormationProgressDTO(
                name=str(formation.name),
                chapters=chapter_dtos,
                progress_percentage=formation_pct,
            )
        return result
