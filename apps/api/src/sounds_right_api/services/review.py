from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from typing import Any

from minio.error import S3Error
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from sounds_right_api.config import ApiSettings
from sounds_right_api.domain.schemas import (
    ArtistSummary,
    ReviewEventPublic,
    ReviewJobSummary,
    ReviewQueueItem,
    ReviewQueueResponse,
    ReviewQueueStatus,
    ReviewTrackSummary,
    ReviewTranscriptSummary,
    ReviewUserSummary,
    TrackVersionPublic,
    TranscriptDocument,
)
from sounds_right_api.models import ReviewEvent, Track, TrackVersion, TranscriptionJob, User
from sounds_right_api.storage.minio_client import create_minio_client

REVIEWER_ROLES = {"reviewer", "admin"}
REVIEWABLE_STATUS = "completed"


class VersionNotFoundError(Exception):
    pass


class VersionNotReviewableError(Exception):
    pass


class TranscriptMissingError(Exception):
    pass


class TranscriptStorageError(Exception):
    pass


class ForbiddenReviewActionError(Exception):
    pass


def ensure_reviewer(user: User) -> None:
    if user.role not in REVIEWER_ROLES:
        raise ForbiddenReviewActionError


async def list_review_queue(
    session: AsyncSession,
    status: ReviewQueueStatus,
    limit: int,
    offset: int,
) -> ReviewQueueResponse:
    total = await session.scalar(
        select(func.count()).select_from(TrackVersion).where(TrackVersion.status == status),
    )
    statement: Select[tuple[TrackVersion]] = (
        select(TrackVersion)
        .where(TrackVersion.status == status)
        .options(
            selectinload(TrackVersion.track).selectinload(Track.artist),
            selectinload(TrackVersion.transcription_jobs),
        )
        .order_by(TrackVersion.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )
    versions = (await session.scalars(statement)).all()

    return ReviewQueueResponse(
        items=[_review_queue_item(version) for version in versions],
        limit=limit,
        offset=offset,
        total=int(total or 0),
    )


async def get_transcript(
    session: AsyncSession,
    version_id: uuid.UUID,
    settings: ApiSettings,
) -> TranscriptDocument:
    version = await session.get(TrackVersion, version_id)
    if version is None:
        raise VersionNotFoundError
    if not version.transcript_object_key:
        raise TranscriptMissingError

    client = create_minio_client(settings)
    try:
        response = client.get_object(
            settings.minio_transcripts_bucket,
            version.transcript_object_key,
        )
        try:
            body = response.read()
        finally:
            response.close()
            response.release_conn()
    except S3Error as exc:
        if exc.code in {"NoSuchKey", "NoSuchBucket", "NoSuchObject"}:
            raise TranscriptMissingError from exc
        raise TranscriptStorageError from exc

    try:
        return TranscriptDocument.model_validate(json.loads(body.decode("utf-8")))
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
        raise TranscriptStorageError from exc


async def approve_version(
    session: AsyncSession,
    version_id: uuid.UUID,
    user: User,
    note: str | None,
    settings: ApiSettings,
) -> TrackVersionPublic:
    ensure_reviewer(user)
    version = await _get_reviewable_version(session, version_id)
    await _ensure_transcript_exists(version, settings)

    now = datetime.now(UTC)
    version.status = "approved"
    version.approved_at = now
    version.approved_by_user_id = user.id
    version.rejected_at = None
    version.rejected_by_user_id = None
    version.rejection_reason = None
    session.add(
        ReviewEvent(
            track_version_id=version.id,
            reviewer_user_id=user.id,
            action="approved",
            reason=note,
            metadata_json=None,
        ),
    )
    await session.commit()
    await session.refresh(version)
    return TrackVersionPublic.model_validate(version)


async def reject_version(
    session: AsyncSession,
    version_id: uuid.UUID,
    user: User,
    reason: str,
) -> TrackVersionPublic:
    ensure_reviewer(user)
    version = await _get_reviewable_version(session, version_id)

    now = datetime.now(UTC)
    version.status = "rejected"
    version.rejected_at = now
    version.rejected_by_user_id = user.id
    version.rejection_reason = reason
    version.approved_at = None
    version.approved_by_user_id = None
    session.add(
        ReviewEvent(
            track_version_id=version.id,
            reviewer_user_id=user.id,
            action="rejected",
            reason=reason,
            metadata_json=None,
        ),
    )
    await session.commit()
    await session.refresh(version)
    return TrackVersionPublic.model_validate(version)


async def list_review_events(
    session: AsyncSession,
    version_id: uuid.UUID,
) -> list[ReviewEventPublic]:
    version = await session.get(TrackVersion, version_id)
    if version is None:
        raise VersionNotFoundError

    statement: Select[tuple[ReviewEvent]] = (
        select(ReviewEvent)
        .where(ReviewEvent.track_version_id == version_id)
        .options(selectinload(ReviewEvent.reviewer))
        .order_by(ReviewEvent.created_at)
    )
    events = (await session.scalars(statement)).all()
    return [
        ReviewEventPublic(
            id=event.id,
            action=event.action,  # type: ignore[arg-type]
            reason=event.reason,
            reviewer=ReviewUserSummary(
                id=event.reviewer.id,
                username=event.reviewer.username,
            ),
            created_at=event.created_at,
        )
        for event in events
    ]


async def _get_reviewable_version(
    session: AsyncSession,
    version_id: uuid.UUID,
) -> TrackVersion:
    version = await session.get(TrackVersion, version_id, with_for_update=True)
    if version is None:
        raise VersionNotFoundError
    if version.status != REVIEWABLE_STATUS:
        raise VersionNotReviewableError
    return version


async def _ensure_transcript_exists(version: TrackVersion, settings: ApiSettings) -> None:
    if not version.transcript_object_key:
        raise TranscriptMissingError

    client = create_minio_client(settings)
    try:
        client.stat_object(settings.minio_transcripts_bucket, version.transcript_object_key)
    except S3Error as exc:
        if exc.code in {"NoSuchKey", "NoSuchBucket", "NoSuchObject"}:
            raise TranscriptMissingError from exc
        raise TranscriptStorageError from exc


def _review_queue_item(version: TrackVersion) -> ReviewQueueItem:
    latest_job = _latest_job(version.transcription_jobs)
    return ReviewQueueItem(
        version_id=version.id,
        track_id=version.track_id,
        artist=ArtistSummary(
            id=version.track.artist.id,
            slug=version.track.artist.slug,
            display_name=version.track.artist.display_name,
        ),
        track=ReviewTrackSummary(
            id=version.track.id,
            title=version.track.title,
            slug=version.track.slug,
            album=version.track.album,
        ),
        version=version.version,
        status=version.status,  # type: ignore[arg-type]
        job=(
            ReviewJobSummary(
                id=latest_job.id,
                status=latest_job.status,  # type: ignore[arg-type]
                completed_at=latest_job.completed_at,
            )
            if latest_job is not None
            else None
        ),
        summary=ReviewTranscriptSummary(
            duration_seconds=version.duration_seconds,
            word_count=version.word_count,
            engine=latest_job.engine if latest_job is not None else None,
        ),
        created_at=version.created_at,
        updated_at=version.updated_at,
    )


def _latest_job(jobs: list[TranscriptionJob]) -> TranscriptionJob | None:
    def sort_key(job: TranscriptionJob) -> tuple[datetime | Any, uuid.UUID]:
        return (job.completed_at or job.started_at or job.created_at, job.id)

    return max(jobs, key=sort_key) if jobs else None
