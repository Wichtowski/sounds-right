# Sounds Right — Rewrite Architecture Canvas

## 1. Project Summary

**Sounds Right** is a rewrite of an old karaoke/audio transcription backend. The original project allowed users to upload audio, optionally provide lyrics, transcribe the song, generate word/segment-level karaoke timing data, review the result, and approve/publish it.

The old project had a good core idea but weak architecture: confused queueing, unsafe auth, unfinished approval flow, risky file handling, temporary file collisions, and too much hand-written Flask/controller logic. The rewrite should preserve the product idea but rebuild the system cleanly with modern technologies.

The goal is not only to make the project work, but also to use it as a serious learning project for:

* Cloudflare-friendly frontend development
* Event-driven architecture
* Kafka/Redpanda
* Envoy reverse proxying
* Object storage with MinIO
* Async Python API architecture
* Whisper.cpp-based transcription workers
* Clean domain modeling and approval workflows

---

## 2. Final Technology Decisions

### Frontend

Use:

* Vinext
* React
* TypeScript
* Tailwind CSS
* TanStack Query
* Zod
* OpenAPI-generated API client

Reasoning:

The project should avoid Vercel/Next.js dependency bias and stay Cloudflare-friendly. Vinext fits the desired direction because it provides a Next-like developer experience while being Vite/Cloudflare-oriented.

The frontend should stay relatively thin. Business rules should live in the API and domain layer, not inside framework-specific frontend code.

---

### Backend API

Use:

* Litestar
* Pydantic
* SQLAlchemy
* Alembic
* PostgreSQL
* MinIO client
* Kafka/Redpanda producer
* Optional Pydantic AI later

Reasoning:

FastAPI would work, but the rewrite should avoid using the same default stack for every project. Litestar is a good modern Python alternative with strong structure, class-based controller support, dependency injection patterns, and compatibility with Pydantic-style validation.

Pydantic should be used for request validation, response schemas, domain DTOs, and event payload validation.

Pydantic AI may be added later for “extra magic,” such as:

* automatic lyrics cleanup
* transcript quality checks
* confidence analysis
* reviewer suggestions
* metadata enrichment
* detecting likely bad alignments
* generating review notes

Pydantic AI should not be core infrastructure in Phase 1. It should be added after the deterministic transcription flow works.

---

### Database

Use:

* PostgreSQL for metadata and state
* Alembic for migrations

Do not use MongoDB for the core system.

Reasoning:

The core data is relational: users, artists, tracks, versions, jobs, approvals, audit events, object keys, and statuses. PostgreSQL is a better source of truth than MongoDB for this domain.

Large transcript JSON files should not be stored in Postgres as the primary storage mechanism. Postgres should store references, checksums, version metadata, and searchable summary fields.

---

### Object Storage

Use:

* MinIO locally
* S3-compatible object storage in production if needed

Store permanently:

* transcript JSON
* segment JSON
* word JSON
* manifest JSON
* waveform/preview artifacts, if generated

Do not store permanently:

* original uploaded sound files
* temporary separated vocals
* temporary chunks
* intermediate worker files

Reasoning:

Raw audio can be large, expensive, and potentially copyright-sensitive. The system should only keep the generated transcript/artifacts. Raw audio should exist temporarily only for processing.

---

### Transcription Engine

Use:

* whisper.cpp

Reasoning:

whisper.cpp fits this rewrite well because it can run as an isolated worker process/binary. It avoids heavy Python ML dependency hell and is easier to reason about as a standalone transcription backend. It also fits the goal of experimenting with serious infrastructure and independent services.

The API should not directly depend on whisper.cpp. The worker should wrap whisper.cpp behind an internal engine interface.

Future engine abstraction:

```txt
TranscriptionEngine
├── WhisperCppEngine
├── FasterWhisperEngine
└── RemoteEngine
```

Phase 1 should implement only `WhisperCppEngine`.

---

### Queue / Event System

Use:

* Kafka-compatible event streaming
* Redpanda for local development
* Kafka protocol-compatible producers/consumers

Do not use:

* Celery
* Redis Queue
* custom RabbitMQ bridge
* RabbitMQ + Celery double-dispatching

Reasoning:

The old project mixed Celery and RabbitMQ manually, creating unnecessary complexity and unclear job ownership. The rewrite should use a clean event-driven flow.

The system naturally emits domain events:

* track created
* version created
* transcription requested
* transcription started
* transcription progress updated
* transcription completed
* transcription failed
* transcription approved
* transcription published

Kafka/Redpanda is a good fit because this project is partly about learning event-driven architecture.

Important note:

Kafka should not be treated as “Celery but cooler.” It is an event log. Job state should be projected into Postgres by consumers.

---

### Reverse Proxy

Use:

* Envoy

Reasoning:

Envoy should be the front door for the system. It provides a good learning opportunity and a clean production-style architecture.

Envoy responsibilities:

* route `/api/*` to the API service
* route frontend requests to Vinext
* keep internal services private
* add request IDs
* configure CORS
* handle access logs
* later handle rate limiting / compression / TLS

Kafka, Postgres, workers, and MinIO internals should not be publicly exposed.

---

## 3. High-Level Architecture

```txt
Client
  ↓
Envoy
  ├── Web Route  → Vinext frontend
  └── API Route  → Litestar API
                    ↓
                 PostgreSQL
                    ↓
              Redpanda / Kafka
                    ↓
            Transcription Worker
                    ↓
                 MinIO
```

Main flow:

```txt
1. User creates artist/track/version metadata.
2. API creates a temporary upload target in MinIO.
3. User uploads audio to temporary MinIO storage.
4. User starts transcription.
5. API emits `transcription.requested`.
6. Worker consumes event.
7. Worker downloads temporary audio.
8. Worker runs ffprobe validation.
9. Worker runs whisper.cpp.
10. Worker generates transcript JSON.
11. Worker uploads transcript artifacts to MinIO.
12. Worker deletes temporary raw audio.
13. Worker emits `transcription.completed` or `transcription.failed`.
14. API/projector updates Postgres job/version state.
15. Reviewer approves or rejects the version.
16. Approved version becomes publishable.
```

---

## 4. Service Layout

Recommended monorepo:

```txt
sounds-right/
  apps/
    web/
      vinext frontend

    api/
      litestar API
      database models
      migrations
      REST endpoints
      Kafka producers
      MinIO integration

    worker/
      Kafka consumers
      whisper.cpp wrapper
      ffmpeg/ffprobe validation
      transcript generation
      artifact upload
      temp cleanup

    projector/
      optional separate service later
      consumes events
      updates read/state models in Postgres

  packages/
    contracts/
      OpenAPI schema
      event schemas
      transcript JSON schema
      generated clients

  infra/
    envoy/
      envoy.yaml

    compose/
      docker-compose.yml

    postgres/
      init scripts if needed

    redpanda/
      config if needed

    minio/
      bucket setup scripts

  docs/
    architecture.md
    events.md
    api.md
    transcript-schema.md
```

For early phases, the `projector` can live inside the API or worker. Later it can become its own service.

---

## 5. Domain Model

### Users

```txt
users
- id
- email
- username
- password_hash
- role
- is_active
- created_at
- updated_at
```

Roles:

```txt
user
reviewer
admin
```

---

### Artists

```txt
artists
- id
- slug
- display_name
- full_name
- created_at
- updated_at
```

---

### Tracks

```txt
tracks
- id
- artist_id
- title
- album
- slug
- created_by_user_id
- created_at
- updated_at
```

---

### Track Versions

```txt
track_versions
- id
- track_id
- version
- status
- temporary_audio_object_key
- transcript_object_key
- manifest_object_key
- transcript_sha256
- transcript_schema_version
- duration_seconds
- word_count
- created_at
- updated_at
- approved_at
- approved_by_user_id
```

Possible statuses:

```txt
draft
uploaded
processing
completed
pending_review
approved
rejected
published
failed
```

---

### Transcription Jobs

```txt
transcription_jobs
- id
- track_version_id
- status
- engine
- progress
- error_code
- error_message
- started_at
- completed_at
- created_at
- updated_at
```

Possible statuses:

```txt
queued
started
processing
completed
failed
cancelled
```

---

### Job Events

```txt
job_events
- id
- job_id
- event_type
- payload_json
- created_at
```

This table is useful for debugging, UI timelines, and auditability.

---

## 6. Transcript Storage

Transcript files should live in MinIO, not directly in Postgres.

Recommended object layout:

```txt
temp-audio/
  {track_version_id}/
    input.mp3

transcripts/
  {artist_slug}/
    {track_slug}/
      v{version}/
        transcript.json
        segments.json
        words.json
        manifest.json

artifacts/
  {artist_slug}/
    {track_slug}/
      v{version}/
        waveform.json
        preview.json
```

Raw audio should be deleted after processing.

MinIO lifecycle policies should eventually delete old temporary files automatically.

---

## 7. Transcript JSON Schema

Initial transcript format:

```json
{
  "schema_version": "1.0",
  "track": {
    "artist": "Artist Name",
    "album": "Album Name",
    "title": "Song Title",
    "version": 1
  },
  "engine": {
    "name": "whisper.cpp",
    "model": "base",
    "language": "auto"
  },
  "metadata": {
    "duration_seconds": 213.42,
    "created_at": "2026-07-03T12:00:00Z",
    "word_count": 512
  },
  "segments": [
    {
      "id": 0,
      "start": 0.0,
      "end": 3.25,
      "text": "example lyric line",
      "words": [
        {
          "word": "example",
          "start": 0.0,
          "end": 0.5,
          "confidence": 0.91
        }
      ]
    }
  ]
}
```

Later versions can split this into separate `segments.json` and `words.json` if the payload becomes too large.

---

## 8. Kafka / Redpanda Event Design

Use validated event payloads with Pydantic.

Every event should have:

```json
{
  "event_id": "uuid",
  "event_type": "transcription.requested",
  "occurred_at": "2026-07-03T12:00:00Z",
  "correlation_id": "uuid",
  "payload": {}
}
```

Recommended topics:

```txt
track.events
transcription.events
review.events
publication.events
```

Alternative more granular topics:

```txt
transcription.requested
transcription.progress
transcription.completed
transcription.failed
transcription.approved
transcription.published
```

For early development, use fewer topics:

```txt
sounds-right.events
```

Then split later if needed.

Important event types:

```txt
track.created
track.version.created
track.version.uploaded
transcription.requested
transcription.started
transcription.progress
transcription.completed
transcription.failed
transcription.approved
transcription.rejected
transcription.published
```

Example `transcription.requested` payload:

```json
{
  "job_id": "uuid",
  "track_version_id": "uuid",
  "audio_object_key": "temp-audio/{track_version_id}/input.mp3",
  "lyrics_object_key": null,
  "engine": "whisper.cpp",
  "options": {
    "language": "auto",
    "separate_vocals": false,
    "model": "base"
  }
}
```

Example `transcription.completed` payload:

```json
{
  "job_id": "uuid",
  "track_version_id": "uuid",
  "transcript_object_key": "transcripts/artist/track/v1/transcript.json",
  "manifest_object_key": "transcripts/artist/track/v1/manifest.json",
  "duration_seconds": 213.42,
  "word_count": 512,
  "sha256": "..."
}
```

---

## 9. API Shape

Initial API routes:

```txt
Auth
POST   /api/auth/register
POST   /api/auth/login
POST   /api/auth/refresh
POST   /api/auth/logout
GET    /api/me

Artists
GET    /api/artists
POST   /api/artists
GET    /api/artists/{artist_id}
PATCH  /api/artists/{artist_id}
DELETE /api/artists/{artist_id}

Tracks
GET    /api/tracks
POST   /api/tracks
GET    /api/tracks/{track_id}
PATCH  /api/tracks/{track_id}

Versions
POST   /api/tracks/{track_id}/versions
GET    /api/tracks/{track_id}/versions
GET    /api/versions/{version_id}
POST   /api/versions/{version_id}/upload-url
POST   /api/versions/{version_id}/upload-complete
POST   /api/versions/{version_id}/start-transcription
POST   /api/versions/{version_id}/approve
POST   /api/versions/{version_id}/reject
POST   /api/versions/{version_id}/publish

Jobs
GET    /api/jobs/{job_id}
GET    /api/jobs/{job_id}/events
GET    /api/jobs/{job_id}/stream

Public
GET    /api/public/karaoke/{artist_slug}/{track_slug}
GET    /api/public/karaoke/{artist_slug}/{track_slug}/versions/{version}
```

For job progress, start with polling:

```txt
GET /api/jobs/{job_id}
```

Later add Server-Sent Events:

```txt
GET /api/jobs/{job_id}/stream
```

Do not add WebSockets until there is a real need for bidirectional communication.

---

## 10. Worker Pipeline

The transcription worker should:

```txt
1. Consume `transcription.requested`.
2. Mark job as started by emitting `transcription.started`.
3. Download temporary audio from MinIO.
4. Validate file using ffprobe.
5. Convert to a normalized internal format if needed.
6. Run whisper.cpp.
7. Parse whisper.cpp output.
8. Normalize transcript into the project JSON schema.
9. Upload transcript artifacts to MinIO.
10. Delete temporary raw audio.
11. Emit `transcription.completed`.
12. On failure, emit `transcription.failed`.
```

The worker must use per-job temp directories:

```txt
/tmp/sounds-right/{job_id}/input
/tmp/sounds-right/{job_id}/output
/tmp/sounds-right/{job_id}/transcript.json
```

Never use a shared temp path like:

```txt
/tmp/audio_to_transcribe.mp3
```

That was a concurrency bug in the old project.

---

## 11. Envoy Routing

Initial Envoy routing:

```txt
/           -> web:3000
/api/*      -> api:8000
/health     -> api:8000/health
```

Do not publicly expose:

```txt
Postgres
Redpanda/Kafka
MinIO internal API
MinIO console
worker services
```

Envoy should eventually handle:

```txt
request IDs
access logs
CORS
compression
TLS termination
basic rate limiting
```

---

## 12. Security Requirements

Minimum security baseline:

```txt
- Passwords hashed with Argon2id or another strong modern password hasher
- JWT access tokens parsed as Bearer tokens
- Refresh tokens stored securely
- Admin/reviewer-only approval endpoints
- No raw exception messages returned to clients
- Request size limits
- File extension and MIME validation
- Real audio validation with ffprobe
- Rate limiting on login/register
- Signed upload URLs for raw audio
- Temporary raw audio deleted after processing
- Internal services not exposed publicly
```

The old project had unsafe auth assumptions and mismatched auth path skipping. This rewrite should treat auth as a first-class feature, not middleware glue.

---

## 13. What Not To Carry Over From Old Project

Do not carry over:

```txt
- Flask controllers
- manual route classes
- ApiResponseFormatter
- custom RabbitMQ client
- Celery + RabbitMQ bridge
- MongoDB models
- hand-written validation
- shared temp audio path
- object-storage-based version generation
- unfinished approval placeholder
- raw exception responses
```

Carry over only the product ideas:

```txt
- artists
- tracks
- audio upload
- optional lyrics
- async transcription
- versioned results
- review/approval flow
- production transcript publishing
- karaoke JSON structure with segments and words
```

---

## 14. Development Phases

### Phase 1 — Foundation

Goal: Get the skeleton running.

Build:

```txt
- monorepo structure
- Docker Compose
- Envoy
- Vinext app
- Litestar API
- Postgres
- Alembic
- MinIO
- Redpanda
- health checks
```

Deliverable:

```txt
Opening the app through Envoy works.
API health check works.
Database migration runs.
MinIO and Redpanda are available locally.
```

---

### Phase 2 — Core Domain API

Build:

```txt
- users/auth
- artists CRUD
- tracks CRUD
- track versions
- upload URL generation
- upload-complete endpoint
```

Deliverable:

```txt
User can create artist, create track, create version, and upload temporary audio to MinIO.
```

---

### Phase 3 — Event Flow

Build:

```txt
- Kafka/Redpanda producer in API
- event schemas with Pydantic
- transcription.requested event
- worker consumer
- job state updates
```

Deliverable:

```txt
Starting a transcription emits an event.
Worker receives it.
Job status changes from queued to started.
```

---

### Phase 4 — Whisper.cpp Worker

Build:

```txt
- whisper.cpp container or binary integration
- ffprobe validation
- per-job temp directory
- transcript output parser
- transcript JSON schema
- upload result to MinIO
- delete raw audio
```

Deliverable:

```txt
Uploaded audio produces transcript.json in MinIO.
Raw audio is removed after processing.
Job becomes completed or failed.
```

---

### Phase 5 — Review UI

Build:

```txt
- dashboard
- track list
- version list
- job status page
- transcript viewer
- approve/reject buttons
- basic karaoke preview
```

Deliverable:

```txt
Reviewer can inspect transcript and approve/reject it.
```

---

### Phase 6 — Publishing

Build:

```txt
- publish approved version
- public transcript endpoint
- manifest generation
- stable public object keys
```

Deliverable:

```txt
Approved karaoke transcript is available through public API.
```

---

### Phase 7 — Pydantic AI Enhancements

Optional later phase.

Possible features:

```txt
- transcript quality summary
- suspicious alignment detection
- automatic cleanup suggestions
- metadata enrichment
- reviewer notes
- lyric normalization
```

Pydantic AI should assist the review process, not replace deterministic validation.

---

## 15. Suggested Initial Docker Services

```txt
envoy
web
api
worker
postgres
redpanda
minio
```

Optional later:

```txt
grafana
prometheus
otel-collector
sentry
mailhog
```

---

## 16. Initial Quality Rules

Backend:

```txt
- Python 3.12+
- uv for dependency management
- Ruff for linting/formatting
- Pyright or mypy for type checks
- pytest for tests
- Alembic migrations required for DB changes
- Pydantic models for API and event contracts
```

Frontend:

```txt
- TypeScript strict mode
- generated API client
- no duplicated API types by hand
- TanStack Query for server state
- Zod for client-side form validation
```

Infrastructure:

```txt
- Docker Compose for local dev
- Envoy as only exposed public entrypoint
- internal Docker network for services
- no public Postgres/Redpanda/MinIO console in production
```

---

## 17. Core Principle

This rewrite should not be a simple modernization of the old codebase.

It should be a clean rebuild around this idea:

```txt
Metadata lives in Postgres.
Large artifacts live in MinIO.
State changes move through Kafka/Redpanda events.
The API owns commands and validation.
The worker owns transcription.
Envoy owns ingress.
Vinext owns the user interface.
whisper.cpp owns ASR.
```

The old project is a useful prototype. The new project should be treated as a proper event-driven audio transcription platform.
