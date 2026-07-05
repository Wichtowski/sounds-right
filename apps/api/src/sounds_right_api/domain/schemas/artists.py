from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ArtistCreate(BaseModel):
    display_name: str = Field(min_length=1, max_length=240)
    full_name: str | None = Field(default=None, max_length=320)


class ArtistUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=240)
    full_name: str | None = Field(default=None, max_length=320)


class ArtistPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    display_name: str
    full_name: str | None
    created_at: datetime
    updated_at: datetime


class ArtistListResponse(BaseModel):
    items: list[ArtistPublic]
    limit: int
    offset: int


class ArtistSummary(BaseModel):
    id: uuid.UUID
    slug: str
    display_name: str
