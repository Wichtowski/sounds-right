from __future__ import annotations

import pytest

from sounds_right_worker.audio.ffprobe import AudioProbeResult, parse_ffprobe_output
from sounds_right_worker.audio.validation import AudioLimits, validate_audio
from sounds_right_worker.errors import (
    AUDIO_DURATION_TOO_LONG,
    AUDIO_TOO_LARGE,
    UNSUPPORTED_AUDIO_FORMAT,
    PipelineError,
)

_VALID_PROBE_JSON = """
{
  "format": {"duration": "213.42", "size": "5242880", "format_name": "mp3"},
  "streams": [
    {"codec_type": "audio", "codec_name": "mp3", "sample_rate": "44100", "channels": 2}
  ]
}
"""

_NO_AUDIO_JSON = """
{
  "format": {"duration": "10.0", "size": "1000", "format_name": "mov"},
  "streams": [{"codec_type": "video", "codec_name": "h264"}]
}
"""


def test_parse_ffprobe_output_extracts_fields() -> None:
    result = parse_ffprobe_output(_VALID_PROBE_JSON)
    assert result.duration_seconds == pytest.approx(213.42)
    assert result.size_bytes == 5242880
    assert result.codec_name == "mp3"
    assert result.sample_rate == 44100
    assert result.channels == 2


def test_parse_ffprobe_output_without_audio_stream_raises() -> None:
    with pytest.raises(PipelineError) as exc:
        parse_ffprobe_output(_NO_AUDIO_JSON)
    assert exc.value.error_code == UNSUPPORTED_AUDIO_FORMAT


def test_validate_audio_accepts_within_limits() -> None:
    probe = parse_ffprobe_output(_VALID_PROBE_JSON)
    validate_audio(probe, AudioLimits(max_size_bytes=10_000_000, max_duration_seconds=900))


def test_validate_audio_rejects_oversized_file() -> None:
    probe = AudioProbeResult(
        duration_seconds=10,
        size_bytes=200_000_000,
        format_name="mp3",
        codec_name="mp3",
        sample_rate=44100,
        channels=2,
    )
    with pytest.raises(PipelineError) as exc:
        validate_audio(probe, AudioLimits(max_size_bytes=104857600, max_duration_seconds=900))
    assert exc.value.error_code == AUDIO_TOO_LARGE


def test_validate_audio_rejects_long_duration() -> None:
    probe = AudioProbeResult(
        duration_seconds=1200,
        size_bytes=1000,
        format_name="mp3",
        codec_name="mp3",
        sample_rate=44100,
        channels=2,
    )
    with pytest.raises(PipelineError) as exc:
        validate_audio(probe, AudioLimits(max_size_bytes=104857600, max_duration_seconds=900))
    assert exc.value.error_code == AUDIO_DURATION_TOO_LONG
