from __future__ import annotations

import uuid


def transcript_object_key(prefix: str, track_version_id: uuid.UUID) -> str:
    """Deterministic key for the normalized transcript document."""
    return f"{prefix}/{track_version_id}/transcript.json"


def manifest_object_key(prefix: str, track_version_id: uuid.UUID) -> str:
    """Deterministic key for the manifest document."""
    return f"{prefix}/{track_version_id}/manifest.json"


def input_extension(audio_object_key: str, fallback: str = "audio") -> str:
    """Extract a safe file extension from a temp audio object key."""
    tail = audio_object_key.rsplit("/", maxsplit=1)[-1]
    if "." not in tail:
        return fallback
    extension = tail.rsplit(".", maxsplit=1)[-1].lower()
    # Guard against absurd/unsafe extensions.
    if not extension.isalnum() or len(extension) > 8:
        return fallback
    return extension
