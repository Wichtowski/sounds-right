# Transcript Schema v1

The worker writes two JSON documents per completed version to the
`sounds-right-transcripts` bucket.

## transcript.json

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
        { "word": "example", "start": 0.0, "end": 0.5, "confidence": null }
      ]
    }
  ]
}
```

Notes:

- Segment timestamps are derived from whisper.cpp millisecond offsets.
- `words` is populated only when word timestamps are available. It is left empty rather than fabricated from subword tokens.
- `word_count` is computed from segment text.

## manifest.json

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
  "engine": { "name": "whisper.cpp", "model": "base" },
  "audio": {
    "duration_seconds": 213.42,
    "codec_name": "mp3",
    "sample_rate": 44100,
    "channels": 2
  },
  "created_at": "2026-07-03T12:00:00Z"
}
```

The SHA-256 of `transcript.json` is included in `transcription.completed` and
stored on `track_versions.transcript_sha256`.
