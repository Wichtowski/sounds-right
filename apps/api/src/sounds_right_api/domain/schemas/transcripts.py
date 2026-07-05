from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class TranscriptWord(BaseModel):
    word: str
    start: float
    end: float
    confidence: float | None = None


class TranscriptSegment(BaseModel):
    id: int | str
    start: float
    end: float
    text: str
    words: list[TranscriptWord] = Field(default_factory=list)


class TranscriptEngine(BaseModel):
    name: str
    model: str | None = None
    language: str | None = None


class TranscriptMetadata(BaseModel):
    duration_seconds: float | None = None
    created_at: datetime | None = None
    word_count: int | None = None
    segment_count: int | None = None


class TranscriptDocument(BaseModel):
    schema_version: str
    track_version_id: uuid.UUID | None = None
    job_id: uuid.UUID | None = None
    engine: TranscriptEngine
    metadata: TranscriptMetadata
    text: str | None = None
    segments: list[TranscriptSegment] = Field(default_factory=list)
