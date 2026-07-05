# Phase 1 — Foundation

## Purpose

Set up the new **Sounds Right** rewrite foundation.

This phase must create a clean monorepo with local infrastructure, a working frontend shell, a working backend shell, database migrations, object storage, Kafka-compatible event infrastructure, and Envoy as the only public entrypoint.

This phase does **not** implement transcription, upload flows, auth, artists, tracks, or business logic. It only creates the technical base that later phases will build on.

---

## Final Phase 1 Goal

At the end of Phase 1, the project should run locally with one command and expose:

```txt
http://localhost:8080/              -> Vinext frontend through Envoy
http://localhost:8080/api/health    -> Litestar API through Envoy
```

The following services should run in Docker Compose:

```txt
envoy
web
api
worker
postgres
redpanda
minio
```

The project should also support:

```txt
API health check
worker health check or placeholder worker boot
Postgres connection
Alembic migration setup
MinIO bucket bootstrap
Redpanda/Kafka connectivity check
Envoy routing
shared environment configuration
basic developer commands
```

---

## Tech Stack For Phase 1

Use these technologies:

```txt
Frontend:
- Vinext
- React
- TypeScript
- Tailwind CSS

Backend:
- Python 3.12+
- Litestar
- Pydantic
- SQLAlchemy
- Alembic
- uv
- Ruff

Database:
- PostgreSQL

Object Storage:
- MinIO

Events:
- Redpanda
- Kafka protocol

Reverse Proxy:
- Envoy

Local Runtime:
- Docker Compose
```

Do not introduce:

```txt
Next.js
Vercel-specific assumptions
FastAPI
Flask
MongoDB
Celery
Redis queue
RabbitMQ
Whisper.cpp integration yet
actual transcription yet
auth yet
track/artist APIs yet
```

---

## Repository Structure

Create this structure:

```txt
sounds-right/
  apps/
    web/
      package.json
      tsconfig.json
      vite/vinext config files
      src/
        app/
        components/
        lib/
        styles/

    api/
      pyproject.toml
      uv.lock
      src/
        sounds_right_api/
          __init__.py
          main.py
          config.py
          health.py
          db/
            __init__.py
            session.py
            base.py
          events/
            __init__.py
            producer.py
          storage/
            __init__.py
            minio_client.py
      migrations/
        env.py
        script.py.mako
        versions/

    worker/
      pyproject.toml
      uv.lock
      src/
        sounds_right_worker/
          __init__.py
          main.py
          config.py
          health.py
          events/
            consumer.py

  packages/
    contracts/
      README.md
      events/
        README.md
      schemas/
        README.md

  infra/
    envoy/
      envoy.yaml

    postgres/
      README.md

    minio/
      create-buckets.sh

    redpanda/
      README.md

  scripts/
    dev.sh
    down.sh
    logs.sh
    migrate.sh
    lint.sh
    format.sh
    check.sh

  docs/
    architecture.md
    phase_1.md

  docker-compose.yml
  .env.example
  .gitignore
  README.md
```

If some Vinext-specific files differ, use the correct files for Vinext, but keep the `apps/web` boundary clean.

---

## Environment Variables

Create `.env.example`.

Required variables:

```env
# General
APP_ENV=local
APP_NAME=sounds-right

# Public ports
ENVOY_PORT=8080
WEB_PORT=3000
API_PORT=8000

# Postgres
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=sounds_right
POSTGRES_USER=sounds_right
POSTGRES_PASSWORD=sounds_right_password
DATABASE_URL=postgresql+asyncpg://sounds_right:sounds_right_password@postgres:5432/sounds_right

# MinIO
MINIO_ENDPOINT=minio:9000
MINIO_PUBLIC_ENDPOINT=localhost:9000
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin_password
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin_password
MINIO_TEMP_AUDIO_BUCKET=sounds-right-temp-audio
MINIO_TRANSCRIPTS_BUCKET=sounds-right-transcripts
MINIO_ARTIFACTS_BUCKET=sounds-right-artifacts
MINIO_SECURE=false

# Redpanda / Kafka
KAFKA_BOOTSTRAP_SERVERS=redpanda:9092
KAFKA_CLIENT_ID=sounds-right-local

# API
API_HOST=0.0.0.0
API_PORT=8000
CORS_ALLOWED_ORIGINS=http://localhost:8080,http://localhost:3000

# Worker
WORKER_NAME=sounds-right-worker
```

Create local `.env` from `.env.example` only if needed. Do not commit secrets.

---

## Docker Compose Requirements

Create `docker-compose.yml` with these services:

### 1. envoy

Responsibilities:

```txt
- expose port 8080
- route frontend traffic to web
- route /api/* traffic to api
- add request IDs if simple
- log access requests
```

Depends on:

```txt
web
api
```

### 2. web

Responsibilities:

```txt
- run Vinext dev server
- expose internal port 3000
- show basic home page
```

The frontend should be reachable only through Envoy for normal local usage.

### 3. api

Responsibilities:

```txt
- run Litestar app
- expose internal port 8000
- provide /api/health
- connect to Postgres
- optionally check MinIO and Redpanda in health details
```

### 4. worker

Responsibilities:

```txt
- boot a placeholder worker process
- connect to Redpanda/Kafka if practical
- log that it is ready
- no transcription work yet
```

### 5. postgres

Use Postgres 16 or newer.

Requirements:

```txt
- persistent Docker volume
- database name from env
- user/password from env
- healthcheck
```

### 6. redpanda

Use Redpanda as Kafka-compatible local event broker.

Requirements:

```txt
- expose internal Kafka port to app services
- optional external port for debugging
- persistent Docker volume optional
- healthcheck if practical
```

### 7. minio

Requirements:

```txt
- persistent Docker volume
- internal API port 9000
- console port may be available locally but should not be routed through Envoy
- root credentials from env
```

### 8. minio-init

Optional one-shot service.

Responsibilities:

```txt
- create required buckets
- make buckets private
```

Buckets:

```txt
sounds-right-temp-audio
sounds-right-transcripts
sounds-right-artifacts
```

---

## Envoy Routing

Create `infra/envoy/envoy.yaml`.

Required routes:

```txt
/api/*  -> api:8000
/*      -> web:3000
```

Desired local behavior:

```txt
GET http://localhost:8080/
returns frontend shell

GET http://localhost:8080/api/health
returns API health JSON
```

Important:

Do not expose these through Envoy:

```txt
Postgres
Redpanda
MinIO console
MinIO internal API
worker
```

For local development, Docker Compose may expose some debug ports directly, but the documented app entrypoint should be Envoy.

---

## Backend API Requirements

Use Litestar.

Create an app factory or application entrypoint in:

```txt
apps/api/src/sounds_right_api/main.py
```

Required route:

```txt
GET /api/health
```

Response example:

```json
{
  "status": "ok",
  "service": "sounds-right-api",
  "environment": "local",
  "checks": {
    "database": "ok",
    "minio": "ok",
    "kafka": "ok"
  }
}
```

If MinIO/Kafka checks are not stable yet, return:

```json
{
  "status": "ok",
  "service": "sounds-right-api",
  "environment": "local",
  "checks": {
    "database": "ok",
    "minio": "skipped",
    "kafka": "skipped"
  }
}
```

But the API should at least validate that config loads correctly.

### Backend Config

Create strongly typed config using Pydantic settings or a clean equivalent.

Config should include:

```txt
app_env
database_url
minio endpoint
minio access key
minio secret key
bucket names
kafka bootstrap servers
cors origins
```

Do not scatter `os.getenv` throughout the codebase.

### Database Setup

Use:

```txt
SQLAlchemy async engine
Alembic migrations
asyncpg driver
```

Create:

```txt
apps/api/src/sounds_right_api/db/session.py
apps/api/src/sounds_right_api/db/base.py
```

No real domain tables are required in Phase 1, but Alembic must be initialized and ready.

Create one initial migration if useful, for example:

```txt
001_create_migration_health_table
```

Possible table:

```sql
CREATE TABLE migration_health (
    id integer PRIMARY KEY,
    created_at timestamptz NOT NULL DEFAULT now()
);
```

This is optional, but it helps verify migrations.

### API Dependencies

Use `uv`.

The API should have commands for:

```txt
run dev server
run migrations
run lint
run format
run tests
```

---

## Worker Requirements

Create a placeholder worker in:

```txt
apps/worker/src/sounds_right_worker/main.py
```

The worker should:

```txt
- start successfully
- load config
- log service name and environment
- optionally connect to Redpanda/Kafka
- remain running
```

It should not transcribe anything yet.

Create placeholder modules:

```txt
events/consumer.py
health.py
config.py
```

The worker should be ready for Phase 3 event consumption.

Do not add whisper.cpp yet.

---

## Frontend Requirements

Create Vinext frontend in:

```txt
apps/web
```

The first page should show:

```txt
Sounds Right
Event-driven karaoke transcription platform
API status: loading / ok / error
```

The frontend should call:

```txt
GET /api/health
```

through Envoy-relative path, not hardcoded service URLs.

Example:

```ts
fetch("/api/health")
```

Do not call:

```txt
http://api:8000
http://localhost:8000
```

The frontend should be environment-portable.

Use TypeScript strict mode.

Add basic Tailwind setup if practical in Phase 1.

---

## Contracts Package

Create:

```txt
packages/contracts
```

For Phase 1, it can contain only docs and placeholders.

Create:

```txt
packages/contracts/README.md
packages/contracts/events/README.md
packages/contracts/schemas/README.md
```

Purpose:

```txt
- future OpenAPI generated clients
- future Kafka event schemas
- future transcript JSON schema
```

No heavy implementation yet.

---

## Scripts

Create scripts in `scripts/`.

### `scripts/dev.sh`

Should start local development:

```sh
docker compose up --build
```

### `scripts/down.sh`

Should stop local development:

```sh
docker compose down
```

### `scripts/logs.sh`

Should show logs:

```sh
docker compose logs -f
```

### `scripts/migrate.sh`

Should run Alembic migrations inside the API container.

Example behavior:

```sh
docker compose exec api uv run alembic upgrade head
```

### `scripts/lint.sh`

Should run lint checks for API and worker.

### `scripts/format.sh`

Should format API and worker.

### `scripts/check.sh`

Should run the basic project checks.

Expected checks:

```txt
API lint
worker lint
frontend typecheck if available
backend import check
```

Scripts should be simple and understandable.

---

## README Requirements

Create or update root `README.md`.

It must include:

```txt
project description
tech stack
local setup
how to start
how to stop
how to view logs
how to run migrations
service URLs
phase 1 scope
what is intentionally not implemented yet
```

Required local URLs:

```txt
App through Envoy: http://localhost:8080
API health:        http://localhost:8080/api/health
MinIO console:     http://localhost:9001, if exposed directly
Redpanda console:  optional, only if included
```

Mention that Envoy is the intended app entrypoint.

---

## `.gitignore`

Include ignores for:

```txt
.env
.venv
__pycache__
.pytest_cache
.ruff_cache
.mypy_cache
node_modules
dist
build
.next
.vinext
coverage
.DS_Store
```

Add any Vinext-specific build/cache folders if generated.

---

## Acceptance Criteria

Phase 1 is complete when all of these are true:

```txt
1. `docker compose up --build` starts the stack.
2. Envoy is available on http://localhost:8080.
3. Frontend loads through Envoy.
4. Frontend can call /api/health.
5. API health endpoint returns JSON.
6. API can load config from environment.
7. API can connect to Postgres or clearly reports DB check.
8. Alembic is initialized and migration command works.
9. MinIO starts and required buckets are created.
10. Redpanda starts and is reachable by internal services.
11. Worker container starts and stays running.
12. Root README explains how to run the project.
13. No old Flask/Celery/RabbitMQ/MongoDB code is carried over.
14. No transcription logic is implemented in this phase.
15. No raw audio upload logic is implemented in this phase.
```

---

## Non-Goals

Do not implement these in Phase 1:

```txt
auth
users
artists CRUD
tracks CRUD
track versions
signed upload URLs
actual file upload
Kafka event publishing
Kafka event consumption
whisper.cpp
transcription
review UI
approval flow
public karaoke endpoints
Pydantic AI
```

Only create clean placeholders where helpful.

---

## Implementation Notes For AI IDE Agent

Follow these rules:

```txt
- Prefer simple, explicit code over clever abstractions.
- Do not over-engineer Phase 1.
- Keep all services bootable before adding polish.
- Commit to the chosen architecture.
- Do not reintroduce Flask, Celery, RabbitMQ, Redis queue, MongoDB, or Next.js.
- Do not implement later-phase features early.
- Use typed config instead of random environment reads.
- Keep service boundaries clean.
- Make the project easy to run locally.
```

When uncertain, choose the smallest working foundation that supports later phases.

---

## Suggested Task Order

### Task 1 — Create monorepo skeleton

Create all top-level directories and placeholder READMEs.

Expected result:

```txt
apps/web
apps/api
apps/worker
packages/contracts
infra/envoy
infra/minio
infra/redpanda
infra/postgres
scripts
docs
```

---

### Task 2 — Create Docker Compose

Add services:

```txt
envoy
web
api
worker
postgres
redpanda
minio
minio-init
```

Make sure containers share an internal network.

---

### Task 3 — Add Litestar API

Create minimal API app with:

```txt
GET /api/health
```

Run it inside Docker.

---

### Task 4 — Add Postgres + Alembic

Create SQLAlchemy async setup and Alembic config.

Verify migration command works.

---

### Task 5 — Add MinIO

Start MinIO and create required buckets.

Verify bucket creation logs.

---

### Task 6 — Add Redpanda

Start Redpanda.

Add a basic connectivity placeholder from API or worker if simple.

---

### Task 7 — Add Worker Shell

Create placeholder worker that starts, loads config, logs readiness, and stays alive.

---

### Task 8 — Add Vinext Frontend

Create frontend shell.

It should call `/api/health`.

---

### Task 9 — Add Envoy

Route:

```txt
/api/* -> api:8000
/*     -> web:3000
```

Verify both frontend and API health work through port 8080.

---

### Task 10 — Add Scripts + README

Add developer scripts and document the setup.

---

## Final Verification Commands

These commands should work by the end of Phase 1:

```sh
cp .env.example .env
./scripts/dev.sh
```

Then in another terminal:

```sh
curl http://localhost:8080/api/health
```

Expected result:

```json
{
  "status": "ok",
  "service": "sounds-right-api"
}
```

Frontend check:

```txt
Open http://localhost:8080
```

Expected result:

```txt
Sounds Right page loads and shows API status.
```

Migration check:

```sh
./scripts/migrate.sh
```

Shutdown:

```sh
./scripts/down.sh
```

---

## Definition of Done

Phase 1 is done when the project has a boring but solid foundation:

```txt
Envoy is the front door.
Vinext frontend loads.
Litestar API responds.
Postgres is ready.
Alembic is ready.
MinIO buckets exist.
Redpanda is running.
Worker shell is alive.
Docs explain how to run everything.
No later-phase business logic has leaked in.
```

The next phase can then safely implement the core domain API.
