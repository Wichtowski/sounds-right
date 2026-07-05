# Sounds Right Architecture

Sounds Right is a local-first rewrite of a karaoke transcription platform.
The architecture uses Envoy as the only documented public entrypoint and keeps implementation services private.

```txt
Client
  -> Envoy
     -> web
     -> api
        -> PostgreSQL
        -> MinIO
        -> Redpanda
     -> worker
        -> Redpanda
```

The API is responsible for validation, state, object references, and event production.
The worker is a placeholder in and will later consume events for transcription work.
