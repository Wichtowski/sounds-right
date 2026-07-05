from __future__ import annotations

import uuid
import asyncio
from typing import cast

from sounds_right_worker.events.producer import EventProducer
from sounds_right_worker.events.schemas import (
    EventEnvelope,
    TranscriptionRequestedPayload,
    TranscriptionStartedPayload,
)
from sounds_right_worker.main import process_requested_event


class FakeProducer:
    def __init__(self) -> None:
        self.events: list[EventEnvelope] = []

    async def publish(self, event: EventEnvelope, key: uuid.UUID) -> None:
        self.events.append(event)


def test_mock_worker_emits_started_progress_and_completed() -> None:
    asyncio.run(run_mock_worker_success())


async def run_mock_worker_success() -> None:
    producer = FakeProducer()
    event = EventEnvelope(
        event_type="transcription.requested",
        correlation_id=uuid.uuid4(),
        producer="sounds-right-api",
        payload=TranscriptionRequestedPayload(
            job_id=uuid.uuid4(),
            track_version_id=uuid.uuid4(),
            track_id=uuid.uuid4(),
            artist_id=uuid.uuid4(),
            audio_object_key="temp-audio/version/input.mp3",
            original_audio_filename="song.mp3",
            audio_content_type="audio/mpeg",
            audio_size_bytes=123,
            engine="whisper.cpp",
            options={
                "language": "auto",
                "model": "base",
                "separate_vocals": False,
            },
        ),
    )

    await process_requested_event(event, cast(EventProducer, producer), "worker-1", False, 0)

    event_types = [published.event_type for published in producer.events]
    assert event_types == [
        "transcription.started",
        "transcription.progress",
        "transcription.progress",
        "transcription.progress",
        "transcription.progress",
        "transcription.completed",
    ]
    assert isinstance(producer.events[0].payload, TranscriptionStartedPayload)


def test_mock_worker_can_emit_failure() -> None:
    asyncio.run(run_mock_worker_failure())


async def run_mock_worker_failure() -> None:
    producer = FakeProducer()
    event = EventEnvelope(
        event_type="transcription.requested",
        correlation_id=uuid.uuid4(),
        producer="sounds-right-api",
        payload=TranscriptionRequestedPayload(
            job_id=uuid.uuid4(),
            track_version_id=uuid.uuid4(),
            track_id=uuid.uuid4(),
            artist_id=uuid.uuid4(),
            audio_object_key="temp-audio/version/input.mp3",
            original_audio_filename="song.mp3",
            audio_content_type="audio/mpeg",
            audio_size_bytes=123,
            engine="whisper.cpp",
            options={
                "language": "auto",
                "model": "base",
                "separate_vocals": False,
            },
        ),
    )

    await process_requested_event(event, cast(EventProducer, producer), "worker-1", True, 0)

    assert [published.event_type for published in producer.events] == [
        "transcription.started",
        "transcription.progress",
        "transcription.failed",
    ]
