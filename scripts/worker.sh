#!/bin/sh
set -eu

# Run the real transcription worker on the host machine.
#
# This uses your locally built whisper.cpp binary and downloaded model
# (WHISPER_CPP_PATH / WHISPER_MODEL_PATH in .env) plus a host-installed ffmpeg.
# It connects to the dockerized Postgres/Redpanda/MinIO via their published
# host ports, so run `make dev` (or `docker compose up`) first.
#
# ffmpeg + ffprobe must be installed on the host (e.g. `apt install ffmpeg`).

# Load root .env into the environment (worker config also reads it directly).
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ -f "$REPO_ROOT/.env" ]; then
  set -a
  . "$REPO_ROOT/.env"
  set +a
fi

# Override docker-internal hostnames with the published host ports.
export KAFKA_BOOTSTRAP_SERVERS="${KAFKA_BOOTSTRAP_SERVERS_HOST:-localhost:19092}"
export MINIO_ENDPOINT="${MINIO_ENDPOINT_HOST:-localhost:9000}"

cd "$REPO_ROOT/apps/worker"
uv run python -m sounds_right_worker.main
