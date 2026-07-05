from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .artists import ArtistSummary


class TrackCreate(BaseModel):
    artist_id: uuid.UUID
    title: str = Field(min_length=1, max_length=240)
    album: str | None = Field(default=None, max_length=240)


class TrackUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=240)
    album: str | None = Field(default=None, max_length=240)


class TrackPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    artist_id: uuid.UUID
    title: str
    album: str | None
    slug: str
    created_at: datetime
    updated_at: datetime
    artist: ArtistSummary | None = None


class TrackListResponse(BaseModel):
    items: list[TrackPublic]
    limit: int
    offset: int
