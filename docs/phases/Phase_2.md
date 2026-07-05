# Phase 2 — Core Domain API

## Purpose

Implement the first real product layer of **Sounds Right** on top of the Phase 1 foundation.

Phase 1 created the technical base: monorepo, Envoy, Vinext, Litestar API, Postgres, Alembic, MinIO, Redpanda, and a placeholder worker.

Phase 2 should add the core backend domain model and API needed before transcription can exist:

```txt
users/auth
artists
tracks
track versions
temporary audio upload URL generation
upload completion tracking
```

This phase should still avoid transcription logic. It should prepare the system so Phase 3 can emit events and Phase 4 can process audio.

---

## Final Phase 2 Goal

At the end of Phase 2, a user should be able to:

```txt
1. Register.
2. Log in.
3. Create an artist.
4. Create a track for that artist.
5. Create a new version of the track.
6. Request a signed upload URL for the version.
7. Upload an audio file directly to MinIO using that URL.
8. Call upload-complete.
9. See the version status change to uploaded.
```

The system should not transcribe anything yet.

---

## Existing Phase 1 Assumptions

Assume Phase 1 already provides:

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
basic health endpoints
```

Do not rebuild Phase 1. Extend it.

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
- MinIO client
- uv
- Ruff

Frontend:
- Vinext
- React
- TypeScript
- Tailwind
- TanStack Query

Infra:
- Envoy
- Docker Compose
- MinIO
- Redpanda, but no required event publishing yet
```

Do not introduce:

```txt
FastAPI
Flask
Next.js
MongoDB
Celery
RabbitMQ
Redis queue
Whisper.cpp
actual transcription worker logic
Pydantic AI
```

---

## Scope

Phase 2 includes:

```txt
auth models
password hashing
JWT/session flow
user table
artist table
track table
track version table
basic API CRUD
signed upload URL generation
upload completion endpoint
frontend forms/pages for basic flow
```

Phase 2 does not include:

```txt
Kafka event publishing
transcription.requested event
worker consuming jobs
whisper.cpp
lyrics alignment
review UI
approval flow
publishing flow
public karaoke endpoint
Pydantic AI features
```

---

## Domain Model

Create real database models and migrations.

Use UUID primary keys unless there is a strong reason not to.

Use timezone-aware timestamps.

Recommended base columns:

```txt
id
created_at
updated_at
```

Use soft deletes only if easy. Otherwise keep hard delete out of Phase 2 and avoid exposing delete endpoints unless needed.

---

## Tables

### users

```txt
users
- id uuid primary key
- email text unique not null
- username text unique not null
- password_hash text not null
- role text not null default 'user'
- is_active boolean not null default true
- created_at timestamptz not null
- updated_at timestamptz not null
```

Allowed roles:

```txt
user
reviewer
admin
```

Phase 2 can create only normal users through registration.

Reviewer/admin seeding can be handled later or via a manual script.

---

### artists

```txt
artists
- id uuid primary key
- slug text unique not null
- display_name text not null
- full_name text nullable
- created_by_user_id uuid nullable references users(id)
- created_at timestamptz not null
- updated_at timestamptz not null
```

Slug should be generated from `display_name`.

Slug collisions should be handled safely.

Example:

```txt
Kendrick Lamar -> kendrick-lamar
Kendrick Lamar duplicate -> kendrick-lamar-2
```

---

### tracks

```txt
tracks
- id uuid primary key
- artist_id uuid not null references artists(id)
- title text not null
- album text nullable
- slug text not null
- created_by_user_id uuid nullable references users(id)
- created_at timestamptz not null
- updated_at timestamptz not null
```

Add unique constraint:

```txt
unique(artist_id, slug)
```

Slug should be generated from `title`.

---

### track_versions

```txt
track_versions
- id uuid primary key
- track_id uuid not null references tracks(id)
- version integer not null
- status text not null
- temporary_audio_object_key text nullable
- original_audio_filename text nullable
- audio_content_type text nullable
- audio_size_bytes bigint nullable
- transcript_object_key text nullable
- manifest_object_key text nullable
- transcript_sha256 text nullable
- transcript_schema_version text nullable
- duration_seconds numeric nullable
- word_count integer nullable
- created_by_user_id uuid nullable references users(id)
- created_at timestamptz not null
- updated_at timestamptz not null
```

Add unique constraint:

```txt
unique(track_id, version)
```

Initial statuses:

```txt
draft
upload_url_created
uploaded
processing
completed
failed
```

Only these statuses are needed in Phase 2:

```txt
draft
upload_url_created
uploaded
```

Do not implement approval/publishing statuses yet unless the enum already includes them for future use.

---

### Optional: upload_sessions

This table is optional, but recommended if clean.

```txt
upload_sessions
- id uuid primary key
- track_version_id uuid not null references track_versions(id)
- object_key text not null
- original_filename text not null
- content_type text not null
- max_size_bytes bigint not null
- expires_at timestamptz not null
- completed_at timestamptz nullable
- created_at timestamptz not null
```

Use this if you want a clean upload flow.

If you skip it, store upload metadata directly on `track_versions`.

Recommended: use `upload_sessions`.

---

## Status Rules

Track version status transitions in Phase 2:

```txt
draft
  -> upload_url_created
  -> uploaded
```

Invalid transitions should be rejected.

Examples:

```txt
Cannot call upload-complete before upload-url exists.
Cannot request upload URL for a version that is already uploaded.
Cannot upload-complete if the object does not exist in MinIO.
```

---

## Auth Requirements

Implement basic auth properly.

### Password Hashing

Use a strong password hasher.

Preferred:

```txt
argon2-cffi
```

Acceptable:

```txt
passlib[argon2]
```

Do not use Werkzeug password hashing from the old project.

### Token Flow

Implement:

```txt
POST /api/auth/register
POST /api/auth/login
GET  /api/me
```

Optional in Phase 2:

```txt
POST /api/auth/refresh
POST /api/auth/logout
```

If refresh/logout would slow Phase 2 too much, document them as Phase 2.5 or Phase 3.

JWT access token is acceptable for Phase 2.

Requirements:

```txt
- Authorization header must use Bearer token format.
- Do not decode raw Authorization header directly.
- JWT secret must be required in config.
- Token expiry must be configurable.
- API must return 401 for missing/invalid/expired token.
```

### Auth Response Shape

Register response:

```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "username": "oskar",
    "role": "user"
  },
  "access_token": "jwt",
  "token_type": "bearer"
}
```

Login response:

```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "username": "oskar",
    "role": "user"
  },
  "access_token": "jwt",
  "token_type": "bearer"
}
```

Do not return password hashes.

---

## API Endpoints

All routes should live under `/api`.

---

### Health

Already exists from Phase 1.

Keep:

```txt
GET /api/health
```

---

### Auth

```txt
POST /api/auth/register
POST /api/auth/login
GET  /api/me
```

#### POST /api/auth/register

Request:

```json
{
  "email": "user@example.com",
  "username": "oskar",
  "password": "strong-password"
}
```

Rules:

```txt
email required
username required
password required
email unique
username unique
password minimum length: 8
```

Response:

```txt
201 Created
```

Return user and access token.

---

#### POST /api/auth/login

Request:

```json
{
  "email_or_username": "oskar",
  "password": "strong-password"
}
```

Response:

```txt
200 OK
```

Return user and access token.

Errors:

```txt
401 for invalid credentials
403 for inactive user
```

---

#### GET /api/me

Requires auth.

Response:

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "username": "oskar",
  "role": "user"
}
```

---

### Artists

```txt
GET    /api/artists
POST   /api/artists
GET    /api/artists/{artist_id}
PATCH  /api/artists/{artist_id}
```

No delete required in Phase 2.

#### POST /api/artists

Requires auth.

Request:

```json
{
  "display_name": "Kendrick Lamar",
  "full_name": "Kendrick Lamar Duckworth"
}
```

Response:

```json
{
  "id": "uuid",
  "slug": "kendrick-lamar",
  "display_name": "Kendrick Lamar",
  "full_name": "Kendrick Lamar Duckworth"
}
```

Rules:

```txt
display_name required
slug generated by backend
slug unique
```

---

#### GET /api/artists

Public or authenticated is acceptable.

Recommended: public.

Support basic query params:

```txt
search
limit
offset
```

Example:

```txt
GET /api/artists?search=kendrick&limit=20&offset=0
```

---

#### GET /api/artists/{artist_id}

Return one artist.

---

#### PATCH /api/artists/{artist_id}

Requires auth.

For Phase 2, allow creator/admin checks only if simple.

Request:

```json
{
  "display_name": "Kendrick Lamar",
  "full_name": "Kendrick Lamar Duckworth"
}
```

---

### Tracks

```txt
GET    /api/tracks
POST   /api/tracks
GET    /api/tracks/{track_id}
PATCH  /api/tracks/{track_id}
GET    /api/artists/{artist_id}/tracks
```

No delete required in Phase 2.

#### POST /api/tracks

Requires auth.

Request:

```json
{
  "artist_id": "uuid",
  "title": "squabble up",
  "album": "GNX"
}
```

Response:

```json
{
  "id": "uuid",
  "artist_id": "uuid",
  "title": "squabble up",
  "album": "GNX",
  "slug": "squabble-up"
}
```

Rules:

```txt
artist_id must exist
title required
slug generated from title
unique artist_id + slug
```

---

#### GET /api/tracks

Support:

```txt
search
artist_id
limit
offset
```

---

#### GET /api/artists/{artist_id}/tracks

Return tracks for a specific artist.

---

#### GET /api/tracks/{track_id}

Return track with artist summary and latest version summary if simple.

---

#### PATCH /api/tracks/{track_id}

Requires auth.

Allow updating:

```txt
title
album
```

If title changes, decide whether slug changes. For Phase 2, simplest rule:

```txt
Do not auto-change slug after creation.
```

---

### Track Versions

```txt
POST /api/tracks/{track_id}/versions
GET  /api/tracks/{track_id}/versions
GET  /api/versions/{version_id}
POST /api/versions/{version_id}/upload-url
POST /api/versions/{version_id}/upload-complete
```

---

#### POST /api/tracks/{track_id}/versions

Requires auth.

Creates the next version number transactionally.

Request:

```json
{}
```

Optional request:

```json
{
  "notes": "first test upload"
}
```

Response:

```json
{
  "id": "uuid",
  "track_id": "uuid",
  "version": 1,
  "status": "draft"
}
```

Rules:

```txt
track must exist
version number must be generated by database-safe logic
unique(track_id, version)
```

Avoid object-storage-based version generation. That was a problem in the old project.

---

#### GET /api/tracks/{track_id}/versions

Return versions for a track.

---

#### GET /api/versions/{version_id}

Return version detail.

---

#### POST /api/versions/{version_id}/upload-url

Requires auth.

Creates a presigned URL for temporary audio upload to MinIO.

Request:

```json
{
  "filename": "song.mp3",
  "content_type": "audio/mpeg",
  "size_bytes": 12345678
}
```

Validation:

```txt
filename required
content_type required
size_bytes required
allowed extensions: mp3, wav, flac, m4a, ogg
allowed content types:
  audio/mpeg
  audio/mp3
  audio/wav
  audio/x-wav
  audio/flac
  audio/ogg
  audio/mp4
max size: configurable, default 100 MB
```

Response:

```json
{
  "upload_url": "http://...",
  "method": "PUT",
  "object_key": "temp-audio/{version_id}/input.mp3",
  "expires_in_seconds": 900,
  "headers": {
    "Content-Type": "audio/mpeg"
  }
}
```

Rules:

```txt
version must exist
version status must be draft
object key generated by backend
status becomes upload_url_created
upload session created if using upload_sessions table
```

Important:

The API should not receive the raw audio file.

The frontend uploads directly to MinIO using the signed URL.

---

#### POST /api/versions/{version_id}/upload-complete

Requires auth.

Request:

```json
{
  "object_key": "temp-audio/{version_id}/input.mp3"
}
```

Behavior:

```txt
1. Verify version exists.
2. Verify upload session exists if using upload_sessions.
3. Verify object exists in MinIO.
4. Optionally verify object size/content type metadata.
5. Mark upload session completed.
6. Update track_version status to uploaded.
7. Store temporary_audio_object_key.
```

Response:

```json
{
  "id": "uuid",
  "status": "uploaded",
  "temporary_audio_object_key": "temp-audio/{version_id}/input.mp3"
}
```

Do not emit Kafka event yet unless it is very trivial and does not cause scope creep. Event publishing belongs to Phase 3.

---

## MinIO Requirements

Use MinIO for temporary audio.

Required bucket from Phase 1:

```txt
sounds-right-temp-audio
```

Object key pattern:

```txt
temp-audio/{track_version_id}/input.{ext}
```

The backend must generate object keys. Do not trust user-provided paths.

Signed URL expiry:

```txt
default: 15 minutes
configurable
```

Max file size:

```txt
default: 100 MB
configurable
```

After upload-complete, raw audio remains in temporary bucket until Phase 4 worker deletes it after processing.

Phase 2 does not implement deletion.

---

## Frontend Requirements

Add minimal frontend pages to exercise the flow.

Keep UI simple. This is not Review UI yet.

Suggested pages:

```txt
/
  show app name and API health

/login
/register

/artists
  list artists
  create artist form

/tracks
  list tracks
  create track form

/tracks/:trackId
  track detail
  list versions
  create version button

/versions/:versionId
  version detail
  request upload URL
  upload audio file to MinIO
  call upload-complete
  show status
```

Frontend should use:

```txt
TanStack Query for server state
fetch or generated client if OpenAPI generation already exists
relative API paths through Envoy
```

Do not hardcode:

```txt
http://localhost:8000
http://api:8000
```

Use:

```txt
/api/...
```

Auth token storage:

For Phase 2 simplicity, token can be stored in memory or localStorage.

Document that a more secure refresh/session strategy may come later.

---

## Pydantic Schemas

Create schemas for:

```txt
UserPublic
AuthRegisterRequest
AuthLoginRequest
AuthResponse

ArtistCreate
ArtistUpdate
ArtistPublic
ArtistListResponse

TrackCreate
TrackUpdate
TrackPublic
TrackListResponse

TrackVersionCreate
TrackVersionPublic
UploadUrlRequest
UploadUrlResponse
UploadCompleteRequest
```

Rules:

```txt
Use explicit response schemas.
Do not return raw SQLAlchemy models.
Do not expose password_hash.
Validate content_type and size.
```

---

## Service Layer

Use a light service layer.

Suggested modules:

```txt
sounds_right_api/
  auth/
    routes.py
    service.py
    security.py
    schemas.py

  artists/
    routes.py
    service.py
    schemas.py

  tracks/
    routes.py
    service.py
    schemas.py

  versions/
    routes.py
    service.py
    schemas.py

  storage/
    minio_client.py
    presigned_urls.py

  db/
    models.py
    session.py
```

Avoid overly complex abstractions.

Keep route handlers thin:

```txt
route -> validate schema -> call service -> return schema
```

---

## Error Handling

Create consistent error responses.

Example:

```json
{
  "error": {
    "code": "artist_not_found",
    "message": "Artist not found"
  }
}
```

Minimum error cases:

```txt
400 invalid request
401 unauthorized
403 forbidden
404 not found
409 conflict
422 validation error
500 internal server error
```

Do not return raw exception strings.

---

## Slug Generation

Create utility:

```txt
slugify(value: str) -> str
```

Rules:

```txt
lowercase
trim whitespace
replace spaces with hyphens
remove unsupported punctuation
collapse repeated hyphens
```

Collision handling:

```txt
kendrick-lamar
kendrick-lamar-2
kendrick-lamar-3
```

Use database checks to guarantee uniqueness.

---

## Version Number Generation

Version creation must be safe.

Recommended implementation:

```txt
Start database transaction.
Select current max(version) for track_id.
Create new version = max + 1.
Insert row with unique(track_id, version).
If conflict, retry once or return conflict.
```

Do not infer version numbers from MinIO object paths.

---

## Testing Requirements

Add backend tests for:

```txt
auth register
auth duplicate email
auth login
GET /api/me
create artist
artist slug collision
create track
track slug collision under same artist
create version v1
create version v2
upload-url invalid content type
upload-url too large
upload-complete missing object
```

MinIO integration tests can be basic if testcontainers are too much for this phase.

At minimum, unit-test validation and service logic.

---

## Developer Commands

Update scripts from Phase 1 if needed.

Required commands:

```sh
./scripts/dev.sh
./scripts/down.sh
./scripts/logs.sh
./scripts/migrate.sh
./scripts/lint.sh
./scripts/format.sh
./scripts/check.sh
```

Add if useful:

```sh
./scripts/test.sh
```

`check.sh` should include:

```txt
API lint
worker lint
API tests
frontend typecheck if available
```

---

## README Updates

Update root README with Phase 2 usage.

Add:

```txt
how to register
how to login
how to create artist
how to create track
how to create version
how to upload audio via signed URL
```

Include example curl flow.

Example curl flow:

```sh
# Register
curl -X POST http://localhost:8080/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"test","password":"password123"}'

# Login
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email_or_username":"test","password":"password123"}'

# Create artist
curl -X POST http://localhost:8080/api/artists \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"display_name":"Kendrick Lamar","full_name":"Kendrick Lamar Duckworth"}'
```

Continue curl examples for track/version/upload if practical.

---

## Acceptance Criteria

Phase 2 is complete when:

```txt
1. User can register.
2. User can login.
3. Authenticated user can call /api/me.
4. Passwords are hashed safely.
5. JWT Bearer auth works.
6. Artists can be created/listed/read/updated.
7. Artist slugs are generated and unique.
8. Tracks can be created/listed/read/updated.
9. Track slugs are unique per artist.
10. Track versions can be created with safe incrementing version numbers.
11. Version status starts as draft.
12. API can generate a MinIO presigned upload URL.
13. Upload URL stores expected object key/session metadata.
14. Frontend can upload directly to MinIO using the signed URL.
15. upload-complete verifies the object exists in MinIO.
16. Version status changes to uploaded.
17. API returns consistent error responses.
18. Alembic migrations create all Phase 2 tables.
19. Basic tests cover auth, artists, tracks, versions, and upload validation.
20. No transcription logic exists yet.
21. No Kafka event flow is required yet.
```

---

## Non-Goals

Do not implement:

```txt
transcription.requested event
Kafka producer flow
worker consuming transcription jobs
whisper.cpp
ffmpeg/ffprobe validation
lyrics upload
transcript JSON
review UI
approve/reject
publishing
public karaoke endpoint
Pydantic AI
admin panel
complex RBAC
refresh token rotation unless already easy
```

---

## Suggested Task Order

### Task 1 — Add database models

Create SQLAlchemy models for:

```txt
User
Artist
Track
TrackVersion
UploadSession
```

Generate Alembic migration.

Run migration.

---

### Task 2 — Add auth

Implement:

```txt
password hashing
JWT creation
Bearer parsing
current user dependency
register
login
me
```

---

### Task 3 — Add artist API

Implement:

```txt
create artist
list artists
get artist
update artist
slug generation
slug collision handling
```

---

### Task 4 — Add track API

Implement:

```txt
create track
list tracks
list by artist
get track
update track
track slug uniqueness per artist
```

---

### Task 5 — Add version API

Implement:

```txt
create version
list versions
get version
safe version number generation
```

---

### Task 6 — Add MinIO signed upload URL

Implement:

```txt
validate filename/content type/size
generate object key
create presigned PUT URL
create upload session
update version status to upload_url_created
```

---

### Task 7 — Add upload-complete endpoint

Implement:

```txt
verify object exists in MinIO
mark upload session completed
update version status to uploaded
store object metadata
```

---

### Task 8 — Add frontend flow

Implement minimal pages/forms for:

```txt
register/login
artists
tracks
versions
audio upload
```

Keep UI simple.

---

### Task 9 — Add tests

Add tests for critical backend behavior.

---

### Task 10 — Update docs

Update README and docs with Phase 2 flow.

---

## Final Verification Flow

After Phase 2, this manual flow should work:

```txt
1. Start stack:
   ./scripts/dev.sh

2. Open:
   http://localhost:8080

3. Register a user.

4. Login.

5. Create artist:
   Kendrick Lamar

6. Create track:
   squabble up

7. Create version:
   v1

8. Select local audio file.

9. Frontend asks API for upload URL.

10. Frontend uploads file directly to MinIO.

11. Frontend calls upload-complete.

12. Version page shows:
    status = uploaded
```

API check:

```sh
curl http://localhost:8080/api/health
```

Expected:

```json
{
  "status": "ok"
}
```

---

## Definition of Done

Phase 2 is done when the project has a working core domain backend and minimal UI:

```txt
Auth works.
Artists work.
Tracks work.
Versions work.
Temporary audio upload to MinIO works.
Upload completion updates Postgres state.
The frontend can drive the basic flow through Envoy.
No transcription has been implemented yet.
```

Phase 3 can then add Kafka/Redpanda event publishing and worker consumption.
