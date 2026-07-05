# Event Contracts

Single Kafka-compatible topic:

```txt
sounds-right.events
```

Every message uses this envelope:

```json
{
  "event_id": "uuid",
  "event_type": "transcription.requested",
  "event_version": 1,
  "occurred_at": "2026-07-03T12:00:00Z",
  "correlation_id": "uuid",
  "causation_id": null,
  "producer": "sounds-right-api",
  "payload": {}
}
```

Event types are:

```txt
transcription.requested
transcription.started
transcription.progress
transcription.completed
transcription.failed
```

The API produces `transcription.requested`.
The worker consumes requested events and emits mock lifecycle events.
The API projector consumes worker lifecycle events and updates Postgres.
