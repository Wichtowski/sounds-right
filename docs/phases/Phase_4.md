# Phase 4 — Whisper.cpp Transcription Worker

## Purpose

Implement the first real transcription pipeline for **Sounds Right**.

Phase 1 created the foundation.  
Phase 2 added the core domain API and temporary audio upload flow.  
Phase 3 added the event-driven bridge between API, Redpanda/Kafka, worker, and Postgres job state.

Phase 4 should turn the placeholder worker into a real transcription worker:

```txt
consume transcription.requested
validate uploaded audio
run whisper.cpp
normalize output into transcript JSON
upload transcript artifacts to MinIO
delete temporary raw audio
emit transcription.completed or transcription.failed
```

This phase should still avoid review UI, approval, publishing, Pydantic AI, and advanced lyrics alignment.

---

## Final Phase 4 Goal

At the end of Phase 4, this flow should work:

```txt
1. User uploads temporary audio through Phase 2 flow.
2. User starts transcription through Phase 3 flow.
3. API emits transcription.requested.
4. Worker consumes transcription.requested.
5. Worker downloads audio from MinIO.
6. Worker validates audio with ffprobe.
7. Worker runs whisper.cpp.
8. Worker creates transcript.json and manifest.json.
9. Worker uploads transcript artifacts to MinIO.
10. Worker deletes temporary raw audio from MinIO.
11. Worker emits transcription.completed.
12. Projector/API updates job and version state in Postgres.
13. Version status becomes completed.
```

Failure path:

```txt
1. Worker fails validation or transcription.
2. Worker emits transcription.failed.
3. Job status becomes failed.
4. Version status becomes failed.
5. Error code/message are stored safely.
```

---

## Existing Phase Assumptions

Assume previous phases already provide:

```txt
Envoy
Vinext frontend
Litestar API
Postgres
Alembic
MinIO
Redpanda/Kafka
worker service
transcription_jobs table
track_versions table
upload-complete flow
transcription.requested event
transcription.started/progress/completed/failed event contracts or placeholders
projector/state update mechanism
```

Do not rebuild earlier phases. Extend them.

---

## Tech Stack

Continue using:

```txt
Worker:
- Python 3.12+
- uv
- Pydantic
- aiokafka or chosen Kafka client from Phase 3
- MinIO client
- Ruff

Audio tools:
- whisper.cpp
- ffmpeg
- ffprobe

Storage:
- MinIO

Events:
- Redpanda/Kafka
```

Do not introduce:

```txt
Celery
RabbitMQ
Redis queue
MongoDB
FastAPI
Flask
faster-whisper
WhisperX
Demucs
Pydantic AI
review UI
approval flow
publishing flow
```

---

## Scope

Phase 4 includes:

```txt
worker consumption of transcription.requested
per-job temp directory handling
MinIO audio download
ffprobe validation
optional audio normalization with ffmpeg
whisper.cpp execution
transcript output parsing
transcript JSON schema v1
manifest JSON schema v1
artifact upload to MinIO
raw audio cleanup from MinIO
progress events
completed events
failed events
basic worker tests
basic end-to-end smoke flow
```

Phase 4 does not include:

```txt
lyrics upload
lyrics alignment
vocal separation
review UI
approve/reject
publishing
public karaoke endpoints
AI quality checks
multi-engine benchmarking
distributed worker scaling
advanced retry/dead-letter infrastructure beyond basic safety
```

---

## Worker Architecture

The worker should be structured around small, testable components.

Recommended structure:

```txt
apps/worker/src/sounds_right_worker/
  __init__.py
  main.py
  config.py
  logging.py

  events/
    __init__.py
    consumer.py
    producer.py
    schemas.py
    handlers.py

  storage/
    __init__.py
    minio_client.py
    object_keys.py

  audio/
    __init__.py
    ffprobe.py
    ffmpeg.py
    validation.py

  transcription/
    __init__.py
    engine.py
    whisper_cpp.py
    parser.py
    schemas.py
    manifest.py

  jobs/
    __init__.py
    tempdir.py
    cleanup.py
    pipeline.py

  tests/
    test_audio_validation.py
    test_transcript_parser.py
    test_manifest.py
    test_object_keys.py
```

Keep the main consumer thin:

```txt
Kafka consumer receives event
  -> validate event schema
  -> call TranscriptionPipeline.handle_requested(event)
  -> pipeline owns the workflow
```

---

## Event Flow

### Input Event

The worker consumes:

```txt
transcription.requested
```

Expected payload:

```json
{
  "event_id": "uuid",
  "event_type": "transcription.requested",
  "occurred_at": "2026-07-03T12:00:00Z",
  "correlation_id": "uuid",
  "payload": {
    "job_id": "uuid",
    "track_version_id": "uuid",
    "audio_object_key": "temp-audio/{track_version_id}/input.mp3",
    "engine": "whisper.cpp",
    "options": {
      "language": "auto",
      "model": "base",
      "separate_vocals": false
    }
  }
}
```

Phase 4 should ignore unsupported options safely.

For example:

```txt
separate_vocals=false supported
separate_vocals=true should return unsupported option failure for now
lyrics_object_key should be ignored or rejected depending on Phase 3 schema
```

Recommended behavior:

```txt
If unsupported advanced option is present, emit transcription.failed with error_code=unsupported_option.
```

---

## Output Events

The worker should emit these events.

### transcription.started

Emit when the worker begins processing.

```json
{
  "event_id": "uuid",
  "event_type": "transcription.started",
  "occurred_at": "2026-07-03T12:00:01Z",
  "correlation_id": "uuid",
  "payload": {
    "job_id": "uuid",
    "track_version_id": "uuid",
    "worker_name": "sounds-right-worker",
    "engine": "whisper.cpp"
  }
}
```

---

### transcription.progress

Emit coarse progress updates.

Do not overdo progress in Phase 4.

Recommended progress steps:

```txt
10 audio_downloaded
20 audio_validated
30 audio_normalized
40 transcription_started
80 transcription_finished
90 artifacts_uploaded
```

Example:

```json
{
  "event_id": "uuid",
  "event_type": "transcription.progress",
  "occurred_at": "2026-07-03T12:00:05Z",
  "correlation_id": "uuid",
  "payload": {
    "job_id": "uuid",
    "track_version_id": "uuid",
    "progress": 20,
    "stage": "audio_validated"
  }
}
```

---

### transcription.completed

Emit when artifacts are uploaded successfully.

```json
{
  "event_id": "uuid",
  "event_type": "transcription.completed",
  "occurred_at": "2026-07-03T12:02:30Z",
  "correlation_id": "uuid",
  "payload": {
    "job_id": "uuid",
    "track_version_id": "uuid",
    "transcript_object_key": "transcripts/artist-slug/track-slug/v1/transcript.json",
    "manifest_object_key": "transcripts/artist-slug/track-slug/v1/manifest.json",
    "engine": "whisper.cpp",
    "model": "base",
    "language": "en",
    "duration_seconds": 213.42,
    "word_count": 512,
    "segment_count": 84,
    "sha256": "..."
  }
}
```

If artist/track slugs are not included in the input event, the worker may use an object layout based on IDs for now:

```txt
transcripts/{track_version_id}/transcript.json
transcripts/{track_version_id}/manifest.json
```

This is acceptable in Phase 4.

Recommended Phase 4 object layout:

```txt
transcripts/{track_version_id}/transcript.json
transcripts/{track_version_id}/manifest.json
```

Human-readable slug layout can come later when publishing.

---

### transcription.failed

Emit on any failure.

```json
{
  "event_id": "uuid",
  "event_type": "transcription.failed",
  "occurred_at": "2026-07-03T12:00:20Z",
  "correlation_id": "uuid",
  "payload": {
    "job_id": "uuid",
    "track_version_id": "uuid",
    "error_code": "audio_validation_failed",
    "error_message": "Unsupported audio format",
    "stage": "audio_validation"
  }
}
```

Do not emit raw tracebacks in event payloads.

Log full internal exceptions in worker logs only.

---

## Error Codes

Use stable error codes.

Recommended initial set:

```txt
audio_not_found
audio_download_failed
audio_validation_failed
audio_too_large
audio_duration_too_long
unsupported_audio_format
unsupported_option
normalization_failed
whisper_cpp_missing
whisper_cpp_failed
transcript_parse_failed
artifact_upload_failed
temp_cleanup_failed
unknown_worker_error
```

Error messages should be safe for UI display.

---

## MinIO Requirements

Input bucket from earlier phases:

```txt
sounds-right-temp-audio
```

Output bucket:

```txt
sounds-right-transcripts
```

Optional artifact bucket:

```txt
sounds-right-artifacts
```

Phase 4 should write:

```txt
sounds-right-transcripts/transcripts/{track_version_id}/transcript.json
sounds-right-transcripts/transcripts/{track_version_id}/manifest.json
```

After successful transcription, delete:

```txt
sounds-right-temp-audio/{audio_object_key}
```

If cleanup fails after successful transcript upload, still emit `transcription.completed`, but include a warning field if the event schema supports it.

Recommended:

```json
{
  "warnings": ["temporary_audio_cleanup_failed"]
}
```

If the schema does not support warnings, log it and leave cleanup for lifecycle policy.

---

## Temp Directory Rules

Use a unique per-job temp directory.

Pattern:

```txt
/tmp/sounds-right/{job_id}/
  input_original
  input.wav
  whisper_output.json
  transcript.json
  manifest.json
```

Never use shared paths like:

```txt
/tmp/audio_to_transcribe.mp3
/tmp/input.wav
/tmp/output.json
```

Required behavior:

```txt
- create temp dir at job start
- cleanup local temp dir in finally block
- do not rely on __del__ cleanup
- do not leave large local audio files around
```

If debugging is needed, support an env flag:

```env
WORKER_KEEP_TEMP_FILES=false
```

Default must be false.

---

## Audio Validation

Use `ffprobe` before transcription.

Validate:

```txt
file exists
file has audio stream
duration is available
format is supported
file size is within configured limit
duration is within configured limit
```

Recommended config:

```env
MAX_AUDIO_SIZE_BYTES=104857600
MAX_AUDIO_DURATION_SECONDS=900
```

Default max duration can be 15 minutes for Phase 4.

Do not rely only on file extension or MIME type from upload request.

### ffprobe Output

Use JSON output:

```sh
ffprobe -v error \
  -show_format \
  -show_streams \
  -of json \
  input_file
```

Parse:

```txt
format.duration
format.size
streams where codec_type == audio
codec_name
sample_rate
channels
```

Create a typed result model:

```txt
AudioProbeResult
- duration_seconds
- size_bytes
- format_name
- codec_name
- sample_rate
- channels
```

---

## Audio Normalization

Whisper.cpp can process common formats depending on build/config, but the worker should normalize audio to WAV for predictable behavior.

Use ffmpeg:

```sh
ffmpeg -y \
  -i input_original \
  -ar 16000 \
  -ac 1 \
  -c:a pcm_s16le \
  input.wav
```

Output:

```txt
16 kHz
mono
pcm_s16le WAV
```

If ffmpeg normalization fails, emit:

```txt
normalization_failed
```

---

## Whisper.cpp Integration

Do not link whisper.cpp deeply into the Python app in Phase 4.

Use it as a CLI binary from the worker.

Recommended config:

```env
WHISPER_CPP_BIN=/usr/local/bin/whisper-cli
WHISPER_CPP_MODEL=/models/ggml-base.bin
WHISPER_CPP_LANGUAGE=auto
WHISPER_CPP_THREADS=4
```

Depending on installed whisper.cpp version, the binary may be named differently.

Support config names cleanly so the binary path can be changed without code edits.

### Expected Worker Command

Use JSON output if supported by the installed whisper.cpp build.

Example conceptual command:

```sh
$WHISPER_CPP_BIN \
  -m $WHISPER_CPP_MODEL \
  -f input.wav \
  -oj \
  -of whisper_output
```

This should produce something like:

```txt
whisper_output.json
```

If the binary uses different flags, adapt implementation to the actual installed version and document it in the worker README.

### Required Wrapper

Create:

```txt
transcription/whisper_cpp.py
```

Expose:

```python
class WhisperCppEngine:
    async def transcribe(self, input_wav: Path, output_dir: Path, options: TranscriptionOptions) -> WhisperCppResult:
        ...
```

The wrapper should:

```txt
- build command safely as argument list
- run subprocess without shell=True
- capture stdout/stderr
- enforce timeout
- verify output file exists
- parse output JSON
- return typed result
```

Never use shell string interpolation for user-controlled input.

---

## Worker Docker Image

Update worker Dockerfile to include:

```txt
Python 3.12+
uv
ffmpeg
ffprobe
whisper.cpp binary
whisper.cpp model file or mounted model volume
```

Model handling options:

### Option A — baked model

Bake the model into the worker image.

Pros:

```txt
simple local dev
worker always has model
```

Cons:

```txt
large image
model changes require rebuild
```

### Option B — mounted model volume

Mount models into:

```txt
/models
```

Pros:

```txt
smaller image
can swap models
```

Cons:

```txt
requires setup script
```

Recommended for Phase 4:

```txt
Use mounted /models volume if simple.
Otherwise bake base model for local dev.
```

Add README notes explaining how the model is obtained.

Do not commit large model binaries into git.

---

## Transcript JSON Schema v1

Create normalized transcript output.

Required file:

```txt
transcript.json
```

Schema:

```json
{
  "schema_version": "1.0",
  "track_version_id": "uuid",
  "job_id": "uuid",
  "engine": {
    "name": "whisper.cpp",
    "model": "base",
    "language": "en"
  },
  "metadata": {
    "duration_seconds": 213.42,
    "created_at": "2026-07-03T12:00:00Z",
    "word_count": 512,
    "segment_count": 84
  },
  "text": "full transcription text",
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
          "confidence": null
        }
      ]
    }
  ]
}
```

If whisper.cpp output does not provide word timestamps with the chosen flags/model, Phase 4 may emit empty `words` arrays and still include segments.

Preferred behavior:

```txt
Use word timestamps if available.
If not available, preserve segment timestamps and leave words empty.
```

Do not fake word timestamps in Phase 4.

Lyrics alignment comes later.

---

## Manifest JSON Schema v1

Create:

```txt
manifest.json
```

Schema:

```json
{
  "schema_version": "1.0",
  "track_version_id": "uuid",
  "job_id": "uuid",
  "status": "completed",
  "artifacts": {
    "transcript": {
      "object_key": "transcripts/{track_version_id}/transcript.json",
      "content_type": "application/json",
      "sha256": "..."
    }
  },
  "engine": {
    "name": "whisper.cpp",
    "model": "base"
  },
  "audio": {
    "duration_seconds": 213.42,
    "codec_name": "mp3",
    "sample_rate": 44100,
    "channels": 2
  },
  "created_at": "2026-07-03T12:00:00Z"
}
```

The manifest should be small and useful for future review/publishing phases.

---

## Checksums

Compute SHA-256 for:

```txt
transcript.json
manifest.json optional
```

The `transcription.completed` event should include the transcript checksum.

This lets the API/projector store:

```txt
transcript_sha256
```

on `track_versions`.

---

## Database / Projector Updates

Depending on Phase 3 design, the worker may not update Postgres directly.

Preferred architecture:

```txt
worker emits events
projector/API consumer updates Postgres
```

Do not make the worker directly mutate API database state unless Phase 3 already chose that explicitly.

On `transcription.started`:

```txt
transcription_jobs.status = started or processing
track_versions.status = processing
```

On `transcription.progress`:

```txt
transcription_jobs.progress = progress
insert job_event if supported
```

On `transcription.completed`:

```txt
transcription_jobs.status = completed
track_versions.status = completed
track_versions.transcript_object_key = payload.transcript_object_key
track_versions.manifest_object_key = payload.manifest_object_key
track_versions.transcript_sha256 = payload.sha256
track_versions.duration_seconds = payload.duration_seconds
track_versions.word_count = payload.word_count
```

On `transcription.failed`:

```txt
transcription_jobs.status = failed
track_versions.status = failed
transcription_jobs.error_code = payload.error_code
transcription_jobs.error_message = payload.error_message
```

---

## Idempotency Requirements

Kafka-style event processing can redeliver messages.

The worker should be reasonably idempotent.

Minimum Phase 4 idempotency:

```txt
If transcript already exists for track_version_id, worker may skip processing and emit completed again.
If job is already completed according to a lightweight API/projector check, skip if such check exists.
Object uploads should overwrite same object key safely for same track_version_id.
Temp local directories should be cleaned before reuse.
```

If the worker has no database read access, object existence check is enough for Phase 4.

Do not create duplicate transcript object paths per retry.

Use deterministic paths:

```txt
transcripts/{track_version_id}/transcript.json
transcripts/{track_version_id}/manifest.json
```

---

## Retry Behavior

Basic retry behavior is enough.

The worker should distinguish:

### Retryable errors

```txt
audio_download_failed
artifact_upload_failed
kafka_produce_failed
transient MinIO errors
```

### Non-retryable errors

```txt
audio_validation_failed
unsupported_audio_format
audio_too_large
audio_duration_too_long
unsupported_option
whisper_cpp_missing
```

Actual Kafka retry/dead-letter setup can be basic in Phase 4.

If Phase 3 added a dead-letter topic, use it.

Suggested topics:

```txt
sounds-right.events
sounds-right.dead-letter
```

If no dead-letter topic exists, log clearly and emit `transcription.failed` for non-retryable errors.

---

## Logging Requirements

Use structured logs if Phase 1/3 introduced them.

Every worker log should include:

```txt
job_id
track_version_id
correlation_id
event_id where relevant
stage
```

Important logs:

```txt
received transcription.requested
downloaded audio
validated audio
normalized audio
started whisper.cpp
finished whisper.cpp
uploaded transcript
uploaded manifest
deleted temporary audio
emitted completed
emitted failed
```

Do not log full presigned URLs.

Do not log secrets.

Do not log raw transcript text by default.

---

## Config Requirements

Add worker config fields:

```env
# Audio limits
MAX_AUDIO_SIZE_BYTES=104857600
MAX_AUDIO_DURATION_SECONDS=900

# Temp files
WORKER_TEMP_ROOT=/tmp/sounds-right
WORKER_KEEP_TEMP_FILES=false

# Whisper.cpp
WHISPER_CPP_BIN=/usr/local/bin/whisper-cli
WHISPER_CPP_MODEL=/models/ggml-base.bin
WHISPER_CPP_MODEL_NAME=base
WHISPER_CPP_THREADS=4
WHISPER_CPP_TIMEOUT_SECONDS=1800

# Transcript output
TRANSCRIPT_SCHEMA_VERSION=1.0
TRANSCRIPT_OBJECT_PREFIX=transcripts
```

Validate config at worker startup.

If `WHISPER_CPP_BIN` or model file is missing, the worker should fail fast or report unhealthy.

For local development, fail fast is acceptable.

---

## API Changes Required In Phase 4

Only minimal API changes should be needed.

Add or verify:

```txt
GET /api/jobs/{job_id}
GET /api/versions/{version_id}
```

These should show:

```txt
job status
progress
error code/message
transcript object key after completion
manifest object key after completion
version status
```

If not already available, add them.

Do not add review/approval endpoints yet.

---

## Frontend Changes Required In Phase 4

Keep frontend changes minimal.

On version/job page, show:

```txt
status
progress
current stage
error message if failed
transcript object key if completed
```

A simple polling UI is fine:

```txt
poll GET /api/jobs/{job_id} every 2 seconds while processing
```

Do not build full transcript viewer yet.

Do not build review UI yet.

Optional simple completion display:

```txt
Transcription completed
Transcript: transcripts/{track_version_id}/transcript.json
```

---

## Testing Requirements

Add unit tests for:

```txt
ffprobe parser
unsupported audio validation
object key generation
transcript parser from sample whisper.cpp output
manifest generation
checksum generation
error mapping
```

Add integration/smoke test if practical:

```txt
Given a small sample audio file in tests/fixtures
When worker pipeline runs locally
Then transcript.json is created
And manifest.json is created
```

Do not commit large audio fixtures.

Use a tiny test audio file if included.

If no audio fixture is committed, document how to run a manual smoke test.

---

## Manual Smoke Test

After Phase 4, this flow should work:

```txt
1. Start stack:
   ./scripts/dev.sh

2. Register/login through frontend or curl.

3. Create artist.

4. Create track.

5. Create version.

6. Upload a small audio file.

7. Start transcription.

8. Watch worker logs:
   docker compose logs -f worker

9. Watch API/job state:
   GET /api/jobs/{job_id}

10. Confirm MinIO contains:
   transcripts/{track_version_id}/transcript.json
   transcripts/{track_version_id}/manifest.json

11. Confirm temporary audio was deleted from temp bucket.
```

---

## Developer Scripts

Update scripts if needed.

Required commands:

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

Add worker-specific helper if useful:

```sh
./scripts/worker-shell.sh
./scripts/worker-test.sh
```

This may instruct how to place the model into `/models`.

Do not commit model binaries.

---

## Documentation Updates

Update docs with:

```txt
how whisper.cpp is installed
where model files live
how to configure WHISPER_CPP_BIN
how to configure WHISPER_CPP_MODEL
how to run a manual transcription smoke test
what transcript.json looks like
what manifest.json looks like
known limitations
```

Create or update:

```txt
docs/transcription-worker.md
docs/transcript-schema.md
docs/events.md
README.md
```

---

## Known Phase 4 Limitations

Document these clearly:

```txt
No lyrics alignment yet.
No vocal separation yet.
No transcript editor yet.
No approval flow yet.
No public publishing yet.
No Pydantic AI quality checks yet.
Word timestamps depend on whisper.cpp output support/configuration.
Raw audio is deleted only after successful worker processing.
Lifecycle cleanup for abandoned temp audio may be added later.
```

---

## Acceptance Criteria

Phase 4 is complete when:

```txt
1. Worker consumes transcription.requested events.
2. Worker emits transcription.started.
3. Worker downloads temporary audio from MinIO.
4. Worker validates audio with ffprobe.
5. Worker normalizes audio with ffmpeg.
6. Worker runs whisper.cpp through a safe subprocess wrapper.
7. Worker parses whisper.cpp output.
8. Worker creates transcript.json.
9. Worker creates manifest.json.
10. Worker uploads transcript.json to MinIO.
11. Worker uploads manifest.json to MinIO.
12. Worker computes transcript SHA-256.
13. Worker emits transcription.completed on success.
14. Worker emits transcription.failed on failure.
15. Projector/API updates job and version state from events.
16. Version becomes completed after success.
17. Version becomes failed after failure.
18. Temporary raw audio is deleted after successful processing.
19. Local temp directory is cleaned after processing.
20. Frontend/job page can show processing/completed/failed state.
21. Tests cover core parser/validation/manifest behavior.
22. Docs explain how to run whisper.cpp locally.
23. No review, approval, publishing, lyrics alignment, or Pydantic AI logic is implemented yet.
```

---

## Non-Goals

Do not implement:

```txt
lyrics upload
lyrics alignment
forced alignment
WhisperX
faster-whisper
Demucs/vocal separation
review dashboard
approve/reject
publish endpoint
public transcript endpoint
Pydantic AI
advanced RBAC
multi-worker autoscaling
Kubernetes
production observability stack
```

---

## Suggested Task Order

### Task 1 — Prepare worker Docker image

Add:

```txt
ffmpeg
ffprobe
whisper.cpp binary
model path configuration
```

Verify worker can run:

```sh
ffprobe -version
ffmpeg -version
$WHISPER_CPP_BIN --help
```

---

### Task 2 — Add worker config

Add typed config for:

```txt
MinIO
Kafka
worker temp root
whisper.cpp binary
whisper.cpp model
limits
timeout
```

Validate config on startup.

---

### Task 3 — Add temp directory manager

Implement:

```txt
create per-job temp dir
cleanup on success/failure
optional keep temp files flag
```

---

### Task 4 — Add MinIO download/upload/delete helpers

Implement:

```txt
download object to path
upload JSON object
delete object
check object exists if needed
```

---

### Task 5 — Add ffprobe validation

Implement:

```txt
run ffprobe
parse JSON
validate audio stream
validate size
validate duration
return AudioProbeResult
```

---

### Task 6 — Add ffmpeg normalization

Implement conversion to:

```txt
16kHz mono WAV pcm_s16le
```

---

### Task 7 — Add whisper.cpp wrapper

Implement safe subprocess wrapper:

```txt
no shell=True
timeout
stdout/stderr capture
output file verification
error mapping
```

---

### Task 8 — Add transcript parser and schema

Implement:

```txt
parse whisper.cpp JSON
normalize to transcript schema v1
support segments
support words if available
```

---

### Task 9 — Add manifest and checksum

Implement:

```txt
manifest.json
sha256 calculation
metadata summary
```

---

### Task 10 — Add full pipeline

Implement:

```txt
handle transcription.requested
emit started/progress/completed/failed
cleanup local temp files
cleanup temporary audio from MinIO on success
```

---

### Task 11 — Wire worker consumer

Connect Kafka consumer handler to pipeline.

Verify logs show event received and processed.

---

### Task 12 — Update API/projector state handling

Ensure completed/failed events update Postgres fields correctly.

---

### Task 13 — Update frontend job status view

Show:

```txt
queued/processing/completed/failed
progress
error message
transcript object key
```

---

### Task 14 — Add tests and docs

Add tests for validation/parser/manifest/checksum.

Update README/docs.

---

## Final Verification Commands

Start stack:

```sh
./scripts/dev.sh
```

Watch worker:

```sh
docker compose logs -f worker
```

Run health check:

```sh
curl http://localhost:8080/api/health
```

After uploading and starting transcription, check job:

```sh
curl http://localhost:8080/api/jobs/{job_id} \
  -H "Authorization: Bearer $TOKEN"
```

Expected eventual job result:

```json
{
  "id": "uuid",
  "status": "completed",
  "progress": 100,
  "transcript_object_key": "transcripts/{track_version_id}/transcript.json",
  "manifest_object_key": "transcripts/{track_version_id}/manifest.json"
}
```

Expected MinIO objects:

```txt
sounds-right-transcripts/transcripts/{track_version_id}/transcript.json
sounds-right-transcripts/transcripts/{track_version_id}/manifest.json
```

Expected temp audio:

```txt
sounds-right-temp-audio/temp-audio/{track_version_id}/input.ext
```

should be deleted after successful processing.

---

## Definition of Done

Phase 4 is done when Sounds Right can process one uploaded audio file end-to-end:

```txt
Uploaded temporary audio goes in.
whisper.cpp runs in the worker.
Transcript artifacts come out in MinIO.
Raw audio is deleted.
Kafka events describe the state changes.
Postgres reflects completed or failed state.
The UI can show the job result.
```

After this phase, the system is ready for Phase 5: review UI, transcript inspection, approve/reject flow, and basic karaoke preview.
