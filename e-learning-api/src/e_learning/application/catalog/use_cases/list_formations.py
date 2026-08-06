"""Use case : lister les formations avec chapitres / vidéos."""

from __future__ import annotations

from collections import defaultdict

from e_learning.application.catalog.dto import (
    ChapterDTO,
    DocumentDTO,
    FormationDTO,
    JobDTO,
    VideoDTO,
)
from e_learning.domain.catalog.entities import Chapter, Document, Formation, Video
from e_learning.domain.catalog.job import Job
from e_learning.domain.catalog.repository import (
    ChapterRepository,
    DocumentRepository,
    FormationRepository,
    JobRepository,
    VideoRepository,
)


class ListFormations:
    def __init__(
        self,
        formations: FormationRepository,
        chapters: ChapterRepository,
        videos: VideoRepository,
        documents: DocumentRepository,
        jobs: JobRepository,
    ) -> None:
        self._formations = formations
        self._chapters = chapters
        self._videos = videos
        self._documents = documents
        self._jobs = jobs

    async def execute(self) -> list[FormationDTO]:
        formations = await self._formations.list_all()
        chapters = await self._chapters.list_all()
        videos = await self._videos.list_all()
        documents = await self._documents.list_all()
        active_jobs = await self._jobs.list_active()
        return self._assemble(formations, chapters, videos, documents, active_jobs)

    async def _build(self, formation: Formation) -> FormationDTO:
        chapters = await self._chapters.list_by_formation(formation.id)
        videos = await self._videos.list_by_formation(formation.id)
        chapter_ids = {str(c.id) for c in chapters}
        documents = [
            d for d in await self._documents.list_all() if str(d.chapter_id) in chapter_ids
        ]
        active_jobs = await self._jobs.list_active()
        return self._assemble([formation], chapters, videos, documents, active_jobs)[0]

    def _assemble(
        self,
        formations: list[Formation],
        chapters: list[Chapter],
        videos: list[Video],
        documents: list[Document],
        active_jobs: list[Job],
    ) -> list[FormationDTO]:
        chapters_by_formation: dict[str, list[Chapter]] = defaultdict(list)
        for chapter in chapters:
            chapters_by_formation[str(chapter.formation_id)].append(chapter)
        for group in chapters_by_formation.values():
            group.sort(key=lambda c: c.position.value)

        videos_by_chapter: dict[str, list[Video]] = defaultdict(list)
        for video in videos:
            videos_by_chapter[str(video.chapter_id)].append(video)
        for group in videos_by_chapter.values():
            group.sort(key=lambda v: v.position.value)

        docs_by_chapter: dict[str, list[Document]] = defaultdict(list)
        for document in documents:
            docs_by_chapter[str(document.chapter_id)].append(document)
        for group in docs_by_chapter.values():
            group.sort(key=lambda d: d.position.value)

        jobs_by_video: dict[str, list[JobDTO]] = defaultdict(list)
        for job in active_jobs:
            if job.video_id is not None:
                jobs_by_video[str(job.video_id)].append(JobDTO.from_entity(job))

        result: list[FormationDTO] = []
        for formation in formations:
            chapter_dtos: list[ChapterDTO] = []
            for chapter in chapters_by_formation.get(str(formation.id), []):
                chapter_dtos.append(
                    ChapterDTO(
                        id=str(chapter.id),
                        name=str(chapter.name),
                        slug=str(chapter.slug),
                        position=chapter.position.value,
                        videos=[
                            VideoDTO.from_entity(
                                v,
                                active_jobs=tuple(jobs_by_video.get(str(v.id), [])),
                            )
                            for v in videos_by_chapter.get(str(chapter.id), [])
                        ],
                        documents=[
                            DocumentDTO.from_entity(d)
                            for d in docs_by_chapter.get(str(chapter.id), [])
                        ],
                    )
                )
            result.append(FormationDTO.from_parts(formation, chapter_dtos))
        return result
