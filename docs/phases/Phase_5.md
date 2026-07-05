# Phase 5 — Review UI

## Purpose

Build the first useful product-facing interface for **Sounds Right**.

By the end of Phase 4, the system should already support this backend flow:

```txt
uploaded audio
  -> transcription.requested event
  -> worker consumes event
  -> whisper.cpp transcribes
  -> transcript artifacts saved to MinIO
  -> transcription.completed / transcription.failed event emitted
  -> Postgres job/version state updated
```

Phase 5 adds the reviewer-facing UI and API polish needed to inspect generated transcripts, preview karaoke timing, and approve or reject a completed transcription.

This phase should make the app feel like a real workflow tool, not only an infra demo.

---

## Final Phase 5 Goal

At the end of Phase 5, a reviewer/admin should be able to:

```txt
1. Open the dashboard through Envoy.
2. See tracks, versions, and transcription jobs.
3. Open a completed transcription version.
4. View transcript metadata.
5. View segments and word-level timestamps.
6. Preview the karaoke timing in a simple player-like UI.
7. Approve the completed version.
8. Reject the completed version with a reason.
9. See status changes reflected in the UI.
```

The system should not publish public karaoke endpoints yet. Publishing belongs to Phase 6.

---

## Existing Assumptions

Assume previous phases already provide:

```txt
Phase 1:
- monorepo
- Envoy
- Vinext frontend shell
- Litestar API
- Postgres
- Alembic
- MinIO
- Redpanda
- worker shell

Phase 2:
- auth
- users
- artists
- tracks
- track versions
- signed upload URL flow
- upload-complete flow

Phase 3:
- Kafka/Redpanda event publishing
- transcription.requested flow
- worker event consumption
- job state projection

Phase 4:
- whisper.cpp worker
- ffprobe validation
- transcript JSON generation
- MinIO transcript artifacts
- raw audio cleanup
- completed/failed job events
```

Do not rebuild previous phases. Extend them.

---

## Tech Stack

Continue using:

```txt
Frontend:
- Vinext
- React
- TypeScript
- Tailwind CSS
- TanStack Query
- Zod

Backend:
- Litestar
- Pydantic
- SQLAlchemy async
- Alembic
- PostgreSQL
- MinIO client

Events:
- Redpanda/Kafka already exists

Ingress:
- Envoy
```

Do not introduce:

```txt
Next.js
Vercel-specific assumptions
FastAPI
Flask
MongoDB
Celery
RabbitMQ
large frontend state framework unless clearly needed
Pydantic AI yet
```

---

## Scope

Phase 5 includes:

```txt
reviewer dashboard
track/version browsing improvements
job status UI
transcript artifact loading
transcript segment viewer
basic karaoke preview
approve version endpoint
reject version endpoint
review status history
minimal role checks for reviewer/admin actions
frontend UI polish enough to be usable
```

Phase 5 does not include:

```txt
public publishing
public karaoke JSON endpoint
production object promotion
advanced transcript editor
word-level correction editor
Pydantic AI quality review
collaborative editing
WebSockets
full admin panel
payments/user subscriptions
```

---

## New Concepts Introduced In Phase 5

Phase 5 introduces the **review workflow**.

A transcription can now move from:

```txt
completed
  -> pending_review
  -> approved
  -> rejected
```

Recommended behavior:

```txt
When transcription completes:
- track_version.status becomes completed

When reviewer opens it:
- no automatic status change is required

When reviewer approves:
- track_version.status becomes approved
- approved_at is set
- approved_by_user_id is set
- review event is recorded

When reviewer rejects:
- track_version.status becomes rejected
- rejected_at is set if column exists
- rejected_by_user_id is set if column exists
- rejection reason is recorded
- review event is recorded
```

If `pending_review` was already modeled earlier, use it. Otherwise, Phase 5 may keep the simpler state flow:

```txt
completed -> approved
completed -> rejected
```

Do not implement publishing yet.

---

## Database Changes

Add review-related fields to `track_versions` if they do not exist yet.

Recommended columns:

```txt
track_versions
- approved_at timestamptz nullable
- approved_by_user_id uuid nullable references users(id)
- rejected_at timestamptz nullable
- rejected_by_user_id uuid nullable references users(id)
- rejection_reason text nullable
```

If `approved_at` and `approved_by_user_id` already exist from earlier planning, only add missing rejection fields.

---

## New Table: review_events

Create a dedicated review event table.

```txt
review_events
- id uuid primary key
- track_version_id uuid not null references track_versions(id)
- reviewer_user_id uuid not null references users(id)
- action text not null
- reason text nullable
- metadata_json jsonb nullable
- created_at timestamptz not null
```

Allowed actions:

```txt
approved
rejected
commented
```

Only `approved` and `rejected` are required in Phase 5.

Reasoning:

```txt
job_events are for worker/job lifecycle
review_events are for human review lifecycle
```

Keep them separate.

---

## Status Rules

Allowed Phase 5 transitions:

```txt
completed -> approved
completed -> rejected
approved  -> rejected   optional, admin only if implemented
rejected  -> approved   optional, admin only if implemented
```

Recommended simplest rule:

```txt
Only completed versions can be approved or rejected.
Approved/rejected versions are final until a later admin override feature exists.
```

Reject invalid transitions with:

```txt
409 Conflict
```

Example invalid transitions:

```txt
Cannot approve draft version.
Cannot approve processing version.
Cannot approve failed version.
Cannot approve already approved version.
Cannot reject already rejected version.
```

---

## API Requirements

All API routes must stay under `/api`.

---

## Review Endpoints

Add these endpoints:

```txt
GET  /api/review/queue
GET  /api/versions/{version_id}/transcript
GET  /api/versions/{version_id}/review-events
POST /api/versions/{version_id}/approve
POST /api/versions/{version_id}/reject
```

---

### GET /api/review/queue

Requires auth.

Recommended role:

```txt
reviewer or admin
```

For Phase 5, if role management is still minimal, authenticated users may access it temporarily, but document the limitation.

Query params:

```txt
status=completed
limit=20
offset=0
```

Useful statuses:

```txt
completed
approved
rejected
failed
```

Response:

```json
{
  "items": [
    {
      "version_id": "uuid",
      "track_id": "uuid",
      "artist": {
        "id": "uuid",
        "display_name": "Kendrick Lamar",
        "slug": "kendrick-lamar"
      },
      "track": {
        "id": "uuid",
        "title": "squabble up",
        "slug": "squabble-up",
        "album": "GNX"
      },
      "version": 1,
      "status": "completed",
      "job": {
        "id": "uuid",
        "status": "completed",
        "completed_at": "2026-07-03T12:00:00Z"
      },
      "summary": {
        "duration_seconds": 213.42,
        "word_count": 512,
        "engine": "whisper.cpp"
      },
      "created_at": "2026-07-03T11:55:00Z",
      "updated_at": "2026-07-03T12:00:00Z"
    }
  ],
  "limit": 20,
  "offset": 0,
  "total": 1
}
```

---

### GET /api/versions/{version_id}/transcript

Requires auth.

Returns transcript JSON loaded from MinIO.

Rules:

```txt
version must exist
version must have transcript_object_key
object must exist in MinIO
response should be validated or normalized with Pydantic before returning if practical
```

Response example:

```json
{
  "schema_version": "1.0",
  "track": {
    "artist": "Kendrick Lamar",
    "album": "GNX",
    "title": "squabble up",
    "version": 1
  },
  "engine": {
    "name": "whisper.cpp",
    "model": "base",
    "language": "en"
  },
  "metadata": {
    "duration_seconds": 213.42,
    "created_at": "2026-07-03T12:00:00Z",
    "word_count": 512
  },
  "segments": []
}
```

Important:

```txt
Do not store the transcript directly in Postgres.
Do not expose raw MinIO credentials.
Do not expose internal MinIO object URLs unless intentionally presigned.
```

---

### GET /api/versions/{version_id}/review-events

Requires auth.

Returns review event history.

Response:

```json
{
  "items": [
    {
      "id": "uuid",
      "action": "approved",
      "reason": null,
      "reviewer": {
        "id": "uuid",
        "username": "oskar"
      },
      "created_at": "2026-07-03T12:10:00Z"
    }
  ]
}
```

---

### POST /api/versions/{version_id}/approve

Requires auth.

Recommended role:

```txt
reviewer or admin
```

Request:

```json
{}
```

Optional request:

```json
{
  "note": "Timing looks good enough for first release."
}
```

Behavior:

```txt
1. Load version.
2. Ensure status is completed.
3. Ensure transcript artifact exists in MinIO.
4. Set status to approved.
5. Set approved_at.
6. Set approved_by_user_id.
7. Create review_events row with action approved.
8. Return updated version.
```

Response:

```json
{
  "id": "uuid",
  "track_id": "uuid",
  "version": 1,
  "status": "approved",
  "approved_at": "2026-07-03T12:10:00Z",
  "approved_by_user_id": "uuid"
}
```

Do not move files to production storage yet. That belongs to Phase 6.

---

### POST /api/versions/{version_id}/reject

Requires auth.

Recommended role:

```txt
reviewer or admin
```

Request:

```json
{
  "reason": "Word timestamps drift after the second chorus."
}
```

Rules:

```txt
reason required
reason max length: 2000 characters
version status must be completed
```

Behavior:

```txt
1. Load version.
2. Ensure status is completed.
3. Set status to rejected.
4. Set rejected_at.
5. Set rejected_by_user_id.
6. Set rejection_reason.
7. Create review_events row with action rejected.
8. Return updated version.
```

Response:

```json
{
  "id": "uuid",
  "track_id": "uuid",
  "version": 1,
  "status": "rejected",
  "rejection_reason": "Word timestamps drift after the second chorus."
}
```

---

## Optional Event Publishing

Review actions may emit Kafka events if the Phase 3 event system is already clean.

Optional events:

```txt
transcription.approved
transcription.rejected
```

If implemented, use the existing event envelope.

Example:

```json
{
  "event_id": "uuid",
  "event_type": "transcription.approved",
  "occurred_at": "2026-07-03T12:10:00Z",
  "correlation_id": "uuid",
  "payload": {
    "track_version_id": "uuid",
    "reviewer_user_id": "uuid"
  }
}
```

Do not let optional event publishing block Phase 5 completion. Database state and UI are the priority.

---

## Transcript Data Handling

The transcript is stored in MinIO as JSON.

Phase 5 should load it through the API:

```txt
frontend -> /api/versions/{version_id}/transcript -> API loads MinIO object -> frontend receives JSON
```

Do not have the frontend fetch directly from MinIO in Phase 5.

Reasoning:

```txt
- API can enforce auth
- API can hide object keys
- API can validate schema
- API can later apply access rules
```

---

## Transcript Schema Types

Create shared TypeScript types or frontend-local types for now.

Recommended frontend types:

```ts
export type TranscriptWord = {
  word: string;
  start: number;
  end: number;
  confidence?: number | null;
};

export type TranscriptSegment = {
  id: number | string;
  start: number;
  end: number;
  text: string;
  words: TranscriptWord[];
};

export type TranscriptDocument = {
  schema_version: string;
  track: {
    artist: string;
    album?: string | null;
    title: string;
    version: number;
  };
  engine: {
    name: string;
    model?: string | null;
    language?: string | null;
  };
  metadata: {
    duration_seconds?: number | null;
    created_at?: string | null;
    word_count?: number | null;
  };
  segments: TranscriptSegment[];
};
```

Eventually these should come from `packages/contracts`, but do not overcomplicate Phase 5 if OpenAPI/type generation is not ready.

---

## Frontend Pages

Add or improve these pages.

---

### `/review`

Review dashboard.

Shows queue of versions.

Required UI:

```txt
filters by status
list/table of versions
artist name
title
version number
status
created/completed date
word count/duration if available
open review button
```

Recommended filters:

```txt
Completed
Approved
Rejected
Failed
```

Default filter:

```txt
completed
```

---

### `/versions/:versionId/review`

Review detail page.

Required sections:

```txt
header with artist/title/version/status
job/transcription summary
transcript metadata
karaoke preview
segment list
review actions
review history
```

Actions:

```txt
Approve
Reject
```

Reject should open a small modal/form requiring a reason.

---

### `/jobs/:jobId`

Improve existing job status page if it exists.

Show:

```txt
job status
progress
started_at
completed_at
error message if failed
events/timeline if available
link to review page if completed
```

---

## Basic Karaoke Preview

Implement a simple transcript preview component.

Name suggestion:

```txt
KaraokePreview
```

Inputs:

```txt
transcript document
current time
```

Since raw audio is deleted after processing, Phase 5 does not need audio playback.

Build a simulated preview:

```txt
play button
pause button
reset button
time slider
current timestamp
highlight current segment
highlight current word
```

Behavior:

```txt
Click play -> local timer starts from 0
As time increases -> active segment/word highlights
Slider lets reviewer scrub through transcript
```

This is enough to validate timing visually without keeping raw audio.

Optional if an audio preview artifact exists later:

```txt
Use real audio playback
```

But do not reintroduce permanent raw audio storage just for this phase.

---

## Segment Viewer

Implement a component:

```txt
TranscriptSegmentList
```

Required behavior:

```txt
list all segments
show start/end times
show segment text
show words with start/end timestamps
click segment -> seek preview to segment.start
active segment highlighted
```

Useful display format:

```txt
[00:12.340 - 00:15.800] Segment text here
word 00:12.340-00:12.700
word 00:12.700-00:13.100
```

Do not implement editing yet.

---

## Review Actions UI

Implement component:

```txt
ReviewActions
```

Behavior:

```txt
If status completed:
  show Approve button
  show Reject button

If status approved:
  show approved state
  hide destructive actions

If status rejected:
  show rejected state and reason
  hide actions

If status failed/draft/processing/uploaded:
  show message that version is not reviewable
```

Approve flow:

```txt
click approve
show confirm dialog
call POST /api/versions/{version_id}/approve
invalidate queries
show success state
```

Reject flow:

```txt
click reject
show modal with textarea
require reason
call POST /api/versions/{version_id}/reject
invalidate queries
show rejected state
```

---

## Frontend State Management

Use TanStack Query.

Recommended query keys:

```ts
['review-queue', status, limit, offset]
['version', versionId]
['version-transcript', versionId]
['version-review-events', versionId]
['job', jobId]
```

Mutations:

```ts
approveVersion(versionId)
rejectVersion(versionId, reason)
```

After mutation success, invalidate:

```txt
review queue
version detail
review events
```

---

## API Client

If an OpenAPI-generated client exists, use it.

If not, create a small frontend API wrapper:

```txt
apps/web/src/lib/api/client.ts
```

Rules:

```txt
Use relative URLs like /api/...
Attach Bearer token if available
Handle 401 globally enough for Phase 5
Return typed results
```

Do not hardcode service URLs.

---

## Access Control

Minimum backend access control:

```txt
GET review queue: authenticated
GET transcript: authenticated
approve: reviewer/admin preferred
reject: reviewer/admin preferred
```

If role management is already available:

```txt
Only reviewer/admin can approve/reject.
```

If not:

```txt
Allow authenticated users temporarily and add TODO clearly.
```

Do not leave approval endpoints completely public.

---

## Error Handling

Use consistent API error responses.

Important error cases:

```txt
404 version not found
404 transcript artifact not found
409 invalid status transition
401 unauthenticated
403 not allowed
400 missing rejection reason
500 MinIO read error
```

Examples:

```json
{
  "error": {
    "code": "version_not_reviewable",
    "message": "Only completed versions can be approved."
  }
}
```

---

## UX Requirements

Keep the UI simple but useful.

Use clear states:

```txt
loading
empty
error
success
failed job
not reviewable
approved
rejected
```

Review queue empty state:

```txt
No completed transcriptions waiting for review.
```

Transcript missing state:

```txt
Transcript artifact is missing or unavailable.
```

Failed job state:

```txt
This transcription failed and cannot be reviewed.
```

---

## Testing Requirements

Backend tests:

```txt
approve completed version
reject completed version with reason
cannot approve draft version
cannot reject processing version
cannot approve missing version
cannot reject without reason
review event created on approve
review event created on reject
transcript endpoint loads MinIO object
transcript endpoint returns 404 when object missing
review queue lists completed versions
```

Frontend tests are optional if the project does not have the setup yet.

If practical, add component tests for:

```txt
KaraokePreview active word selection
ReviewActions visible states
TranscriptSegmentList segment click
```

---

## Suggested Backend Modules

Recommended structure:

```txt
apps/api/src/sounds_right_api/
  review/
    routes.py
    service.py
    schemas.py

  transcripts/
    routes.py
    service.py
    schemas.py

  versions/
    service.py
    schemas.py

  storage/
    minio_client.py
```

Keep route handlers thin:

```txt
route -> auth dependency -> service -> response schema
```

---

## Suggested Frontend Components

Recommended structure:

```txt
apps/web/src/features/review/
  pages/
    ReviewQueuePage.tsx
    VersionReviewPage.tsx

  components/
    ReviewQueueTable.tsx
    ReviewStatusBadge.tsx
    ReviewActions.tsx
    RejectDialog.tsx
    ReviewEventTimeline.tsx

apps/web/src/features/transcript/
  components/
    KaraokePreview.tsx
    TranscriptSegmentList.tsx
    TranscriptMetadataCard.tsx
    Timestamp.tsx

apps/web/src/lib/api/
  review.ts
  transcripts.ts
```

Keep components small and readable.

---

## Timestamp Formatting

Implement small helper:

```ts
formatTimestamp(seconds: number): string
```

Example:

```txt
0       -> 00:00.000
12.34   -> 00:12.340
75.2    -> 01:15.200
```

Use it consistently in preview and segment list.

---

## README Updates

Update README with:

```txt
how to open review dashboard
how to review a completed transcription
how to approve
how to reject
known limitations of Phase 5
```

Mention that:

```txt
Publishing is not implemented yet.
Transcript editing is not implemented yet.
Audio playback is simulated unless preview audio artifacts exist.
```

---

## Acceptance Criteria

Phase 5 is complete when:

```txt
1. Review queue page exists.
2. Review queue lists completed versions.
3. Version review page exists.
4. Version review page loads transcript JSON from API.
5. API loads transcript JSON from MinIO.
6. Transcript metadata is visible.
7. Segment list is visible.
8. Word timestamps are visible.
9. Basic karaoke preview works with simulated playback.
10. Active segment/word highlighting works.
11. Completed version can be approved.
12. Completed version can be rejected with reason.
13. Invalid status transitions return 409.
14. Review events are stored in Postgres.
15. Review event timeline is visible in UI.
16. Approved/rejected status updates are reflected in UI.
17. Approval endpoints require authentication.
18. Tests cover approval/rejection backend behavior.
19. No publishing flow is implemented yet.
20. No transcript editing is implemented yet.
```

---

## Non-Goals

Do not implement these in Phase 5:

```txt
public transcript publishing
moving artifacts to production bucket
public karaoke endpoint
advanced transcript editor
word timestamp correction
lyrics correction
Pydantic AI review assistant
collaborative review
WebSockets
permanent raw audio storage
real audio playback requiring raw uploaded audio
```

---

## Suggested Task Order

### Task 1 — Add review database migration

Add:

```txt
review_events table
missing approval/rejection columns on track_versions
```

Run migration.

---

### Task 2 — Add review service

Implement:

```txt
get review queue
approve version
reject version
get review events
```

Enforce status transitions.

---

### Task 3 — Add transcript API

Implement:

```txt
GET /api/versions/{version_id}/transcript
```

Load transcript JSON from MinIO.

---

### Task 4 — Add review API routes

Implement:

```txt
GET /api/review/queue
GET /api/versions/{version_id}/review-events
POST /api/versions/{version_id}/approve
POST /api/versions/{version_id}/reject
```

---

### Task 5 — Add frontend review queue

Implement:

```txt
/review
ReviewQueueTable
status filters
open review links
```

---

### Task 6 — Add transcript viewer

Implement:

```txt
VersionReviewPage
TranscriptMetadataCard
TranscriptSegmentList
```

---

### Task 7 — Add karaoke preview

Implement:

```txt
KaraokePreview
play/pause/reset
slider
active word/segment highlighting
```

---

### Task 8 — Add approve/reject UI

Implement:

```txt
ReviewActions
RejectDialog
mutation handling
query invalidation
```

---

### Task 9 — Add review timeline

Implement:

```txt
ReviewEventTimeline
```

Show approve/reject history.

---

### Task 10 — Add tests and docs

Add backend tests and update README.

---

## Final Manual Verification Flow

Use a completed transcription from Phase 4.

Steps:

```txt
1. Start stack:
   ./scripts/dev.sh

2. Open:
   http://localhost:8080

3. Log in.

4. Upload and process a track using previous phase flow.

5. Wait until version status is completed.

6. Open:
   http://localhost:8080/review

7. Click completed version.

8. Verify transcript loads.

9. Use preview play button.

10. Click a segment and verify preview seeks.

11. Approve the version.

12. Verify status becomes approved.

13. Repeat with another completed version and reject it with reason.

14. Verify review event timeline updates.
```

API verification:

```sh
curl http://localhost:8080/api/review/queue \
  -H "Authorization: Bearer $TOKEN"
```

Approve verification:

```sh
curl -X POST http://localhost:8080/api/versions/$VERSION_ID/approve \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

Reject verification:

```sh
curl -X POST http://localhost:8080/api/versions/$VERSION_ID/reject \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"reason":"Timing drifts after the chorus."}'
```

---

## Definition of Done

Phase 5 is done when the app has a usable review workflow:

```txt
Reviewer can find completed transcriptions.
Reviewer can inspect transcript JSON visually.
Reviewer can preview timing with simulated karaoke playback.
Reviewer can approve a completed version.
Reviewer can reject a completed version with a reason.
Review actions are persisted.
Status changes are reflected in UI.
Publishing is still left for Phase 6.
```
