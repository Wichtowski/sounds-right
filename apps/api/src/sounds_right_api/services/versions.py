from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from minio.error import S3Error
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from sounds_right_api.config import ApiSettings
from sounds_right_api.domain.schemas import (
    TrackVersionPublic,
    UploadCompleteRequest,
    UploadUrlRequest,
    UploadUrlResponse,
)
from sounds_right_api.models import Track, TrackVersion, UploadSession, User
from sounds_right_api.storage.minio_client import create_minio_client, create_public_minio_client


class VersionNotFoundError(Exception):
    pass


class VersionTrackNotFoundError(Exception):
    pass


class InvalidVersionStatusError(Exception):
    pass


class UploadObjectNotFoundError(Exception):
    pass


class UploadSessionNotFoundError(Exception):
    pass


class UploadTooLargeError(Exception):
    pass


async def create_track_version(
    session: AsyncSession,
    track_id: uuid.UUID,
    user: User,
) -> TrackVersionPublic:
    track = await session.scalar(select(Track).where(Track.id == track_id).with_for_update())
    if track is None:
        raise VersionTrackNotFoundError

    next_version = await session.scalar(
        select(func.coalesce(func.max(TrackVersion.version), 0) + 1).where(
            TrackVersion.track_id == track_id,
        ),
    )
    version = TrackVersion(
        track_id=track_id,
        version=int(next_version or 1),
        status="draft",
        created_by_user_id=user.id,
    )
    session.add(version)
    await session.commit()
    await session.refresh(version)
    return TrackVersionPublic.model_validate(version)


async def list_track_versions(
    session: AsyncSession,
    track_id: uuid.UUID,
) -> list[TrackVersionPublic]:
    versions = (
        await session.scalars(
            select(TrackVersion)
            .where(TrackVersion.track_id == track_id)
            .order_by(TrackVersion.version.desc()),
        )
    ).all()
    return [TrackVersionPublic.model_validate(version) for version in versions]


async def get_track_version(session: AsyncSession, version_id: uuid.UUID) -> TrackVersionPublic:
    version = await session.get(TrackVersion, version_id)
    if version is None:
        raise VersionNotFoundError
    return TrackVersionPublic.model_validate(version)


async def create_upload_url(
    session: AsyncSession,
    version_id: uuid.UUID,
    payload: UploadUrlRequest,
    settings: ApiSettings,
) -> UploadUrlResponse:
    if payload.size_bytes > settings.max_audio_upload_size_bytes:
        raise UploadTooLargeError

    version = await session.get(TrackVersion, version_id)
    if version is None:
        raise VersionNotFoundError
    if version.status != "draft":
        raise InvalidVersionStatusError

    extension = payload.filename.rsplit(".", maxsplit=1)[-1].lower()
    object_key = f"temp-audio/{version.id}/input.{extension}"
    expires_at = datetime.now(UTC) + timedelta(seconds=settings.upload_url_expires_seconds)

    upload_session = UploadSession(
        track_version_id=version.id,
        object_key=object_key,
        original_filename=payload.filename,
        content_type=payload.content_type,
        max_size_bytes=settings.max_audio_upload_size_bytes,
        expires_at=expires_at,
    )
    version.status = "upload_url_created"
    version.original_audio_filename = payload.filename
    version.audio_content_type = payload.content_type
    version.audio_size_bytes = payload.size_bytes
    session.add(upload_session)
    await session.commit()

    client = create_public_minio_client(settings)
    upload_url = client.presigned_put_object(
        settings.minio_temp_audio_bucket,
        object_key,
        expires=timedelta(seconds=settings.upload_url_expires_seconds),
    )

    return UploadUrlResponse(
        upload_url=upload_url,
        object_key=object_key,
        expires_in_seconds=settings.upload_url_expires_seconds,
        headers={"Content-Type": payload.content_type},
    )


async def complete_upload(
    session: AsyncSession,
    version_id: uuid.UUID,
    payload: UploadCompleteRequest,
    settings: ApiSettings,
) -> TrackVersionPublic:
    version = await session.get(TrackVersion, version_id)
    if version is None:
        raise VersionNotFoundError
    if version.status != "upload_url_created":
        raise InvalidVersionStatusError

    upload_session = await session.scalar(
        select(UploadSession).where(
            UploadSession.track_version_id == version.id,
            UploadSession.object_key == payload.object_key,
            UploadSession.completed_at.is_(None),
        ),
    )
    if upload_session is None:
        raise UploadSessionNotFoundError

    client = create_minio_client(settings)
    try:
        stat = client.stat_object(settings.minio_temp_audio_bucket, upload_session.object_key)
    except S3Error as exc:
        if exc.code in {"NoSuchKey", "NoSuchBucket", "NoSuchObject"}:
            raise UploadObjectNotFoundError from exc
        raise

    if stat.size and stat.size > upload_session.max_size_bytes:
        raise UploadTooLargeError

    upload_session.completed_at = datetime.now(UTC)
    version.status = "uploaded"
    version.temporary_audio_object_key = upload_session.object_key
    version.original_audio_filename = upload_session.original_filename
    version.audio_content_type = upload_session.content_type
    version.audio_size_bytes = stat.size
    await session.commit()
    await session.refresh(version)
    return TrackVersionPublic.model_validate(version)
