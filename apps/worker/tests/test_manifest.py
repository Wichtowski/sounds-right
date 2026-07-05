from __future__ import annotations

import uuid

from sounds_right_worker.audio.ffprobe import AudioProbeResult
from sounds_right_worker.transcription.manifest import build_manifest, compute_sha256
from sounds_right_worker.transcription.parser import build_transcript
from sounds_right_worker.transcription.whisper_cpp import parse_whisper_output

_WHISPER_JSON = """
{
  "result": {"language": "en"},
  "transcription": [
    {"offsets": {"from": 0, "to": 3250}, "text": " example lyric line"}
  ]
}
"""


def _transcript() -> object:
    result = parse_whisper_output(_WHISPER_JSON)
    return build_transcript(
        result,
        schema_version="1.0",
        track_version_id=uuid.uuid4(),
        job_id=uuid.uuid4(),
        engine_name="whisper.cpp",
        model="base",
        duration_seconds=3.25,
    )


def test_compute_sha256_is_stable() -> None:
    assert compute_sha256(b"hello") == compute_sha256(b"hello")
    assert compute_sha256(b"hello") != compute_sha256(b"world")


def test_build_manifest_includes_transcript_artifact() -> None:
    transcript = _transcript()
    probe = AudioProbeResult(
        duration_seconds=3.25,
        size_bytes=1000,
        format_name="mp3",
        codec_name="mp3",
        sample_rate=44100,
        channels=2,
    )
    transcript_bytes = transcript.model_dump_json().encode("utf-8")  # type: ignore[attr-defined]
    sha = compute_sha256(transcript_bytes)

    manifest = build_manifest(
        schema_version="1.0",
        transcript=transcript,  # type: ignore[arg-type]
        transcript_object_key="transcripts/x/transcript.json",
        transcript_sha256=sha,
        probe=probe,
    )

    assert manifest.status == "completed"
    assert manifest.artifacts.transcript.object_key == "transcripts/x/transcript.json"
    assert manifest.artifacts.transcript.sha256 == sha
    assert manifest.engine.name == "whisper.cpp"
    assert manifest.audio.codec_name == "mp3"
    assert manifest.audio.sample_rate == 44100
