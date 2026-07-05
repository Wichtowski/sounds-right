from __future__ import annotations

import uuid
from typing import cast

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from sounds_right_api.domain.schemas import (
    JobEventPublic,
    StartTranscriptionRequest,
    StartTranscriptionResponse,
    TranscriptionJobPublic,
)
from sounds_right_api.events.producer import EventProducer
from sounds_right_api.events.schemas import (
    EventEnvelope,
    TranscriptionOptionsPayload,
    TranscriptionRequestedPayload,
)
from sounds_right_api.models import JobEvent, TrackVersion, TranscriptionJob, User

ACTIVE_JOB_STATUSES = {"queued", "started", "processing"}


class JobNotFoundError(Exception):
    pass


class VersionNotFoundError(Exception):
    pass


class VersionNotUploadedError(Exception):
    pass


class ActiveJobExistsError(Exception):
    pass


class MissingAudioObjectError(Exception):
    pass


async def start_transcription(
    session: AsyncSession,
    version_id: uuid.UUID,
    payload: StartTranscriptionRequest,
    user: User,
    producer: EventProducer,
) -> StartTranscriptionResponse:
    version = await session.scalar(
        select(TrackVersion)
        .where(TrackVersion.id == version_id)
        .options(selectinload(TrackVersion.track)),
    )
    if version is None:
        raise VersionNotFoundError
    if version.status != "uploaded":
        raise VersionNotUploadedError
    if not version.temporary_audio_object_key:
        raise MissingAudioObjectError
    if (
        version.original_audio_filename is None
        or version.audio_content_type is None
        or version.audio_size_bytes is None
    ):
        raise MissingAudioObjectError

    active_job = await session.scalar(
        select(TranscriptionJob).where(
            TranscriptionJob.track_version_id == version.id,
            TranscriptionJob.status.in_(ACTIVE_JOB_STATUSES),
        ),
    )
    if active_job is not None:
        raise ActiveJobExistsError

    job = TranscriptionJob(
        track_version_id=version.id,
        status="queued",
        engine=payload.engine,
        progress=0,
        correlation_id=uuid.uuid4(),
        requested_by_user_id=user.id,
    )
    version.status = "queued_for_processing"
    session.add(job)
    await session.flush()

    event = EventEnvelope(
        event_type="transcription.requested",
        correlation_id=job.correlation_id,
        producer="sounds-right-api",
        payload=TranscriptionRequestedPayload(
            job_id=job.id,
            track_version_id=version.id,
            track_id=version.track_id,
            artist_id=version.track.artist_id,
            audio_object_key=version.temporary_audio_object_key,
            original_audio_filename=version.original_audio_filename,
            audio_content_type=version.audio_content_type,
            audio_size_bytes=version.audio_size_bytes,
            engine=payload.engine,
            options=TranscriptionOptionsPayload(**payload.options.model_dump()),
        ),
    )
    session.add(
        JobEvent(
            job_id=job.id,
            event_id=event.event_id,
            event_type=event.event_type,
            payload_json=cast(
                dict[str, object],
                event.payload.model_dump(mode="json"),
            ),
        ),
    )
    await session.commit()

    await producer.publish(event, job.id)

    return StartTranscriptionResponse(
        job_id=job.id,
        track_version_id=version.id,
        status="queued",
        correlation_id=job.correlation_id,
    )


async def get_job(session: AsyncSession, job_id: uuid.UUID) -> TranscriptionJobPublic:
    job = await session.get(TranscriptionJob, job_id)
    if job is None:
        raise JobNotFoundError
    return TranscriptionJobPublic.model_validate(job)


async def list_job_events(session: AsyncSession, job_id: uuid.UUID) -> list[JobEventPublic]:
    exists = await session.get(TranscriptionJob, job_id)
    if exists is None:
        raise JobNotFoundError

    statement: Select[tuple[JobEvent]] = (
        select(JobEvent).where(JobEvent.job_id == job_id).order_by(JobEvent.created_at)
    )
    events = (await session.scalars(statement)).all()
    return [
        JobEventPublic(
            event_id=event.event_id,
            event_type=event.event_type,
            created_at=event.created_at,
            payload=event.payload_json,
        )
        for event in events
    ]
