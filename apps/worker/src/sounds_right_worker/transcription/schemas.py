from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class TranscriptionOptions(BaseModel):
    language: str = "auto"
    model: str = "base"
    separate_vocals: bool = False


class WhisperCppResult(BaseModel):
    """Raw-ish parsed output returned by the whisper.cpp wrapper."""

    language: str
    segments: list[WhisperSegment]


class WhisperWord(BaseModel):
    word: str
    start: float
    end: float
    confidence: float | None = None


class WhisperSegment(BaseModel):
    start: float
    end: float
    text: str
    words: list[WhisperWord] = Field(default_factory=list)


class TranscriptEngine(BaseModel):
    name: str
    model: str
    language: str


class TranscriptMetadata(BaseModel):
    duration_seconds: float
    created_at: datetime
    word_count: int
    segment_count: int


class TranscriptWord(BaseModel):
    word: str
    start: float
    end: float
    confidence: float | None = None


class TranscriptSegment(BaseModel):
    id: int
    start: float
    end: float
    text: str
    words: list[TranscriptWord] = Field(default_factory=list)


class Transcript(BaseModel):
    schema_version: str
    track_version_id: uuid.UUID
    job_id: uuid.UUID
    engine: TranscriptEngine
    metadata: TranscriptMetadata
    text: str
    segments: list[TranscriptSegment]


WhisperCppResult.model_rebuild()
