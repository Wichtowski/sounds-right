from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

EventType = Literal[
    "transcription.requested",
    "transcription.started",
    "transcription.progress",
    "transcription.completed",
    "transcription.failed",
]


class TranscriptionOptionsPayload(BaseModel):
    language: str = "auto"
    model: str = "base"
    separate_vocals: bool = False


class TranscriptionRequestedPayload(BaseModel):
    job_id: uuid.UUID
    track_version_id: uuid.UUID
    track_id: uuid.UUID
    artist_id: uuid.UUID
    audio_object_key: str
    original_audio_filename: str
    audio_content_type: str
    audio_size_bytes: int
    engine: Literal["whisper.cpp"]
    options: TranscriptionOptionsPayload


class TranscriptionStartedPayload(BaseModel):
    job_id: uuid.UUID
    track_version_id: uuid.UUID
    worker_id: str
    engine: str
    message: str


class TranscriptionProgressPayload(BaseModel):
    job_id: uuid.UUID
    track_version_id: uuid.UUID
    progress: int = Field(ge=0, le=100)
    stage: str
    message: str


class TranscriptionCompletedPayload(BaseModel):
    job_id: uuid.UUID
    track_version_id: uuid.UUID
    transcript_object_key: str | None = None
    manifest_object_key: str | None = None
    duration_seconds: float | None = None
    word_count: int | None = None
    segment_count: int | None = None
    engine: str | None = None
    model: str | None = None
    language: str | None = None
    sha256: str | None = None
    message: str


class TranscriptionFailedPayload(BaseModel):
    job_id: uuid.UUID
    track_version_id: uuid.UUID
    error_code: str
    error_message: str
    retryable: bool


EventPayload = Annotated[
    TranscriptionRequestedPayload
    | TranscriptionStartedPayload
    | TranscriptionProgressPayload
    | TranscriptionCompletedPayload
    | TranscriptionFailedPayload,
    Field(discriminator=None),
]


class EventEnvelope(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    event_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    event_type: EventType
    event_version: int = 1
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    correlation_id: uuid.UUID
    causation_id: uuid.UUID | None = None
    producer: str
    payload: EventPayload


event_envelope_adapter: TypeAdapter[EventEnvelope] = TypeAdapter(EventEnvelope)
