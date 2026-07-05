from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path

from sounds_right_worker.errors import (
    AUDIO_VALIDATION_FAILED,
    UNSUPPORTED_AUDIO_FORMAT,
    PipelineError,
)
from sounds_right_worker.logging import get_logger

logger = get_logger(__name__)

_STAGE = "audio_validation"


@dataclass(frozen=True)
class AudioProbeResult:
    duration_seconds: float
    size_bytes: int
    format_name: str
    codec_name: str
    sample_rate: int | None
    channels: int | None


def parse_ffprobe_output(raw: str) -> AudioProbeResult:
    """Parse ``ffprobe -of json`` output into a typed result.

    Raises PipelineError when the payload lacks a usable audio stream or
    required fields.
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PipelineError(
            AUDIO_VALIDATION_FAILED,
            "Could not read audio metadata",
            stage=_STAGE,
        ) from exc

    fmt = data.get("format") or {}
    streams = data.get("streams") or []
    audio_streams = [s for s in streams if s.get("codec_type") == "audio"]
    if not audio_streams:
        raise PipelineError(
            UNSUPPORTED_AUDIO_FORMAT,
            "File does not contain an audio stream",
            stage=_STAGE,
        )

    audio = audio_streams[0]

    duration_raw = fmt.get("duration") or audio.get("duration")
    if duration_raw is None:
        raise PipelineError(
            AUDIO_VALIDATION_FAILED,
            "Audio duration is unavailable",
            stage=_STAGE,
        )
    try:
        duration_seconds = float(duration_raw)
    except (TypeError, ValueError) as exc:
        raise PipelineError(
            AUDIO_VALIDATION_FAILED,
            "Audio duration is invalid",
            stage=_STAGE,
        ) from exc

    size_raw = fmt.get("size")
    if size_raw is None:
        raise PipelineError(
            AUDIO_VALIDATION_FAILED,
            "Audio file size is unavailable",
            stage=_STAGE,
        )
    try:
        size_bytes = int(size_raw)
    except (TypeError, ValueError) as exc:
        raise PipelineError(
            AUDIO_VALIDATION_FAILED,
            "Audio file size is invalid",
            stage=_STAGE,
        ) from exc

    sample_rate = _safe_int(audio.get("sample_rate"))
    channels = _safe_int(audio.get("channels"))

    return AudioProbeResult(
        duration_seconds=duration_seconds,
        size_bytes=size_bytes,
        format_name=str(fmt.get("format_name", "unknown")),
        codec_name=str(audio.get("codec_name", "unknown")),
        sample_rate=sample_rate,
        channels=channels,
    )


def _safe_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


async def probe_audio(ffprobe_path: str, input_file: Path) -> AudioProbeResult:
    args = [
        ffprobe_path,
        "-v",
        "error",
        "-show_format",
        "-show_streams",
        "-of",
        "json",
        str(input_file),
    ]
    process = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        logger.error(
            "ffprobe failed",
            extra={"returncode": process.returncode, "stderr": stderr.decode(errors="replace")},
        )
        raise PipelineError(
            AUDIO_VALIDATION_FAILED,
            "Could not read audio metadata",
            stage=_STAGE,
        )
    return parse_ffprobe_output(stdout.decode(errors="replace"))
