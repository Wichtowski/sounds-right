from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sounds_right_api.db.base import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="user",
        server_default="user",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )


class Artist(Base, TimestampMixin):
    __tablename__ = "artists"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(240), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(320), nullable=True)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    tracks: Mapped[list[Track]] = relationship(back_populates="artist")


class Track(Base, TimestampMixin):
    __tablename__ = "tracks"
    __table_args__ = (UniqueConstraint("artist_id", "slug", name="uq_tracks_artist_slug"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    artist_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("artists.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    album: Mapped[str | None] = mapped_column(String(240), nullable=True)
    slug: Mapped[str] = mapped_column(String(160), nullable=False)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    artist: Mapped[Artist] = relationship(back_populates="tracks")
    versions: Mapped[list[TrackVersion]] = relationship(back_populates="track")


class TrackVersion(Base, TimestampMixin):
    __tablename__ = "track_versions"
    __table_args__ = (
        UniqueConstraint("track_id", "version", name="uq_track_versions_track_version"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    track_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tracks.id"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="draft",
        server_default="draft",
    )
    temporary_audio_object_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    original_audio_filename: Mapped[str | None] = mapped_column(Text, nullable=True)
    audio_content_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    audio_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    transcript_object_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    manifest_object_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    transcript_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    transcript_schema_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(nullable=True)
    word_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    track: Mapped[Track] = relationship(back_populates="versions")
    upload_sessions: Mapped[list[UploadSession]] = relationship(back_populates="track_version")
    transcription_jobs: Mapped[list[TranscriptionJob]] = relationship(
        back_populates="track_version",
    )
    review_events: Mapped[list[ReviewEvent]] = relationship(back_populates="track_version")
    publications: Mapped[list[Publication]] = relationship(back_populates="track_version")


class UploadSession(Base):
    __tablename__ = "upload_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    track_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("track_versions.id"),
        nullable=False,
    )
    object_key: Mapped[str] = mapped_column(Text, nullable=False)
    original_filename: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False)
    max_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    track_version: Mapped[TrackVersion] = relationship(back_populates="upload_sessions")


class TranscriptionJob(Base, TimestampMixin):
    __tablename__ = "transcription_jobs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    track_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("track_versions.id"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    engine: Mapped[str] = mapped_column(String(80), nullable=False)
    progress: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    error_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    correlation_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    requested_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    track_version: Mapped[TrackVersion] = relationship(back_populates="transcription_jobs")
    events: Mapped[list[JobEvent]] = relationship(back_populates="job")


class JobEvent(Base):
    __tablename__ = "job_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("transcription_jobs.id"),
        nullable=False,
    )
    event_id: Mapped[uuid.UUID] = mapped_column(unique=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    payload_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    job: Mapped[TranscriptionJob] = relationship(back_populates="events")


class ReviewEvent(Base):
    __tablename__ = "review_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    track_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("track_versions.id"),
        nullable=False,
    )
    reviewer_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    track_version: Mapped[TrackVersion] = relationship(back_populates="review_events")
    reviewer: Mapped[User] = relationship()


class Publication(Base, TimestampMixin):
    __tablename__ = "publications"
    __table_args__ = (
        UniqueConstraint("track_version_id", name="uq_publications_track_version_id"),
        UniqueConstraint("track_id", "version", name="uq_publications_track_version"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    track_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tracks.id"), nullable=False)
    track_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("track_versions.id"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    public_manifest_object_key: Mapped[str] = mapped_column(Text, nullable=False)
    public_latest_object_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    public_transcript_object_key: Mapped[str] = mapped_column(Text, nullable=False)
    public_segments_object_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    public_words_object_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    unpublished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    track: Mapped[Track] = relationship()
    track_version: Mapped[TrackVersion] = relationship(back_populates="publications")
    published_by: Mapped[User | None] = relationship()
