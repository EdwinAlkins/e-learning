"""Use case : synchroniser le FS avec la base (par relative_path)."""

from __future__ import annotations

import asyncio
from pathlib import PurePosixPath

from e_learning.application.catalog.name_match import find_matching_video
from e_learning.application.shared.storage import CatalogStoragePort
from e_learning.domain.catalog.entities import Chapter, Document, Formation, Video
from e_learning.domain.catalog.repository import (
    ChapterRepository,
    DocumentRepository,
    FormationRepository,
    VideoRepository,
)
from e_learning.domain.catalog.value_objects import (
    ChapterName,
    DocumentTitle,
    DurationSeconds,
    FormationName,
    Position,
    RelativePath,
    Slug,
    VideoTitle,
)


class ReconcileCatalog:
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

    async def execute(self) -> None:
        scanned = await asyncio.to_thread(self._storage.scan)

        formations_by_slug = {str(f.slug): f for f in await self._formations.list_all()}
        chapters_by_key = {
            (str(c.formation_id), str(c.slug)): c for c in await self._chapters.list_all()
        }
        all_videos = await self._videos.list_all()
        videos_by_path = {str(v.relative_path): v for v in all_videos}
        videos_by_chapter_filename = {(str(v.chapter_id), v.filename): v for v in all_videos}
        all_docs = await self._documents.list_all()
        docs_by_path = {str(d.relative_path): d for d in all_docs}
        docs_by_chapter_filename = {(str(d.chapter_id), d.filename): d for d in all_docs}

        formations_to_upsert: list[Formation] = []
        chapters_to_upsert: list[Chapter] = []
        videos_to_upsert: list[Video] = []
        docs_to_upsert: list[Document] = []

        seen_video_paths: set[str] = set()
        seen_doc_paths: set[str] = set()
        seen_formation_slugs: set[str] = set()
        seen_chapter_keys: set[tuple[str, str]] = set()

        for s_formation in scanned:
            seen_formation_slugs.add(s_formation.slug)
            formation = formations_by_slug.get(s_formation.slug)
            if formation is None:
                formation = Formation.create(
                    name=FormationName(s_formation.slug),
                    slug=Slug(s_formation.slug),
                )
                formations_by_slug[s_formation.slug] = formation
            formations_to_upsert.append(formation)

            for chapter_index, s_chapter in enumerate(s_formation.chapters):
                key = (str(formation.id), s_chapter.slug)
                seen_chapter_keys.add(key)
                chapter = chapters_by_key.get(key)
                if chapter is None:
                    chapter = Chapter.create(
                        formation_id=formation.id,
                        name=ChapterName(s_chapter.slug),
                        position=Position(chapter_index),
                        slug=Slug(s_chapter.slug),
                    )
                    chapters_by_key[key] = chapter
                    chapters_to_upsert.append(chapter)
                elif chapter.position.value != chapter_index:
                    chapter.move_to(Position(chapter_index))
                    chapters_to_upsert.append(chapter)

                chapter_videos: list[Video] = []
                for video_index, s_video in enumerate(s_chapter.videos):
                    seen_video_paths.add(s_video.relative_path)
                    abs_path = self._storage.absolute_path(s_video.relative_path)
                    tx_ready = abs_path.with_suffix(".txt").is_file()
                    sum_ready = abs_path.with_suffix(".md").is_file()
                    existing = videos_by_path.get(s_video.relative_path)
                    if existing is None:
                        # Path obsolète après rename FS : même fichier dans le chapitre.
                        existing = videos_by_chapter_filename.get(
                            (str(chapter.id), s_video.filename)
                        )
                    # Sidecars FS = source de vérité. Un job « processing » sans fichier
                    # est conservé ; dès qu'un .txt/.md existe → ready (même si processing/failed).
                    if tx_ready:
                        tx_status = Video.AI_READY
                    elif (
                        existing is not None
                        and existing.transcription_status == Video.AI_PROCESSING
                    ):
                        tx_status = Video.AI_PROCESSING
                    else:
                        tx_status = Video.AI_NONE
                    if sum_ready:
                        sum_status = Video.AI_READY
                    elif existing is not None and existing.summary_status == Video.AI_PROCESSING:
                        sum_status = Video.AI_PROCESSING
                    else:
                        sum_status = Video.AI_NONE
                    if existing is None:
                        video = Video.create(
                            chapter_id=chapter.id,
                            title=VideoTitle(s_video.title),
                            filename=s_video.filename,
                            relative_path=RelativePath(s_video.relative_path),
                            position=Position(video_index),
                            duration=DurationSeconds(s_video.duration_seconds),
                            kind=getattr(s_video, "kind", Video.KIND_VIDEO),
                            processing_status=Video.STATUS_READY,
                            transcription_status=tx_status,
                            summary_status=sum_status,
                        )
                        videos_by_path[s_video.relative_path] = video
                        videos_by_chapter_filename[(str(chapter.id), s_video.filename)] = video
                        videos_to_upsert.append(video)
                        chapter_videos.append(video)
                    else:
                        changed = False
                        old_path = str(existing.relative_path)
                        old_chapter_key = (str(existing.chapter_id), existing.filename)
                        if (
                            existing.chapter_id != chapter.id
                            or old_path != s_video.relative_path
                        ):
                            existing.relocate(
                                chapter_id=chapter.id,
                                position=Position(video_index),
                                relative_path=RelativePath(s_video.relative_path),
                            )
                            changed = True
                        elif existing.position.value != video_index:
                            existing.move_to(Position(video_index))
                            changed = True
                        if abs(existing.duration.value - s_video.duration_seconds) > 0.01:
                            existing.update_duration(DurationSeconds(s_video.duration_seconds))
                            changed = True
                        scanned_kind = getattr(s_video, "kind", Video.KIND_VIDEO)
                        if existing.kind != scanned_kind:
                            existing.set_kind(scanned_kind)
                            changed = True
                        if existing.transcription_status != tx_status:
                            existing.set_transcription_status(tx_status)
                            changed = True
                        if existing.summary_status != sum_status:
                            existing.set_summary_status(sum_status)
                            changed = True
                        if old_path != s_video.relative_path:
                            videos_by_path.pop(old_path, None)
                            videos_by_path[s_video.relative_path] = existing
                        if old_chapter_key != (str(chapter.id), s_video.filename):
                            videos_by_chapter_filename.pop(old_chapter_key, None)
                            videos_by_chapter_filename[
                                (str(chapter.id), s_video.filename)
                            ] = existing
                        if changed:
                            videos_to_upsert.append(existing)
                        chapter_videos.append(existing)

                for doc_index, s_doc in enumerate(s_chapter.documents):
                    seen_doc_paths.add(s_doc.relative_path)
                    matched = find_matching_video(chapter_videos, s_doc.title)
                    if matched is None:
                        matched = find_matching_video(
                            chapter_videos, PurePosixPath(s_doc.filename).stem
                        )
                    target_video_id = matched.id if matched else None
                    existing_doc = docs_by_path.get(s_doc.relative_path)
                    if existing_doc is None:
                        existing_doc = docs_by_chapter_filename.get(
                            (str(chapter.id), s_doc.filename)
                        )
                    if existing_doc is None:
                        document = Document.create(
                            chapter_id=chapter.id,
                            title=DocumentTitle(s_doc.title),
                            filename=s_doc.filename,
                            relative_path=RelativePath(s_doc.relative_path),
                            position=Position(doc_index),
                            mime_type=s_doc.mime_type,
                            video_id=target_video_id,
                        )
                        docs_by_path[s_doc.relative_path] = document
                        docs_by_chapter_filename[(str(chapter.id), s_doc.filename)] = document
                        docs_to_upsert.append(document)
                    else:
                        changed = False
                        old_path = str(existing_doc.relative_path)
                        old_chapter_key = (str(existing_doc.chapter_id), existing_doc.filename)
                        if (
                            existing_doc.chapter_id != chapter.id
                            or old_path != s_doc.relative_path
                        ):
                            existing_doc.relocate(
                                chapter_id=chapter.id,
                                position=Position(doc_index),
                                relative_path=RelativePath(s_doc.relative_path),
                                filename=s_doc.filename,
                            )
                            changed = True
                        if existing_doc.video_id != target_video_id:
                            existing_doc.attach_video(target_video_id)
                            changed = True
                        if old_path != s_doc.relative_path:
                            docs_by_path.pop(old_path, None)
                            docs_by_path[s_doc.relative_path] = existing_doc
                        if old_chapter_key != (str(chapter.id), s_doc.filename):
                            docs_by_chapter_filename.pop(old_chapter_key, None)
                            docs_by_chapter_filename[
                                (str(chapter.id), s_doc.filename)
                            ] = existing_doc
                        if changed:
                            docs_to_upsert.append(existing_doc)

        await self._formations.upsert_many(formations_to_upsert)
        await self._chapters.upsert_many(chapters_to_upsert)
        await self._videos.upsert_many(videos_to_upsert)
        await self._documents.upsert_many(docs_to_upsert)

        for formation in await self._formations.list_all():
            if str(formation.slug) not in seen_formation_slugs:
                await self._formations.delete(formation.id)

        for video in await self._videos.list_all():
            if str(video.relative_path) not in seen_video_paths:
                await self._videos.delete(video.id)

        for document in await self._documents.list_all():
            if str(document.relative_path) not in seen_doc_paths:
                await self._documents.delete(document.id)

        # Chapitres orphelins (absents du FS). Notes/progress liées aux vidéos
        # cascade-supprimées ne sont pas soft-delete ici — risque métier documenté,
        # hors scope P0 (reconcile soft-delete notes plus tard).
        for chapter in await self._chapters.list_all():
            key = (str(chapter.formation_id), str(chapter.slug))
            if key not in seen_chapter_keys:
                await self._chapters.delete(chapter.id)
