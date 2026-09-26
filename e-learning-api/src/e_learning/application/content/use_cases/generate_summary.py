"""Use case : générer un résumé à partir de la transcription."""

from __future__ import annotations

from e_learning.application.content.dto import GenerateSummaryCommand, SummaryDTO
from e_learning.application.jobs.progress import NullProgressReporter, ProgressReporter
from e_learning.application.shared.errors import SummaryGenerationError
from e_learning.application.shared.media import MediaFilePort, SummaryPort
from e_learning.application.usage.record import record_llm_usage
from e_learning.domain.catalog.repository import VideoRepository
from e_learning.domain.catalog.value_objects import VideoId
from e_learning.domain.usage.entities import TokenUsage
from e_learning.domain.usage.repository import TokenUsageRepository


class GenerateSummary:
    def __init__(
        self,
        videos: VideoRepository,
        media_files: MediaFilePort,
        summary: SummaryPort,
        usage: TokenUsageRepository,
    ) -> None:
        self._videos = videos
        self._media_files = media_files
        self._summary = summary
        self._usage = usage

    async def execute(
        self,
        command: GenerateSummaryCommand,
        *,
        progress: ProgressReporter | None = None,
    ) -> SummaryDTO:
        reporter = progress or NullProgressReporter()
        video = await self._videos.get(VideoId.from_string(command.video_id))
        transcription_path = self._media_files.transcription_path(str(video.relative_path))
        transcription = self._media_files.read_text(transcription_path)
        if transcription is None:
            raise SummaryGenerationError(f"Aucune transcription pour la vidéo {command.video_id}.")
        await reporter.set(20, "Appel au modèle de résumé…")
        completion = await self._summary.generate(transcription)
        await record_llm_usage(
            self._usage,
            usage=completion.usage,
            kind=TokenUsage.KIND_SUMMARY,
            user_id=command.user_id,
        )
        text = completion.text
        await reporter.set(80, "Écriture du résumé…")
        out = self._media_files.summary_path(str(video.relative_path))
        self._media_files.write_text(out, text)
        await reporter.set(100, "Résumé terminé")
        return SummaryDTO(summary=text)
