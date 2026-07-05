from __future__ import annotations

import uuid

import pytest

from sounds_right_worker.errors import TRANSCRIPT_PARSE_FAILED, PipelineError
from sounds_right_worker.transcription.parser import build_transcript
from sounds_right_worker.transcription.whisper_cpp import parse_whisper_output

_WHISPER_JSON = """
{
  "result": {"language": "en"},
  "transcription": [
    {"offsets": {"from": 0, "to": 3250}, "text": " example lyric line"},
    {"offsets": {"from": 3250, "to": 6000}, "text": " second line here"}
  ]
}
"""


def test_parse_whisper_output_builds_segments() -> None:
    result = parse_whisper_output(_WHISPER_JSON)
    assert result.language == "en"
    assert len(result.segments) == 2
    assert result.segments[0].start == pytest.approx(0.0)
    assert result.segments[0].end == pytest.approx(3.25)
    assert result.segments[0].text == "example lyric line"
    assert result.segments[0].words == []


def test_parse_whisper_output_invalid_json_raises() -> None:
    with pytest.raises(PipelineError) as exc:
        parse_whisper_output("{not json")
    assert exc.value.error_code == TRANSCRIPT_PARSE_FAILED


def test_build_transcript_normalizes_result() -> None:
    result = parse_whisper_output(_WHISPER_JSON)
    version_id = uuid.uuid4()
    job_id = uuid.uuid4()

    transcript = build_transcript(
        result,
        schema_version="1.0",
        track_version_id=version_id,
        job_id=job_id,
        engine_name="whisper.cpp",
        model="base",
        duration_seconds=6.0,
    )

    assert transcript.schema_version == "1.0"
    assert transcript.track_version_id == version_id
    assert transcript.job_id == job_id
    assert transcript.engine.language == "en"
    assert transcript.metadata.segment_count == 2
    assert transcript.metadata.word_count == 6
    assert transcript.text == "example lyric line second line here"
    assert transcript.segments[1].id == 1
