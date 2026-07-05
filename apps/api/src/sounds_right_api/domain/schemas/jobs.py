from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .common import TranscriptionJobStatus


class TranscriptionOptions(BaseModel):
    language: str = Field(default="auto", min_length=1, max_length=32)
    model: str = Field(default="base", min_length=1, max_length=80)
    separate_vocals: bool = False


class StartTranscriptionRequest(BaseModel):
    engine: Literal["whisper.cpp"] = "whisper.cpp"
    options: TranscriptionOptions = Field(default_factory=TranscriptionOptions)


class StartTranscriptionResponse(BaseModel):
    job_id: uuid.UUID
    track_version_id: uuid.UUID
    status: Literal["queued"]
    correlation_id: uuid.UUID


class TranscriptionJobPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    track_version_id: uuid.UUID
    status: TranscriptionJobStatus
    engine: str
    progress: int
    error_code: str | None
    error_message: str | None
    correlation_id: uuid.UUID
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


class JobEventPublic(BaseModel):
    event_id: uuid.UUID
    event_type: str
    created_at: datetime
    payload: dict[str, object]


class JobEventsResponse(BaseModel):
    job_id: uuid.UUID
    events: list[JobEventPublic]
