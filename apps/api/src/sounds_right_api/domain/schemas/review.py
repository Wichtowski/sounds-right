from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from .artists import ArtistSummary
from .common import TrackVersionStatus, TranscriptionJobStatus

ReviewQueueStatus = Literal["completed", "approved", "rejected", "failed"]
ReviewAction = Literal["approved", "rejected", "commented"]


class ReviewTrackSummary(BaseModel):
    id: uuid.UUID
    title: str
    slug: str
    album: str | None


class ReviewJobSummary(BaseModel):
    id: uuid.UUID
    status: TranscriptionJobStatus
    completed_at: datetime | None


class ReviewTranscriptSummary(BaseModel):
    duration_seconds: float | None
    word_count: int | None
    engine: str | None


class ReviewQueueItem(BaseModel):
    version_id: uuid.UUID
    track_id: uuid.UUID
    artist: ArtistSummary
    track: ReviewTrackSummary
    version: int
    status: TrackVersionStatus
    job: ReviewJobSummary | None
    summary: ReviewTranscriptSummary
    created_at: datetime
    updated_at: datetime


class ReviewQueueResponse(BaseModel):
    items: list[ReviewQueueItem]
    limit: int
    offset: int
    total: int


class ApproveVersionRequest(BaseModel):
    note: str | None = Field(default=None, max_length=2000)


class RejectVersionRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=2000)


class ReviewUserSummary(BaseModel):
    id: uuid.UUID
    username: str


class ReviewEventPublic(BaseModel):
    id: uuid.UUID
    action: ReviewAction
    reason: str | None
    reviewer: ReviewUserSummary
    created_at: datetime


class ReviewEventsResponse(BaseModel):
    items: list[ReviewEventPublic]
