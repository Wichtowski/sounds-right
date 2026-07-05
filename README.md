# Sounds Right

Sounds Right is a rewrite foundation for an event-driven karaoke transcription platform.
It includes local infrastructure, a Vinext frontend, a Litestar API, Postgres migrations, MinIO object storage, Redpanda event streaming, Envoy routing, a whisper.cpp transcription worker, and a reviewer workflow for completed transcript artifacts.

## Requirements

- Docker
- Docker Compose
- `make`
- `uv` for local Python dependency management

## Local Development

Start the full stack:

```sh
make dev
```

Open:

```txt
http://localhost:8080/
http://localhost:8080/api/health
```

Run migrations:

```sh
make migrate
```

Run checks:

```sh
make check
```

## Event-driven transcription mock flow

Create the Kafka topic through Docker Compose startup or manually with:

```sh
docker compose run --rm redpanda-init
```

After registering, logging in, creating an artist, creating a track, creating a version, uploading audio, and completing the upload, start mock transcription:

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

Check job status:

```sh
curl http://localhost:8080/api/jobs/$JOB_ID \
  -H "Authorization: Bearer $TOKEN"
```

Check the job timeline:

```sh
curl http://localhost:8080/api/jobs/$JOB_ID/events \
  -H "Authorization: Bearer $TOKEN"
```

Set `WORKER_MOCK_SHOULD_FAIL=true` in the worker environment to force the mock worker to emit `transcription.failed`.

## Real whisper.cpp transcription

The real worker runs whisper.cpp on the host using your local build and model.

1. Install `ffmpeg` (provides `ffprobe`) on the host.
2. Build whisper.cpp and download a model (either manually or using the scripts in the whisper.cpp repository), then point `.env` at them:

   ```sh
   # set WHISPER_CPP_PATH and WHISPER_MODEL_PATH in .env
   ```

3. Start the dockerized infrastructure (Postgres/Redpanda/MinIO/API/web):

   ```sh
   make dev
   ```

4. In another terminal, run the real worker on the host:

   ```sh
   make worker
   ```

The containerized `worker` service stays in mock mode (whisper.cpp is not installed
in the image); real transcription runs via `make worker`. See
[docs/transcription-worker.md](docs/transcription-worker.md) for details, the
[transcript schema](docs/transcript-schema.md), and the [event contracts](docs/events.md).

Useful commands:

```sh
make worker         # run the real whisper.cpp worker on the host
make worker-test    # run only the worker test suite
make worker-shell   # shell into the dockerized worker container
make whisper-model MODEL=base   # download a ggml model into ./models
make test           # run API + worker test suites
```

## Review workflow

Start the stack and run migrations:

```sh
make dev
make migrate
```

Open the review dashboard:

```txt
http://localhost:8080/review
```

The review queue lists completed, approved, rejected, and failed versions.
Open a completed version to inspect transcript metadata, segment timing, word timestamps, and the simulated karaoke preview.
Use the approve action when the timing is acceptable.
Use the reject action with a reason when the transcript should not move forward.

The review API is available under:

```txt
GET  /api/review/queue
GET  /api/versions/{version_id}/transcript
GET  /api/versions/{version_id}/review-events
POST /api/versions/{version_id}/approve
POST /api/versions/{version_id}/reject
```

Known limits:

- Publishing is not implemented yet
- Transcript editing is not implemented yet
- Audio playback is simulated because raw uploaded audio is cleaned up after processing
- Approval and rejection require a `reviewer` or `admin` role
