from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .artists import ArtistSummary
from .review import ReviewTrackSummary
from .transcripts import TranscriptDocument

PublicationStatus = Literal["published", "unpublished", "superseded"]


class PublishVersionRequest(BaseModel):
    make_latest: bool = True


class UnpublishVersionRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=2000)


class PublicationUrls(BaseModel):
    manifest: str
    latest: str | None = None
    version: str


class PublicationPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    track_id: uuid.UUID
    track_version_id: uuid.UUID
    version: int
    status: PublicationStatus
    public_manifest_object_key: str
    public_latest_object_key: str | None
    public_transcript_object_key: str
    public_segments_object_key: str | None
    public_words_object_key: str | None
    public_urls: PublicationUrls
    published_by_user_id: uuid.UUID | None
    published_at: datetime | None
    unpublished_at: datetime | None
    created_at: datetime
    updated_at: datetime


class PublicationListResponse(BaseModel):
    items: list[PublicationPublic]
    limit: int
    offset: int
    total: int


class PublicKaraokeVersion(BaseModel):
    version: int
    publication_id: uuid.UUID
    status: PublicationStatus
    published_at: datetime | None
    manifest_url: str
    transcript_url: str


class PublicKaraokeManifest(BaseModel):
    schema_version: str = "1.0"
    artist: ArtistSummary
    track: ReviewTrackSummary
    latest_version: int | None
    versions: list[PublicKaraokeVersion]


class PublicKaraokeDocument(BaseModel):
    manifest: PublicKaraokeManifest
    transcript: TranscriptDocument
