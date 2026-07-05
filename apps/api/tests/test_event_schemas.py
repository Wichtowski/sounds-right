from __future__ import annotations

import uuid

from sounds_right_api.events.schemas import (
    EventEnvelope,
    TranscriptionProgressPayload,
    TranscriptionStartedPayload,
    event_envelope_adapter,
)


def test_event_envelope_round_trips_started_event() -> None:
    event = EventEnvelope(
        event_type="transcription.started",
        correlation_id=uuid.uuid4(),
        producer="sounds-right-worker",
        payload=TranscriptionStartedPayload(
            job_id=uuid.uuid4(),
            track_version_id=uuid.uuid4(),
            worker_id="worker-1",
            engine="mock",
            message="Mock transcription started",
        ),
    )

    parsed = event_envelope_adapter.validate_json(event.model_dump_json())

    assert parsed.event_id == event.event_id
    assert parsed.event_type == "transcription.started"
    assert isinstance(parsed.payload, TranscriptionStartedPayload)


def test_progress_payload_rejects_invalid_percent() -> None:
    try:
        TranscriptionProgressPayload(
            job_id=uuid.uuid4(),
            track_version_id=uuid.uuid4(),
            progress=101,
            stage="mock_processing",
            message="too much",
        )
    except ValueError:
        return

    raise AssertionError("progress above 100 should fail validation")
