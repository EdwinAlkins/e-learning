"""Adaptateurs de génération de résumé."""

from __future__ import annotations

from e_learning.application.shared.errors import SummaryGenerationError
from e_learning.application.shared.media import SummaryPort
from e_learning.infrastructure.config import Settings


class OpenAPISummaryAdapter(SummaryPort):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def generate(self, transcription: str) -> str:
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            raise SummaryGenerationError(
                "Le paquet openai n'est pas installé (groupe de deps ai)."
            ) from exc

        client = AsyncOpenAI(
            base_url=self._settings.openai_base_url,
            api_key=self._settings.openai_api_key.get_secret_value(),
        )
        system = (
            "Tu es un assistant pédagogique pour une formation e-learning. "
            "Résume la transcription suivante en markdown structuré, "
            "en français, de façon concise et pédagogique."
        )
        user = f"Transcription :\n{transcription}"
        try:
            response = await client.chat.completions.create(
                model=self._settings.openai_model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            if not response.choices:
                raise SummaryGenerationError("Réponse LLM vide.")
            content = response.choices[0].message.content
            if not content:
                raise SummaryGenerationError("Réponse LLM vide.")
            return content
        except SummaryGenerationError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise SummaryGenerationError(str(exc)) from exc


class GeminiSummaryAdapter(SummaryPort):
    async def generate(self, transcription: str) -> str:
        import asyncio
        import tempfile
        from pathlib import Path

        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as tmp:
            tmp.write(transcription)
            tmp_path = Path(tmp.name)
        try:
            proc = await asyncio.create_subprocess_exec(
                "npx",
                "-y",
                "@google/gemini-cli",
                "-p",
                f"Résume en markdown pédagogique le fichier {tmp_path}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                raise SummaryGenerationError(stderr.decode() or "gemini-cli a échoué")
            return stdout.decode().strip()
        finally:
            tmp_path.unlink(missing_ok=True)
