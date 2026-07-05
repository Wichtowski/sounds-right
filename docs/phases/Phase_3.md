# Phase 3 — Event Flow

## Purpose

Implement the event-driven backbone of **Sounds Right**.

Phase 1 created the local foundation: Envoy, Vinext, Litestar API, Postgres, Alembic, MinIO, Redpanda, and a placeholder worker.

Phase 2 created the core domain API: auth, artists, tracks, versions, signed upload URLs, upload completion, and `uploaded` track versions.

Phase 3 connects the API and worker through Kafka-compatible events using Redpanda.

This phase should make the system capable of starting a transcription workflow **without actually transcribing audio yet**.

The goal is:

```txt
API command -> domain state update -> Kafka event -> worker receives event -> worker emits status events -> API/projector updates Postgres
```

This phase prepares the system for Phase 4, where `whisper.cpp` will actually process the uploaded audio.

---

## Final Phase 3 Goal

At the end of Phase 3, a user should be able to:

```txt
1. Register and log in.
2. Create artist, track, and version.
3. Upload temporary audio to MinIO.
4. Mark upload as complete.
5. Click/start transcription.
6. API creates a transcription job.
7. API emits `transcription.requested` to Redpanda/Kafka.
8. Worker consumes the event.
9. Worker emits `transcription.started`.
10. Worker emits fake/simulated `transcription.progress` events.
11. Worker emits `transcription.completed` or `transcription.failed` in mock mode.
12. API/projector consumes worker events and updates Postgres job/version state.
13. Frontend can display job status changing over time.
```

No real transcription should happen yet.

---

## Existing Phase Assumptions

Assume Phase 1 provides:

```txt
Envoy
Vinext frontend shell
Litestar API shell
Postgres
Alembic
MinIO
Redpanda
worker placeholder
Docker Compose
developer scripts
```

Assume Phase 2 provides:

```txt
users/auth
artists
tracks
track_versions
upload_sessions
signed upload URLs
upload-complete endpoint
MinIO temporary audio object keys
version status = uploaded
```

Do not rebuild earlier phases. Extend them.

---

## Tech Stack

Continue using:

```txt
API:
- Litestar
- Pydantic
- SQLAlchemy async
- Alembic
- PostgreSQL
- aiokafka or confluent-kafka

Worker:
- Python 3.12+
- Pydantic
- Kafka consumer/producer
- structured logging

Events:
- Redpanda locally
- Kafka protocol-compatible clients

Frontend:
- Vinext
- React
- TypeScript
- TanStack Query
```

Recommended Python Kafka client:

```txt
aiokafka
```

Alternative:

```txt
confluent-kafka
```

Pick one and use it consistently.

Do not introduce:

```txt
Celery
RabbitMQ
Redis Queue
Temporal
MongoDB
Whisper.cpp
actual transcription
ffmpeg/ffprobe validation
Pydantic AI
```

---

## Scope

Phase 3 includes:

```txt
Kafka/Redpanda topic setup
event schema definitions
event producer in API
transcription job creation endpoint
transactional-ish event publishing
worker consumer
worker mock processing
worker event producer
API/projector event consumer
job/version state projection
job events timeline
frontend job status display
basic polling or SSE for job updates
```

Phase 3 does not include:

```txt
real audio validation
whisper.cpp
transcript JSON generation
MinIO transcript output
raw audio deletion
review UI
approval flow
publishing
Pydantic AI
```

---

## Key Design Principle

Kafka is not just a task queue.

Treat Kafka/Redpanda as the system event log.

Commands happen through the API:

```txt
POST /api/versions/{version_id}/start-transcription
```

Events describe what happened:

```txt
transcription.requested
transcription.started
transcription.progress
transcription.completed
transcription.failed
```

Postgres stores current state.

Kafka stores event history.

The worker reacts to events.

The API/projector updates read models/state from events.

---

## Recommended Event Flow

```txt
User
  ↓
Frontend
  ↓ POST /api/versions/{version_id}/start-transcription
API
  ↓ creates transcription_jobs row
  ↓ creates job_events row
  ↓ emits transcription.requested
Redpanda/Kafka
  ↓
Worker
  ↓ consumes transcription.requested
  ↓ emits transcription.started
  ↓ emits transcription.progress
  ↓ emits transcription.completed OR transcription.failed
Redpanda/Kafka
  ↓
Projector/API Consumer
  ↓ updates transcription_jobs
  ↓ updates track_versions
  ↓ appends job_events
Frontend
  ↓ polls /api/jobs/{job_id}
  ↓ displays current state
```

---

## Topic Strategy

For Phase 3, keep topics simple.

Recommended topic:

```txt
sounds-right.events
```

Use a single topic with typed events first.

Reasoning:

```txt
- easier local development
- fewer topic-management problems
- simpler consumer setup
- enough for early event flow
```

Later phases may split into:

```txt
track.events
transcription.events
review.events
publication.events
```

But do not split early unless necessary.

---

## Kafka Topic Requirements

Create or ensure topic:

```txt
sounds-right.events
```

Suggested local settings:

```txt
partitions: 3
replication factor: 1
retention: default or 7 days
```

Add a topic bootstrap script or Docker Compose init command if practical.

Suggested file:

```txt
infra/redpanda/create-topics.sh
```

Example behavior:

```sh
rpk topic create sounds-right.events --brokers redpanda:9092 --partitions 3 --replicas 1
```

Make topic creation idempotent.

---

## Event Envelope

All Kafka events must use a shared envelope.

Create in contracts and API/worker code:

```txt
packages/contracts/events/README.md
apps/api/src/sounds_right_api/events/schemas.py
apps/worker/src/sounds_right_worker/events/schemas.py
```

If shared Python package setup is easy, use one shared package.

If not, duplicate carefully for Phase 3 and plan to consolidate later.

Base event envelope:

```json
{
  "event_id": "uuid",
  "event_type": "transcription.requested",
  "event_version": 1,
  "occurred_at": "2026-07-03T12:00:00Z",
  "correlation_id": "uuid",
  "causation_id": "uuid-or-null",
  "producer": "sounds-right-api",
  "payload": {}
}
```

Field rules:

```txt
event_id:
  unique UUID for this exact event

event_type:
  string enum, e.g. transcription.requested

event_version:
  integer schema version, start with 1

occurred_at:
  timezone-aware UTC ISO timestamp

correlation_id:
  shared ID across the user action / job flow

causation_id:
  event_id or command ID that caused this event, nullable

producer:
  service name, e.g. sounds-right-api or sounds-right-worker

payload:
  event-specific Pydantic model
```

---

## Event Types

Implement these in Phase 3:

```txt
transcription.requested
transcription.started
transcription.progress
transcription.completed
transcription.failed
```

Optional if easy:

```txt
transcription.cancelled
```

Do not implement approval/publishing events yet.

---

## Event Payloads

### transcription.requested

Produced by:

```txt
API
```

Consumed by:

```txt
worker
```

Payload:

```json
{
  "job_id": "uuid",
  "track_version_id": "uuid",
  "track_id": "uuid",
  "artist_id": "uuid",
  "audio_object_key": "temp-audio/{version_id}/input.mp3",
  "original_audio_filename": "song.mp3",
  "audio_content_type": "audio/mpeg",
  "audio_size_bytes": 12345678,
  "engine": "whisper.cpp",
  "options": {
    "language": "auto",
    "model": "base",
    "separate_vocals": false
  }
}
```

Rules:

```txt
track_version status must be uploaded
track_version must have temporary_audio_object_key
API creates job before producing event
job status starts as queued
version status changes to processing or queued_for_processing
```

Recommended Phase 3 version statuses:

```txt
draft
upload_url_created
uploaded
queued_for_processing
processing
completed
failed
```

---

### transcription.started

Produced by:

```txt
worker
```

Consumed by:

```txt
API/projector
```

Payload:

```json
{
  "job_id": "uuid",
  "track_version_id": "uuid",
  "worker_id": "sounds-right-worker-1",
  "engine": "mock",
  "message": "Mock transcription started"
}
```

Projection behavior:

```txt
transcription_jobs.status = started
track_versions.status = processing
append job_events row
```

---

### transcription.progress

Produced by:

```txt
worker
```

Consumed by:

```txt
API/projector
```

Payload:

```json
{
  "job_id": "uuid",
  "track_version_id": "uuid",
  "progress": 40,
  "stage": "mock_processing",
  "message": "Mock processing 40% complete"
}
```

Rules:

```txt
progress integer from 0 to 100
stage is machine-readable
message is human-readable
```

Projection behavior:

```txt
transcription_jobs.progress = payload.progress
append job_events row
```

---

### transcription.completed

Produced by:

```txt
worker
```

Consumed by:

```txt
API/projector
```

Phase 3 mock payload:

```json
{
  "job_id": "uuid",
  "track_version_id": "uuid",
  "transcript_object_key": null,
  "manifest_object_key": null,
  "duration_seconds": null,
  "word_count": null,
  "sha256": null,
  "message": "Mock transcription completed"
}
```

Projection behavior:

```txt
transcription_jobs.status = completed
transcription_jobs.progress = 100
transcription_jobs.completed_at = now
track_versions.status = completed
append job_events row
```

Note:

Real transcript object fields stay null in Phase 3. Phase 4 fills them.

---

### transcription.failed

Produced by:

```txt
worker
```

Consumed by:

```txt
API/projector
```

Payload:

```json
{
  "job_id": "uuid",
  "track_version_id": "uuid",
  "error_code": "mock_failure",
  "error_message": "Mock worker failed intentionally",
  "retryable": true
}
```

Projection behavior:

```txt
transcription_jobs.status = failed
transcription_jobs.error_code = payload.error_code
transcription_jobs.error_message = payload.error_message
transcription_jobs.completed_at = now
track_versions.status = failed
append job_events row
```

---

## Database Changes

Add or update these tables.

---

## transcription_jobs

If not already created in Phase 2, create now.

```txt
transcription_jobs
- id uuid primary key
- track_version_id uuid not null references track_versions(id)
- status text not null
- engine text not null
- progress integer not null default 0
- error_code text nullable
- error_message text nullable
- correlation_id uuid not null
- requested_by_user_id uuid nullable references users(id)
- started_at timestamptz nullable
- completed_at timestamptz nullable
- created_at timestamptz not null
- updated_at timestamptz not null
```

Allowed statuses:

```txt
queued
started
processing
completed
failed
cancelled
```

In Phase 3, use:

```txt
queued
started
processing
completed
failed
```

---

## job_events

```txt
job_events
- id uuid primary key
- job_id uuid not null references transcription_jobs(id)
- event_id uuid not null unique
- event_type text not null
- payload_json jsonb not null
- created_at timestamptz not null
```

Purpose:

```txt
- job timeline for frontend
- debugging
- auditability
- replay-ish visibility
```

---

## event_outbox

Recommended for reliability.

```txt
event_outbox
- id uuid primary key
- event_id uuid not null unique
- topic text not null
- event_type text not null
- payload_json jsonb not null
- status text not null default 'pending'
- attempts integer not null default 0
- last_error text nullable
- published_at timestamptz nullable
- created_at timestamptz not null
- updated_at timestamptz not null
```

Allowed statuses:

```txt
pending
published
failed
```

Why:

The API should not update Postgres and produce Kafka in totally unrelated operations without a recovery path.

For Phase 3, implement a simple outbox dispatcher if possible.

Acceptable simpler alternative:

```txt
API writes DB state then publishes Kafka immediately.
If Kafka publish fails, rollback DB transaction or mark job as failed_to_enqueue.
```

Recommended approach:

```txt
1. API transaction creates job.
2. API transaction creates outbox row.
3. Outbox dispatcher publishes event to Kafka.
4. Dispatcher marks outbox row as published.
```

This can run as:

```txt
- background task inside API for local MVP
- separate worker process later
```

For Phase 3, simple is acceptable, but document the tradeoff.

---

## API Endpoints

Add these routes.

---

## POST /api/versions/{version_id}/start-transcription

Requires auth.

Purpose:

```txt
Create a transcription job and enqueue/request transcription via Kafka event.
```

Request:

```json
{
  "engine": "whisper.cpp",
  "options": {
    "language": "auto",
    "model": "base",
    "separate_vocals": false
  }
}
```

Request can be empty and use defaults:

```json
{}
```

Defaults:

```txt
engine = whisper.cpp
language = auto
model = base
separate_vocals = false
```

Validation:

```txt
version exists
version status is uploaded
version has temporary_audio_object_key
no active job already exists for this version
engine must be allowed
```

Response:

```json
{
  "job_id": "uuid",
  "track_version_id": "uuid",
  "status": "queued",
  "correlation_id": "uuid"
}
```

State changes:

```txt
create transcription_jobs row with status queued
create job_events row for transcription.requested
update track_versions.status = queued_for_processing
publish or outbox transcription.requested event
```

Errors:

```txt
404 version not found
409 version not uploaded
409 active job already exists
500 event enqueue failed, if not using outbox
```

---

## GET /api/jobs/{job_id}

Requires auth for now.

Response:

```json
{
  "id": "uuid",
  "track_version_id": "uuid",
  "status": "processing",
  "engine": "whisper.cpp",
  "progress": 40,
  "error_code": null,
  "error_message": null,
  "created_at": "2026-07-03T12:00:00Z",
  "started_at": "2026-07-03T12:00:05Z",
  "completed_at": null
}
```

---

## GET /api/jobs/{job_id}/events

Requires auth for now.

Response:

```json
{
  "job_id": "uuid",
  "events": [
    {
      "event_type": "transcription.requested",
      "created_at": "2026-07-03T12:00:00Z",
      "payload": {}
    },
    {
      "event_type": "transcription.progress",
      "created_at": "2026-07-03T12:00:10Z",
      "payload": {
        "progress": 40,
        "stage": "mock_processing"
      }
    }
  ]
}
```

---

## Optional: GET /api/jobs/{job_id}/stream

Optional in Phase 3.

If implemented, use Server-Sent Events.

Purpose:

```txt
Push job progress to frontend without polling.
```

If this adds too much complexity, skip it and use polling in frontend.

Recommended for Phase 3:

```txt
Use polling first.
Add SSE in Phase 5 or later.
```

---

## API Producer Requirements

Create module:

```txt
apps/api/src/sounds_right_api/events/producer.py
```

Responsibilities:

```txt
connect to Redpanda/Kafka
serialize Pydantic event envelopes
publish to sounds-right.events
support graceful startup/shutdown
log event_id and event_type
```

Required behavior:

```txt
- JSON serialization
- UTF-8 encoding
- event_type as Kafka message key or job_id as key
```

Recommended key:

```txt
key = job_id
```

Reasoning:

Events for the same job should land in the same partition and preserve order.

---

## Worker Consumer Requirements

Create or update:

```txt
apps/worker/src/sounds_right_worker/events/consumer.py
apps/worker/src/sounds_right_worker/events/producer.py
apps/worker/src/sounds_right_worker/main.py
```

Worker behavior:

```txt
1. Connect to Redpanda/Kafka.
2. Subscribe to sounds-right.events.
3. Read only events relevant to worker.
4. When event_type == transcription.requested, process it.
5. Ignore events produced by itself if not relevant.
6. Produce transcription.started.
7. Produce fake transcription.progress events.
8. Produce transcription.completed.
```

Important:

Because the same topic contains all events, the worker must filter events by `event_type`.

Avoid infinite loops:

```txt
worker consumes transcription.requested
worker ignores transcription.started/progress/completed/failed
```

Use consumer group:

```txt
sounds-right-workers
```

Worker ID:

```txt
from env WORKER_NAME or hostname
```

---

## Mock Worker Processing

Phase 3 worker should simulate processing.

Example behavior:

```txt
on transcription.requested:
  emit transcription.started
  sleep 1 second
  emit progress 10
  sleep 1 second
  emit progress 30
  sleep 1 second
  emit progress 60
  sleep 1 second
  emit progress 90
  sleep 1 second
  emit transcription.completed
```

Make mock behavior configurable:

```env
WORKER_MOCK_MODE=true
WORKER_MOCK_SHOULD_FAIL=false
WORKER_MOCK_STEP_DELAY_SECONDS=1
```

If `WORKER_MOCK_SHOULD_FAIL=true`, worker should emit `transcription.failed` after one progress event.

This helps test failure projection.

---

## Projector / Event Consumer Requirements

The system needs a consumer that updates Postgres based on events emitted by the worker.

Recommended for Phase 3:

```txt
Run projector inside API process as a background task, or create a separate lightweight projector service.
```

Simpler option:

```txt
Add projector loop to API app startup.
```

Cleaner option:

```txt
Create apps/projector service.
```

For Phase 3, either is acceptable.

If creating a separate service feels like too much, keep it inside API but isolate code clearly:

```txt
apps/api/src/sounds_right_api/events/projector.py
```

Consumer group:

```txt
sounds-right-projector
```

Projector behavior:

```txt
consume sounds-right.events
filter event types:
  transcription.started
  transcription.progress
  transcription.completed
  transcription.failed
update transcription_jobs
update track_versions
append job_events
ignore transcription.requested if already recorded by API
```

Idempotency:

```txt
Before inserting job_events, check event_id unique.
If event_id already exists, skip projection.
```

This prevents duplicate Kafka delivery from corrupting state.

---

## Event Idempotency Rules

Kafka consumers can receive duplicate messages.

Implement minimum idempotency:

```txt
job_events.event_id is unique
projector inserts job_events row first or checks event_id
if duplicate event_id, skip update
```

For status updates:

```txt
completed should not move back to processing
failed should not move back to processing
progress should only increase if simple
```

Recommended simple rule for Phase 3:

```txt
If job status is completed or failed, ignore started/progress events.
```

---

## State Transition Rules

Track version statuses in Phase 3:

```txt
draft
upload_url_created
uploaded
queued_for_processing
processing
completed
failed
```

Transcription job statuses:

```txt
queued
started
processing
completed
failed
cancelled
```

Allowed transition examples:

```txt
track_version:
uploaded -> queued_for_processing
queued_for_processing -> processing
processing -> completed
processing -> failed

transcription_job:
queued -> started
started -> processing
processing -> completed
processing -> failed
```

Do not allow:

```txt
completed -> processing
failed -> processing
completed -> failed, unless explicitly designed later
```

---

## Frontend Requirements

Add minimal UI for starting and watching a job.

Extend the version detail page from Phase 2.

When version status is `uploaded`, show:

```txt
Start transcription button
```

On click:

```txt
POST /api/versions/{version_id}/start-transcription
```

Then navigate or show:

```txt
/jobs/{job_id}
```

Add page:

```txt
/jobs/:jobId
```

Display:

```txt
job status
progress percentage
engine
timeline of job events
error message if failed
```

Use polling first:

```txt
GET /api/jobs/{job_id}
GET /api/jobs/{job_id}/events
```

Suggested polling interval:

```txt
1000-2000 ms while job is active
stop polling when completed or failed
```

Do not implement complex review UI yet.

---

## Pydantic Schemas

Create or update schemas for:

```txt
EventEnvelope
TranscriptionRequestedPayload
TranscriptionStartedPayload
TranscriptionProgressPayload
TranscriptionCompletedPayload
TranscriptionFailedPayload
StartTranscriptionRequest
StartTranscriptionResponse
TranscriptionJobPublic
JobEventPublic
JobEventsResponse
```

Rules:

```txt
Do not use untyped dicts where Pydantic models are reasonable.
Validate event_type and payload combinations.
Keep event_version explicit.
```

---

## Logging Requirements

Use structured logs where practical.

Every event publish log should include:

```txt
event_id
event_type
job_id
track_version_id
producer
topic
```

Every event consume log should include:

```txt
event_id
event_type
consumer_group
job_id
result
```

Avoid logging secrets or MinIO credentials.

---

## Configuration

Add env vars if missing:

```env
KAFKA_TOPIC=sounds-right.events
KAFKA_BOOTSTRAP_SERVERS=redpanda:9092
KAFKA_CLIENT_ID=sounds-right-local
KAFKA_API_CONSUMER_GROUP=sounds-right-projector
KAFKA_WORKER_CONSUMER_GROUP=sounds-right-workers
WORKER_NAME=sounds-right-worker
WORKER_MOCK_MODE=true
WORKER_MOCK_SHOULD_FAIL=false
WORKER_MOCK_STEP_DELAY_SECONDS=1
```

If using an API-embedded projector:

```env
API_ENABLE_PROJECTOR=true
```

---

## Docker Compose Updates

Ensure services start in a workable order.

Update worker service to run real consumer loop.

If using API-embedded projector:

```txt
api starts web API and projector background task
```

If using separate projector service, add:

```txt
projector
```

Phase 3 required services then become:

```txt
envoy
web
api
worker
postgres
redpanda
minio
```

Optional:

```txt
projector
```

Do not expose Redpanda publicly through Envoy.

Direct local debug port is acceptable if already configured.

---

## Error Handling

Handle these cases:

```txt
start-transcription called for missing version -> 404
start-transcription called for non-uploaded version -> 409
start-transcription called twice for same active version -> 409
Kafka publish fails -> clear error or outbox pending state
worker receives malformed event -> log and skip / dead-letter later
projector receives duplicate event -> skip safely
projector receives event for missing job -> log error, do not crash
```

No dead-letter topic is required in Phase 3, but code should not crash forever on bad messages.

Optional topic for later:

```txt
sounds-right.dead-letter
```

---

## Testing Requirements

Add backend tests for:

```txt
start transcription happy path
start transcription fails when version missing
start transcription fails when version not uploaded
start transcription fails when active job exists
transcription.requested event schema validation
projector handles transcription.started
projector handles transcription.progress
projector handles transcription.completed
projector handles transcription.failed
projector ignores duplicate event_id
```

Worker tests:

```txt
worker ignores non-requested events
worker emits started/progress/completed for requested event in mock mode
worker emits failed when mock failure enabled
```

Integration tests are preferred but not required if they slow Phase 3 too much.

At minimum, test event schema and projection logic without a real Kafka broker.

---

## Developer Scripts

Update scripts if needed.

Required:

```sh
./scripts/dev.sh
./scripts/down.sh
./scripts/logs.sh
./scripts/migrate.sh
./scripts/lint.sh
./scripts/format.sh
./scripts/check.sh
./scripts/test.sh
```

Add optional scripts:

```sh
./scripts/create-topics.sh
./scripts/list-topics.sh
./scripts/consume-events.sh
./scripts/produce-test-event.sh
```

These are useful for learning Kafka/Redpanda.

Example:

```sh
./scripts/consume-events.sh
```

Should consume from:

```txt
sounds-right.events
```

---

## README Updates

Update root README with Phase 3 flow.

Add section:

```txt
Event-driven transcription mock flow
```

Document:

```txt
how to create topic
how to start transcription
how to view job status
how to view job events
how to inspect Kafka/Redpanda events
how to make worker fail intentionally
```

Include curl example:

```sh
curl -X POST http://localhost:8080/api/versions/$VERSION_ID/start-transcription \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "engine": "whisper.cpp",
    "options": {
      "language": "auto",
      "model": "base",
      "separate_vocals": false
    }
  }'
```

Job status:

```sh
curl http://localhost:8080/api/jobs/$JOB_ID \
  -H "Authorization: Bearer $TOKEN"
```

Job events:

```sh
curl http://localhost:8080/api/jobs/$JOB_ID/events \
  -H "Authorization: Bearer $TOKEN"
```

---

## Acceptance Criteria

Phase 3 is complete when all of these are true:

```txt
1. Redpanda topic `sounds-right.events` exists.
2. Event envelope schema exists and is validated with Pydantic.
3. API can create transcription_jobs rows.
4. API exposes POST /api/versions/{version_id}/start-transcription.
5. API rejects start-transcription if version is not uploaded.
6. API emits or outboxes `transcription.requested`.
7. Worker consumes `transcription.requested`.
8. Worker emits `transcription.started`.
9. Worker emits mock `transcription.progress` events.
10. Worker emits mock `transcription.completed`.
11. Worker can emit mock `transcription.failed` when configured.
12. Projector/API consumer updates transcription_jobs status.
13. Projector/API consumer updates track_versions status.
14. job_events table stores event timeline.
15. Duplicate event IDs do not duplicate job events or corrupt state.
16. Frontend can start transcription from uploaded version page.
17. Frontend can display job progress/status.
18. README documents the event flow.
19. No whisper.cpp integration exists yet.
20. No actual transcription happens yet.
```

---

## Non-Goals

Do not implement these in Phase 3:

```txt
whisper.cpp
real audio processing
ffmpeg/ffprobe validation
transcript JSON generation
MinIO transcript artifact writing
raw audio deletion
lyrics support
review UI
approve/reject
publishing
public transcript endpoint
Pydantic AI features
complex Kafka topic topology
schema registry
dead-letter queue, unless trivial
```

---

## Suggested Task Order

### Task 1 — Add event schemas

Create Pydantic models for:

```txt
EventEnvelope
all transcription payloads
```

Document them in `packages/contracts/events/README.md`.

---

### Task 2 — Add DB migration

Add tables if missing:

```txt
transcription_jobs
job_events
event_outbox, recommended
```

Update track version statuses if using enums/check constraints.

---

### Task 3 — Add Kafka topic bootstrap

Create topic:

```txt
sounds-right.events
```

Make creation idempotent.

---

### Task 4 — Add API producer/outbox

Implement event publishing or outbox dispatch.

Recommended:

```txt
DB transaction writes job + job_event + outbox event
background dispatcher publishes to Kafka
```

If too much, publish directly after DB commit and document tradeoff.

---

### Task 5 — Add start transcription endpoint

Implement:

```txt
POST /api/versions/{version_id}/start-transcription
```

Validate status and create job.

---

### Task 6 — Add worker consumer

Worker should consume `transcription.requested` and mock process it.

Emit:

```txt
transcription.started
transcription.progress
transcription.completed
```

---

### Task 7 — Add projector

Consume worker events and update Postgres.

Must be idempotent by event_id.

---

### Task 8 — Add job APIs

Implement:

```txt
GET /api/jobs/{job_id}
GET /api/jobs/{job_id}/events
```

---

### Task 9 — Add frontend job UI

Add start transcription button and job status page.

Use polling.

---

### Task 10 — Add tests and docs

Add schema/projection/service tests.

Update README.

---

## Final Verification Flow

Manual verification after Phase 3:

```txt
1. Start stack.
2. Register/login.
3. Create artist.
4. Create track.
5. Create version.
6. Upload temporary audio.
7. Mark upload complete.
8. Click Start transcription.
9. Observe job status:
   queued -> started/processing -> completed
10. Check job event timeline.
11. Check Kafka topic contains events.
```

Expected frontend result:

```txt
Version page shows Start transcription.
Job page shows progress moving from 0 to 100.
Job ends as completed.
```

Expected database result:

```txt
transcription_jobs row exists
job_events rows exist
track_versions.status = completed
```

Expected Kafka result:

```txt
sounds-right.events contains:
- transcription.requested
- transcription.started
- transcription.progress
- transcription.completed
```

---

## Definition of Done

Phase 3 is done when the system has a real event-driven mock transcription flow:

```txt
The API creates jobs.
The API emits transcription.requested events.
The worker consumes events.
The worker emits progress/completion/failure events.
The API/projector projects events into Postgres.
The frontend can show job progress.
No real transcription exists yet.
```

Phase 4 can then replace mock worker behavior with real `whisper.cpp` processing.
