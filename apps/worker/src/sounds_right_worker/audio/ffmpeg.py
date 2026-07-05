from __future__ import annotations

import asyncio
from pathlib import Path

from sounds_right_worker.errors import NORMALIZATION_FAILED, PipelineError
from sounds_right_worker.logging import get_logger

logger = get_logger(__name__)

_STAGE = "audio_normalization"


async def normalize_to_wav(
    ffmpeg_path: str,
    input_file: Path,
    output_file: Path,
) -> Path:
    """Convert input audio to 16 kHz mono pcm_s16le WAV for whisper.cpp."""
    args = [
        ffmpeg_path,
        "-y",
        "-i",
        str(input_file),
        "-ar",
        "16000",
        "-ac",
        "1",
        "-c:a",
        "pcm_s16le",
        str(output_file),
    ]
    process = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await process.communicate()
    if process.returncode != 0 or not output_file.exists():
        logger.error(
            "ffmpeg normalization failed",
            extra={"returncode": process.returncode, "stderr": stderr.decode(errors="replace")},
        )
        raise PipelineError(
            NORMALIZATION_FAILED,
            "Could not normalize audio for transcription",
            stage=_STAGE,
        )
    return output_file
