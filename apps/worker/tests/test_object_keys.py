from __future__ import annotations

import uuid

from sounds_right_worker.storage.object_keys import (
    input_extension,
    manifest_object_key,
    transcript_object_key,
)


def test_transcript_object_key_is_deterministic() -> None:
    version_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
    key = transcript_object_key("transcripts", version_id)
    assert key == "transcripts/11111111-1111-1111-1111-111111111111/transcript.json"
    assert key == transcript_object_key("transcripts", version_id)


def test_manifest_object_key_is_deterministic() -> None:
    version_id = uuid.UUID("22222222-2222-2222-2222-222222222222")
    key = manifest_object_key("transcripts", version_id)
    assert key == "transcripts/22222222-2222-2222-2222-222222222222/manifest.json"


def test_input_extension_from_key() -> None:
    assert input_extension("temp-audio/abc/input.mp3") == "mp3"
    assert input_extension("temp-audio/abc/input.WAV") == "wav"


def test_input_extension_falls_back_when_missing_or_unsafe() -> None:
    assert input_extension("temp-audio/abc/input") == "audio"
    assert input_extension("temp-audio/abc/input.superlongextension") == "audio"
