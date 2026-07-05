from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .common import ALLOWED_AUDIO_CONTENT_TYPES, ALLOWED_AUDIO_EXTENSIONS, TrackVersionStatus


class TrackVersionCreate(BaseModel):
    notes: str | None = None


class TrackVersionPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    track_id: uuid.UUID
    version: int
    status: TrackVersionStatus
    temporary_audio_object_key: str | None
    original_audio_filename: str | None
    audio_content_type: str | None
    audio_size_bytes: int | None
    transcript_object_key: str | None = None
    manifest_object_key: str | None = None
    transcript_sha256: str | None = None
    duration_seconds: float | None = None
    word_count: int | None = None
    approved_at: datetime | None = None
    approved_by_user_id: uuid.UUID | None = None
    rejected_at: datetime | None = None
    rejected_by_user_id: uuid.UUID | None = None
    rejection_reason: str | None = None
    created_at: datetime
    updated_at: datetime


class UploadUrlRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=260)
    content_type: str
    size_bytes: int = Field(gt=0)

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, value: str) -> str:
        if value not in ALLOWED_AUDIO_CONTENT_TYPES:
            raise ValueError("Unsupported audio content type")
        return value

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, value: str) -> str:
        extension = value.rsplit(".", maxsplit=1)[-1].lower() if "." in value else ""
        if extension not in ALLOWED_AUDIO_EXTENSIONS:
            raise ValueError("Unsupported audio file extension")
        return value


class UploadUrlResponse(BaseModel):
    upload_url: str
    method: Literal["PUT"] = "PUT"
    object_key: str
    expires_in_seconds: int
    headers: dict[str, str]


class UploadCompleteRequest(BaseModel):
    object_key: str = Field(min_length=1)
