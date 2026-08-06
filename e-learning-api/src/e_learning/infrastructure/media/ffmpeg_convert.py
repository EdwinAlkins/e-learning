"""Adaptateur ffmpeg pour la conversion vidéo / audio."""

from __future__ import annotations

import json
import logging
import os
import subprocess
import tempfile
import time
from collections.abc import Callable
from pathlib import Path

import ffmpeg

from e_learning.application.shared.errors import MediaConversionError
from e_learning.application.shared.media import MediaConvertPort

logger = logging.getLogger("e_learning")


def _ffmpeg_stderr(exc: ffmpeg.Error) -> str:
    raw = exc.stderr
    if raw is None:
        return str(exc)
    if isinstance(raw, bytes):
        return raw.decode("utf-8", errors="replace").strip() or str(exc)
    return str(raw).strip() or str(exc)


def _probe_streams(path: Path) -> list[dict]:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_streams",
                "-of",
                "json",
                str(path),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return []
        payload = json.loads(result.stdout)
        streams = payload.get("streams")
        return streams if isinstance(streams, list) else []
    except FileNotFoundError, json.JSONDecodeError, OSError:
        return []


def _probe_duration_seconds(path: Path) -> float | None:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return None
        return float(result.stdout.strip())
    except FileNotFoundError, ValueError, OSError:
        return None


def needs_video_transcode(path: Path) -> bool:
    """True si le fichier n'est pas déjà un MP4 H.264 (+ AAC optionnel)."""
    if path.suffix.lower() != ".mp4":
        return True
    streams = _probe_streams(path)
    if not streams:
        return True
    video_codecs = {
        str(s.get("codec_name", "")).lower() for s in streams if s.get("codec_type") == "video"
    }
    audio_codecs = {
        str(s.get("codec_name", "")).lower() for s in streams if s.get("codec_type") == "audio"
    }
    if not video_codecs or not video_codecs.issubset({"h264"}):
        return True
    if audio_codecs and not audio_codecs.issubset({"aac"}):
        return True
    return False


def needs_audio_transcode(path: Path) -> bool:
    """True si le fichier n'est pas déjà un MP3."""
    if path.suffix.lower() != ".mp3":
        return True
    streams = _probe_streams(path)
    if not streams:
        return True
    audio_codecs = {
        str(s.get("codec_name", "")).lower() for s in streams if s.get("codec_type") == "audio"
    }
    return not audio_codecs or not audio_codecs.issubset({"mp3"})


def _run_ffmpeg_with_progress(
    stream: ffmpeg.Stream,
    *,
    label: str,
    source: Path,
    duration_hint: float | None = None,
    on_progress: Callable[[int], None] | None = None,
) -> None:
    """Exécute ffmpeg et journalise la progression (~toutes les 10 s / 5 %)."""
    duration = (
        duration_hint if duration_hint and duration_hint > 0 else _probe_duration_seconds(source)
    )
    cmd = stream.global_args("-progress", "pipe:1", "-nostats").compile()
    logger.info(
        "ffmpeg start %s (durée source ≈ %s)",
        label,
        f"{duration:.0f}s" if duration else "inconnue",
    )
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    assert process.stdout is not None
    last_log = 0.0
    last_pct = -1
    out_time_ms = 0
    try:
        for line in process.stdout:
            line = line.strip()
            if line.startswith("out_time_ms="):
                raw = line.split("=", 1)[1]
                try:
                    out_time_ms = int(raw)
                except ValueError:
                    continue
            elif line == "progress=end":
                break
            else:
                continue

            now = time.monotonic()
            pct = None
            if duration and duration > 0:
                pct = min(99, int((out_time_ms / 1_000_000) / duration * 100))
            should_log = now - last_log >= 10.0 or (pct is not None and pct >= last_pct + 5)
            if should_log:
                elapsed = out_time_ms / 1_000_000
                if pct is not None:
                    logger.info("ffmpeg %s : %s%% (%.0fs / %.0fs)", label, pct, elapsed, duration)
                    last_pct = pct
                    if on_progress is not None:
                        on_progress(pct)
                else:
                    logger.info("ffmpeg %s : %.0fs traités", label, elapsed)
                last_log = now

        stderr = process.stderr.read() if process.stderr else ""
        code = process.wait()
        if code != 0:
            raise MediaConversionError(
                f"Échec ffmpeg pour {source.name}: {(stderr or '').strip() or f'code={code}'}"
            )
        if on_progress is not None:
            on_progress(100)
        logger.info("ffmpeg %s : 100%% terminé", label)
    except Exception:
        process.kill()
        process.wait(timeout=30)
        raise


class FfmpegConvertAdapter(MediaConvertPort):
    def needs_video_transcode(self, path: Path) -> bool:
        return needs_video_transcode(path)

    def needs_audio_transcode(self, path: Path) -> bool:
        return needs_audio_transcode(path)

    def convert_to_mp4(
        self,
        source: Path,
        destination: Path,
        *,
        on_progress: Callable[[int], None] | None = None,
    ) -> None:
        """Ré-encode en H.264/AAC + faststart (lecture web)."""
        destination.parent.mkdir(parents=True, exist_ok=True)
        same_path = source.resolve() == destination.resolve()
        output = destination
        tmp_path: Path | None = None
        if same_path:
            fd, tmp_name = tempfile.mkstemp(
                suffix=".mp4", prefix=".__convert_", dir=str(destination.parent)
            )
            os.close(fd)
            tmp_path = Path(tmp_name)
            output = tmp_path

        try:
            stream = (
                ffmpeg.input(str(source))
                .output(
                    str(output),
                    vcodec="libx264",
                    acodec="aac",
                    pix_fmt="yuv420p",
                    preset="veryfast",
                    crf=23,
                    movflags="+faststart",
                )
                .overwrite_output()
            )
            _run_ffmpeg_with_progress(
                stream, label=source.name, source=source, on_progress=on_progress
            )
            if tmp_path is not None:
                tmp_path.replace(destination)
        except MediaConversionError:
            if tmp_path is not None and tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
            raise
        except ffmpeg.Error as exc:
            if tmp_path is not None and tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
            detail = _ffmpeg_stderr(exc)
            raise MediaConversionError(f"Échec ffmpeg pour {source.name}: {detail}") from exc
        except Exception:
            if tmp_path is not None and tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
            raise

    def convert_to_mp3(
        self,
        source: Path,
        destination: Path,
        *,
        on_progress: Callable[[int], None] | None = None,
    ) -> None:
        """Ré-encode en MP3 (libmp3lame)."""
        destination.parent.mkdir(parents=True, exist_ok=True)
        same_path = source.resolve() == destination.resolve()
        output = destination
        tmp_path: Path | None = None
        if same_path:
            fd, tmp_name = tempfile.mkstemp(
                suffix=".mp3", prefix=".__convert_", dir=str(destination.parent)
            )
            os.close(fd)
            tmp_path = Path(tmp_name)
            output = tmp_path

        try:
            stream = ffmpeg.input(str(source))
            stream = ffmpeg.output(
                stream.audio,
                str(output),
                acodec="libmp3lame",
                audio_bitrate="192k",
            ).overwrite_output()
            _run_ffmpeg_with_progress(
                stream, label=source.name, source=source, on_progress=on_progress
            )
            if tmp_path is not None:
                tmp_path.replace(destination)
        except MediaConversionError:
            if tmp_path is not None and tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
            raise
        except ffmpeg.Error as exc:
            if tmp_path is not None and tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
            detail = _ffmpeg_stderr(exc)
            raise MediaConversionError(f"Échec ffmpeg audio pour {source.name}: {detail}") from exc
        except Exception:
            if tmp_path is not None and tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
            raise
