from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path

from sounds_right_worker.errors import (
    TRANSCRIPT_PARSE_FAILED,
    WHISPER_CPP_FAILED,
    WHISPER_CPP_MISSING,
    PipelineError,
)
from sounds_right_worker.logging import get_logger
from sounds_right_worker.transcription.schemas import (
    TranscriptionOptions,
    WhisperCppResult,
    WhisperSegment,
)

logger = get_logger(__name__)

_STAGE = "transcription"
_OUTPUT_PREFIX = "whisper_output"


@dataclass(frozen=True)
class WhisperCppConfig:
    binary: Path
    model: Path
    threads: int
    timeout_seconds: int
    default_language: str


class WhisperCppEngine:
    def __init__(self, config: WhisperCppConfig) -> None:
        self._config = config

    def ensure_available(self) -> None:
        if not self._config.binary.exists():
            raise PipelineError(
                WHISPER_CPP_MISSING,
                "Transcription engine is not available",
                stage=_STAGE,
            )
        if not self._config.model.exists():
            raise PipelineError(
                WHISPER_CPP_MISSING,
                "Transcription model is not available",
                stage=_STAGE,
            )

    async def transcribe(
        self,
        input_wav: Path,
        output_dir: Path,
        options: TranscriptionOptions,
    ) -> WhisperCppResult:
        self.ensure_available()

        output_prefix = output_dir / _OUTPUT_PREFIX
        language = options.language or self._config.default_language

        args = [
            str(self._config.binary),
            "-m",
            str(self._config.model),
            "-f",
            str(input_wav),
            "-l",
            language,
            "-t",
            str(self._config.threads),
            "-oj",
            "-of",
            str(output_prefix),
        ]

        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            _, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self._config.timeout_seconds,
            )
        except TimeoutError as exc:
            process.kill()
            await process.wait()
            raise PipelineError(
                WHISPER_CPP_FAILED,
                "Transcription timed out",
                stage=_STAGE,
            ) from exc

        if process.returncode != 0:
            logger.error(
                "whisper.cpp failed",
                extra={
                    "returncode": process.returncode,
                    "stderr": stderr.decode(errors="replace"),
                },
            )
            raise PipelineError(
                WHISPER_CPP_FAILED,
                "Transcription engine failed",
                stage=_STAGE,
            )

        output_file = output_dir / f"{_OUTPUT_PREFIX}.json"
        if not output_file.exists():
            raise PipelineError(
                WHISPER_CPP_FAILED,
                "Transcription produced no output",
                stage=_STAGE,
            )

        return parse_whisper_output(output_file.read_text(encoding="utf-8"))


def parse_whisper_output(raw: str) -> WhisperCppResult:
    """Parse whisper.cpp ``-oj`` JSON output into a normalized result.

    Segment timestamps are derived from millisecond offsets. Word timestamps are
    intentionally left empty rather than fabricated from subword tokens.
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PipelineError(
            TRANSCRIPT_PARSE_FAILED,
            "Could not read transcription output",
            stage=_STAGE,
        ) from exc

    result = data.get("result") or {}
    language = str(result.get("language") or "unknown")

    raw_segments = data.get("transcription") or []
    segments: list[WhisperSegment] = []
    for entry in raw_segments:
        offsets = entry.get("offsets") or {}
        start_ms = offsets.get("from")
        end_ms = offsets.get("to")
        if start_ms is None or end_ms is None:
            continue
        text = str(entry.get("text", "")).strip()
        segments.append(
            WhisperSegment(
                start=float(start_ms) / 1000.0,
                end=float(end_ms) / 1000.0,
                text=text,
            )
        )

    return WhisperCppResult(language=language, segments=segments)
