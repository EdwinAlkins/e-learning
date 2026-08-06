"""Adaptateur Whisper pour la transcription."""

from __future__ import annotations

import asyncio
from pathlib import Path

from e_learning.application.shared.errors import TranscriptionError
from e_learning.application.shared.media import TranscriptionPort


def _transcribe_sync(
    video_path: Path,
    *,
    model: str,
    language: str | None,
    with_timecodes: bool,
) -> str:
    import whisper  # type: ignore[import-untyped]

    wmodel = whisper.load_model(model)
    result = wmodel.transcribe(
        str(video_path),
        language=language,
        verbose=False,
    )
    if with_timecodes and "segments" in result:
        lines: list[str] = []
        for segment in result["segments"]:
            start = float(segment["start"])
            text = str(segment["text"]).strip()
            lines.append(f"[{start:.2f}] {text}")
        return "\n".join(lines)
    return str(result.get("text", "")).strip()


class WhisperTranscriptionAdapter(TranscriptionPort):
    async def transcribe(
        self,
        video_path: Path,
        *,
        model: str = "base",
        language: str | None = None,
        with_timecodes: bool = False,
    ) -> str:
        try:
            import whisper  # type: ignore[import-untyped]  # noqa: F401
        except ImportError as exc:
            raise TranscriptionError(
                "Le paquet openai-whisper n'est pas installé (groupe de deps ai)."
            ) from exc

        try:
            return await asyncio.to_thread(
                _transcribe_sync,
                video_path,
                model=model,
                language=language,
                with_timecodes=with_timecodes,
            )
        except TranscriptionError:
            raise
        except Exception as exc:  # noqa: BLE001 — surface as infra error
            raise TranscriptionError(str(exc)) from exc
