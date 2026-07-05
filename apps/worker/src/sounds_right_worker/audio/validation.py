from __future__ import annotations

from dataclasses import dataclass

from sounds_right_worker.audio.ffprobe import AudioProbeResult
from sounds_right_worker.errors import (
    AUDIO_DURATION_TOO_LONG,
    AUDIO_TOO_LARGE,
    AUDIO_VALIDATION_FAILED,
    PipelineError,
)

_STAGE = "audio_validation"


@dataclass(frozen=True)
class AudioLimits:
    max_size_bytes: int
    max_duration_seconds: float


def validate_audio(probe: AudioProbeResult, limits: AudioLimits) -> None:
    """Enforce configured audio limits. Raises PipelineError on violation."""
    if probe.size_bytes <= 0:
        raise PipelineError(
            AUDIO_VALIDATION_FAILED,
            "Audio file size is invalid or zero",
            stage=_STAGE,
        )
    if probe.size_bytes > limits.max_size_bytes:
        raise PipelineError(
            AUDIO_TOO_LARGE,
            "Audio file exceeds the maximum allowed size",
            stage=_STAGE,
        )
    if probe.duration_seconds > limits.max_duration_seconds:
        raise PipelineError(
            AUDIO_DURATION_TOO_LONG,
            "Audio duration exceeds the maximum allowed length",
            stage=_STAGE,
        )
