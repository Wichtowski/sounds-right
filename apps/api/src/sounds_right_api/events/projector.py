from __future__ import annotations

import asyncio
import contextlib
import logging
from datetime import UTC, datetime
from typing import cast

from aiokafka import AIOKafkaConsumer  # type: ignore[import-untyped]
from litestar import Litestar
from sqlalchemy import select

from sounds_right_api.config import get_settings
from sounds_right_api.db.session import SessionLocal
from sounds_right_api.events.schemas import (
    EventEnvelope,
    TranscriptionCompletedPayload,
    TranscriptionFailedPayload,
    TranscriptionProgressPayload,
    TranscriptionStartedPayload,
    event_envelope_adapter,
)
from sounds_right_api.models import JobEvent, TrackVersion, TranscriptionJob

logger = logging.getLogger(__name__)
projector_task: asyncio.Task[None] | None = None


async def start_projector(app: Litestar) -> None:
    settings = get_settings()
    if not settings.api_enable_projector:
        return
    global projector_task
    projector_task = asyncio.create_task(run_projector())
    app.state.projector_task = projector_task


async def stop_projector(app: Litestar) -> None:
    task = getattr(app.state, "projector_task", None)
    if task is None:
        return
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task


async def run_projector() -> None:
    settings = get_settings()
    consumer = AIOKafkaConsumer(
        settings.kafka_topic,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        client_id=f"{settings.kafka_client_id}-projector",
        group_id=settings.kafka_api_consumer_group,
        auto_offset_reset="earliest",
    )
    await consumer.start()
    try:
        async for message in consumer:
            try:
                event = event_envelope_adapter.validate_json(message.value)
            except Exception:
                logger.exception("skipping malformed event")
                continue
            if event.event_type not in {
                "transcription.started",
                "transcription.progress",
                "transcription.completed",
                "transcription.failed",
            }:
                continue
            await project_event(event)
    finally:
        await consumer.stop()


async def project_event(event: EventEnvelope) -> None:
    async with SessionLocal() as session:
        duplicate = await session.scalar(
            select(JobEvent.id).where(JobEvent.event_id == event.event_id),
        )
        if duplicate is not None:
            logger.info(
                "skipped duplicate event",
                extra={"event_id": str(event.event_id), "event_type": event.event_type},
            )
            return

        payload = event.payload
        if not isinstance(
            payload,
            (
                TranscriptionStartedPayload,
                TranscriptionProgressPayload,
                TranscriptionCompletedPayload,
                TranscriptionFailedPayload,
            ),
        ):
            return

        job = await session.get(TranscriptionJob, payload.job_id)
        if job is None:
            logger.error(
                "event references missing job",
                extra={"event_id": str(event.event_id), "job_id": str(payload.job_id)},
            )
            return
        if job.status in {"completed", "failed"} and event.event_type in {
            "transcription.started",
            "transcription.progress",
        }:
            return

        version = await session.get(TrackVersion, payload.track_version_id)
        if version is None:
            logger.error(
                "event references missing track version",
                extra={
                    "event_id": str(event.event_id),
                    "track_version_id": str(payload.track_version_id),
                },
            )
            return

        now = datetime.now(UTC)
        if isinstance(payload, TranscriptionStartedPayload):
            job.status = "started"
            job.started_at = now
            version.status = "processing"
        elif isinstance(payload, TranscriptionProgressPayload):
            job.status = "processing"
            job.progress = max(job.progress, payload.progress)
            version.status = "processing"
        elif isinstance(payload, TranscriptionCompletedPayload):
            job.status = "completed"
            job.progress = 100
            job.completed_at = now
            version.status = "completed"
            version.transcript_object_key = payload.transcript_object_key
            version.manifest_object_key = payload.manifest_object_key
            version.duration_seconds = payload.duration_seconds
            version.word_count = payload.word_count
            version.transcript_sha256 = payload.sha256
        elif isinstance(payload, TranscriptionFailedPayload):
            job.status = "failed"
            job.error_code = payload.error_code
            job.error_message = payload.error_message
            job.completed_at = now
            version.status = "failed"

        session.add(
            JobEvent(
                job_id=job.id,
                event_id=event.event_id,
                event_type=event.event_type,
                payload_json=cast(dict[str, object], payload.model_dump(mode="json")),
            ),
        )
        await session.commit()
        logger.info(
            "projected event",
            extra={
                "event_id": str(event.event_id),
                "event_type": event.event_type,
                "job_id": str(job.id),
                "consumer_group": get_settings().kafka_api_consumer_group,
                "result": "applied",
            },
        )
