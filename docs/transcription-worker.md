# Transcription Worker

The transcription worker consumes `transcription.requested` events, runs
whisper.cpp, produces transcript artifacts in MinIO, and emits lifecycle events
that the API projector applies to Postgres.

## Pipeline

```txt
consume transcription.requested
  -> emit transcription.started
  -> download temporary audio from MinIO        (progress 10, audio_downloaded)
  -> validate audio with ffprobe                (progress 20, audio_validated)
  -> normalize to 16kHz mono WAV with ffmpeg     (progress 30, audio_normalized)
  -> run whisper.cpp                            (progress 40 -> 80)
  -> build transcript.json + manifest.json
  -> upload artifacts to MinIO                  (progress 90, artifacts_uploaded)
  -> delete temporary raw audio from MinIO
  -> emit transcription.completed
```

On any mapped failure the worker emits `transcription.failed` with a stable
`error_code`. Local temp directories are always cleaned in a `finally` block
(unless `WORKER_KEEP_TEMP_FILES=true`).

## Modes

- `WORKER_MOCK_MODE=false` (default): real whisper.cpp pipeline.
- `WORKER_MOCK_MODE=true`: emits mock lifecycle events without touching audio.

The dockerized `worker` service is forced to mock mode (whisper.cpp/ffmpeg are
not installed in the image). Run the real worker on the host with `make worker`.

## whisper.cpp installation

whisper.cpp and its model are provisioned outside the worker code:

- **Locally**: build whisper.cpp and download a model on your host, then set
  `WHISPER_CPP_PATH` and `WHISPER_MODEL_PATH` in `.env` (host paths, `~` is
  expanded automatically).
- **CI**: the GitHub workflow clones/builds whisper.cpp and downloads the model.

Model binaries must never be committed to git (see `.gitignore`).

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `WHISPER_CPP_PATH` | `/usr/local/bin/whisper-cli` | whisper.cpp binary |
| `WHISPER_MODEL_PATH` | `/models/ggml-base.bin` | ggml model file |
| `WHISPER_CPP_MODEL_NAME` | `base` | model name recorded in artifacts |
| `WHISPER_CPP_LANGUAGE` | `auto` | default language |
| `WHISPER_CPP_THREADS` | `4` | worker threads |
| `WHISPER_CPP_TIMEOUT_SECONDS` | `1800` | subprocess timeout |
| `FFMPEG_PATH` / `FFPROBE_PATH` | `ffmpeg` / `ffprobe` | audio tools |
| `MAX_AUDIO_SIZE_BYTES` | `104857600` | max input size |
| `MAX_AUDIO_DURATION_SECONDS` | `900` | max input duration |
| `WORKER_TEMP_ROOT` | `/tmp/sounds-right` | per-job temp root |
| `WORKER_KEEP_TEMP_FILES` | `false` | keep temp files for debugging |
| `TRANSCRIPT_SCHEMA_VERSION` | `1.0` | transcript/manifest schema version |
| `TRANSCRIPT_OBJECT_PREFIX` | `transcripts` | object key prefix |

The worker fails fast on startup (in non-mock mode) if the whisper.cpp binary or
model file is missing.

## Object layout

```txt
sounds-right-transcripts/transcripts/{track_version_id}/transcript.json
sounds-right-transcripts/transcripts/{track_version_id}/manifest.json
```

Temporary raw audio in `sounds-right-temp-audio` is deleted after successful
processing.

## Error codes

`audio_not_found`, `audio_download_failed`, `audio_validation_failed`,
`audio_too_large`, `audio_duration_too_long`, `unsupported_audio_format`,
`unsupported_option`, `normalization_failed`, `whisper_cpp_missing`,
`whisper_cpp_failed`, `transcript_parse_failed`, `artifact_upload_failed`,
`temp_cleanup_failed`, `unknown_worker_error`.

## Manual smoke test

1. `make dev`
2. Register/login, create artist, track, version; upload a small audio file and
   complete the upload.
3. Start transcription:

   ```sh
   curl -X POST http://localhost:8080/api/versions/$VERSION_ID/start-transcription \
     -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
     -d '{"engine":"whisper.cpp","options":{"language":"auto","model":"base","separate_vocals":false}}'
   ```

4. Run the real worker on the host: `make worker`
5. Poll `GET /api/jobs/{job_id}` until `completed`.
6. Confirm MinIO contains `transcripts/{track_version_id}/transcript.json` and
   `manifest.json`, and that the temporary audio was deleted.

## Known limitations

- No lyrics alignment, vocal separation, transcript editor, approval, or publishing.
- Word timestamps depend on whisper.cpp output support; leaves `words`
  empty rather than fabricating them.
- Raw audio is only deleted after successful processing; abandoned temp audio
  relies on future lifecycle cleanup.
