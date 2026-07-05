# Events

All events share a common envelope and flow through the single Kafka/Redpanda
topic `sounds-right.events`, keyed by `job_id`.

## Envelope

```json
{
  "event_id": "uuid",
  "event_type": "transcription.requested",
  "event_version": 1,
  "occurred_at": "2026-07-03T12:00:00Z",
  "correlation_id": "uuid",
  "causation_id": "uuid | null",
  "producer": "sounds-right-api",
  "payload": {}
}
```

- `correlation_id` groups all events for a single transcription job.
- `causation_id` points at the event that caused this one.
- `producer` is `sounds-right-api` or the worker name.

## transcription.requested (API -> worker)

```json
{
  "job_id": "uuid",
  "track_version_id": "uuid",
  "track_id": "uuid",
  "artist_id": "uuid",
  "audio_object_key": "temp-audio/{track_version_id}/input.mp3",
  "original_audio_filename": "song.mp3",
  "audio_content_type": "audio/mpeg",
  "audio_size_bytes": 5242880,
  "engine": "whisper.cpp",
  "options": { "language": "auto", "model": "base", "separate_vocals": false }
}
```

`separate_vocals: true` is rejected with `transcription.failed`
(`error_code = unsupported_option`)

## transcription.started (worker -> projector)

```json
{ "job_id": "uuid", "track_version_id": "uuid", "worker_id": "sounds-right-worker", "engine": "whisper.cpp", "message": "Transcription started" }
```

## transcription.progress

```json
{ "job_id": "uuid", "track_version_id": "uuid", "progress": 20, "stage": "audio_validated", "message": "audio_validated (20%)" }
```

Stages: `audio_downloaded` (10), `audio_validated` (20), `audio_normalized` (30),
`transcription_started` (40), `transcription_finished` (80),
`artifacts_uploaded` (90).

## transcription.completed

```json
{
  "job_id": "uuid",
  "track_version_id": "uuid",
  "transcript_object_key": "transcripts/{track_version_id}/transcript.json",
  "manifest_object_key": "transcripts/{track_version_id}/manifest.json",
  "duration_seconds": 213.42,
  "word_count": 512,
  "segment_count": 84,
  "engine": "whisper.cpp",
  "model": "base",
  "language": "en",
  "sha256": "...",
  "message": "Transcription completed"
}
```

## transcription.failed

```json
{ "job_id": "uuid", "track_version_id": "uuid", "error_code": "audio_validation_failed", "error_message": "Unsupported audio format", "retryable": false }
```

Raw tracebacks are never placed in payloads; only stable codes and UI-safe
messages. See [transcription-worker.md](transcription-worker.md) for the full
error code list.

## Projector state transitions

| Event | transcription_jobs | track_versions |
| --- | --- | --- |
| `transcription.started` | `status=started`, `started_at` | `status=processing` |
| `transcription.progress` | `status=processing`, `progress=max(...)` | `status=processing` |
| `transcription.completed` | `status=completed`, `progress=100`, `completed_at` | `status=completed`, transcript/manifest keys, duration, word_count, sha256 |
| `transcription.failed` | `status=failed`, error code/message, `completed_at` | `status=failed` |

Projection is idempotent: duplicate `event_id`s are skipped, and started/progress
events are ignored once a job is `completed` or `failed`.
