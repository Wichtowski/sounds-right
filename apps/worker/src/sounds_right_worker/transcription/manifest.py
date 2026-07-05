from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime

from pydantic import BaseModel

from sounds_right_worker.audio.ffprobe import AudioProbeResult
from sounds_right_worker.transcription.schemas import Transcript


class ManifestArtifact(BaseModel):
    object_key: str
    content_type: str
    sha256: str


class ManifestArtifacts(BaseModel):
    transcript: ManifestArtifact


class ManifestEngine(BaseModel):
    name: str
    model: str


class ManifestAudio(BaseModel):
    duration_seconds: float
    codec_name: str
    sample_rate: int | None
    channels: int | None


class Manifest(BaseModel):
    schema_version: str
    track_version_id: uuid.UUID
    job_id: uuid.UUID
    status: str
    artifacts: ManifestArtifacts
    engine: ManifestEngine
    audio: ManifestAudio
    created_at: datetime


def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_manifest(
    *,
    schema_version: str,
    transcript: Transcript,
    transcript_object_key: str,
    transcript_sha256: str,
    probe: AudioProbeResult,
    created_at: datetime | None = None,
) -> Manifest:
    return Manifest(
        schema_version=schema_version,
        track_version_id=transcript.track_version_id,
        job_id=transcript.job_id,
        status="completed",
        artifacts=ManifestArtifacts(
            transcript=ManifestArtifact(
                object_key=transcript_object_key,
                content_type="application/json",
                sha256=transcript_sha256,
            ),
        ),
        engine=ManifestEngine(
            name=transcript.engine.name,
            model=transcript.engine.model,
        ),
        audio=ManifestAudio(
            duration_seconds=probe.duration_seconds,
            codec_name=probe.codec_name,
            sample_rate=probe.sample_rate,
            channels=probe.channels,
        ),
        created_at=created_at or datetime.now(UTC),
    )
