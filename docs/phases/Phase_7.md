# Phase 7 — AI Polish / Pydantic AI Enhancements

## Purpose

Add an optional intelligence layer to **Sounds Right** after the core product is already working.

By this phase, the system should already support:

```txt
artists
tracks
track versions
audio upload
Kafka/Redpanda event flow
whisper.cpp transcription
transcript artifact storage in MinIO
review UI
approve/reject flow
publishing approved transcripts
public karaoke JSON/manifest endpoints
```

Phase 7 should make the reviewer experience smarter, faster, and more pleasant by adding AI-assisted quality checks, cleanup suggestions, metadata enrichment, and review notes.

This phase must not make AI the source of truth. AI should assist human review, not silently rewrite or publish transcripts.

---

## Final Phase 7 Goal

At the end of Phase 7, reviewers should be able to:

```txt
1. Open a completed transcript version.
2. Run an AI quality analysis.
3. See likely issues in the transcript.
4. See suggested cleanup actions.
5. See generated review notes.
6. Optionally apply safe suggestions manually.
7. Re-run analysis after edits.
8. Store AI analysis results as auditable artifacts.
```

The system should provide AI-generated assistance, but all meaningful data changes should require explicit reviewer action.

---

## Phase 7 Theme

The principle for this phase:

```txt
AI suggests.
Humans approve.
The system records everything.
```

Do not build a magical black box that modifies transcripts without traceability.

---

## Tech Stack

Continue using the existing stack:

```txt
Frontend:
- Vinext
- React
- TypeScript
- Tailwind
- TanStack Query

Backend:
- Litestar
- Pydantic
- SQLAlchemy
- Alembic
- PostgreSQL
- MinIO
- Kafka/Redpanda

AI Layer:
- Pydantic AI
- provider-agnostic model configuration
```

The exact LLM provider should be configurable.

Examples:

```txt
OpenAI
Anthropic
local OpenAI-compatible model
Ollama/OpenRouter-compatible endpoint if desired later
```

Do not hardcode a single vendor deeply into the domain layer.

---

## Non-Goals

Do not implement these in Phase 7:

```txt
new transcription engine
replacement for whisper.cpp
automatic publishing
silent transcript mutation
complex collaborative editing
full lyrics licensing system
full search engine
recommendation engine
chatbot-first UI
```

This phase is about reviewer assistance and quality analysis only.

---

## Main Features

Implement these features in order.

---

## Feature 1 — AI Quality Analysis

Add an endpoint that analyzes a transcript version and produces a structured quality report.

### Endpoint

```txt
POST /api/versions/{version_id}/ai/analyze
```

Requires:

```txt
authenticated reviewer or admin
version must exist
version must have transcript artifacts
version should be completed, approved, rejected, or published
```

Recommended request:

```json
{
  "analysis_types": [
    "timing_quality",
    "text_quality",
    "segment_quality",
    "metadata_quality"
  ],
  "force_reanalysis": false
}
```

Recommended response:

```json
{
  "analysis_id": "uuid",
  "version_id": "uuid",
  "status": "completed",
  "summary": "Transcript is mostly usable but has several likely timing issues in the chorus.",
  "score": 82,
  "issues": [
    {
      "type": "timing_gap",
      "severity": "medium",
      "segment_id": 12,
      "message": "Large gap between words may indicate missing lyrics or silence.",
      "suggestion": "Review segment 12 timing manually."
    }
  ]
}
```

### Analysis Categories

Support these categories:

```txt
timing_quality
text_quality
segment_quality
metadata_quality
safety_quality
```

#### timing_quality

Detect likely timing issues:

```txt
very long word durations
zero-duration words
overlapping words
large unexplained gaps
segment start after segment end
word outside segment boundaries
segments with too many words
segments with suspiciously long duration
```

This should be mostly deterministic. AI can summarize the findings, but validation should use code.

#### text_quality

Detect likely text issues:

```txt
repeated hallucinated phrases
nonsense words
very low confidence words
weird casing
broken punctuation
empty segment text
text/words mismatch
```

#### segment_quality

Detect readability issues:

```txt
segments that are too long
segments that are too short
segments with awkward line breaks
chorus/repetition inconsistencies
```

#### metadata_quality

Detect metadata problems:

```txt
missing artist
missing title
unknown language
duration mismatch
word count mismatch
schema version mismatch
```

#### safety_quality

Do not censor lyrics, but flag system-level risks:

```txt
transcript unexpectedly empty
transcript contains obvious processing error text
transcript appears unrelated to requested track metadata
AI failed to parse transcript safely
```

---

## Feature 2 — Deterministic Transcript Validator

Before calling AI, build a deterministic validator.

Create module:

```txt
apps/api/src/sounds_right_api/transcripts/validator.py
```

or, if validation belongs closer to artifacts:

```txt
apps/api/src/sounds_right_api/review/validator.py
```

The validator should inspect transcript JSON and return structured findings.

Example finding model:

```python
class TranscriptFinding(BaseModel):
    type: str
    severity: Literal["low", "medium", "high", "critical"]
    segment_id: int | None = None
    word_index: int | None = None
    message: str
    suggestion: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
```

Important:

```txt
Deterministic validation comes first.
AI summarizes and prioritizes.
Do not rely on the LLM to detect every structural issue.
```

---

## Feature 3 — AI Review Notes

Add a feature that generates reviewer-facing notes.

### Endpoint

```txt
POST /api/versions/{version_id}/ai/review-notes
```

Requires:

```txt
authenticated reviewer/admin
existing transcript
```

Response:

```json
{
  "notes_id": "uuid",
  "version_id": "uuid",
  "summary": "This transcript is generally strong. Main review points are chorus timing and several low-confidence words in the second verse.",
  "recommended_actions": [
    "Check chorus segments 18-24 for timing drift.",
    "Review low-confidence words in segment 31.",
    "Confirm whether the intro should remain empty."
  ]
}
```

Store review notes in Postgres and optionally as MinIO artifact.

---

## Feature 4 — Cleanup Suggestions

Add AI-generated suggestions, but do not apply them automatically.

### Endpoint

```txt
POST /api/versions/{version_id}/ai/suggest-cleanup
```

Response:

```json
{
  "suggestion_id": "uuid",
  "version_id": "uuid",
  "suggestions": [
    {
      "id": "uuid",
      "type": "punctuation_cleanup",
      "severity": "low",
      "segment_id": 5,
      "original_text": "i been a go getter from the start",
      "suggested_text": "I been a go-getter from the start",
      "reason": "Improves readability without changing timing."
    }
  ]
}
```

Important rules:

```txt
Suggestions are not automatically applied.
Reviewer must explicitly accept or reject each suggestion.
Accepted suggestions must create an audit record.
Original transcript artifact must remain recoverable.
```

### Optional Apply Endpoint

Only add this if the Review UI already has editing support from Phase 5.

```txt
POST /api/versions/{version_id}/ai/suggestions/{suggestion_id}/apply
POST /api/versions/{version_id}/ai/suggestions/{suggestion_id}/reject
```

If editing support is not ready, store suggestions only and leave apply/reject for a future phase.

---

## Feature 5 — Metadata Enrichment

Add optional metadata enrichment suggestions.

### Endpoint

```txt
POST /api/tracks/{track_id}/ai/enrich-metadata
```

Possible suggestions:

```txt
normalized title casing
artist display name cleanup
album casing cleanup
language guess
genre guess
explicitness flag suggestion
search keywords
```

Important:

```txt
Do not scrape external sites in this phase.
Do not claim metadata is authoritative.
Do not overwrite user-provided metadata automatically.
```

Response:

```json
{
  "track_id": "uuid",
  "suggestions": {
    "normalized_title": "Squabble Up",
    "language": "en",
    "keywords": ["hip-hop", "rap"]
  },
  "confidence": 0.72,
  "notes": "Suggestions are based only on local metadata and transcript text."
}
```

---

## Feature 6 — AI Analysis Artifacts

AI outputs should be stored as artifacts for auditability.

Use Postgres for metadata and MinIO for larger JSON artifacts.

Object layout:

```txt
ai-analysis/
  {artist_slug}/
    {track_slug}/
      v{version}/
        analysis-{analysis_id}.json
        review-notes-{notes_id}.json
        cleanup-suggestions-{suggestion_id}.json
```

Postgres should store:

```txt
analysis id
version id
artifact object key
analysis type
status
model/provider used
created by user id
created at
summary
score
```

Do not store only ephemeral AI output in logs.

---

## Database Changes

Add migrations for these tables.

### ai_analysis_runs

```txt
ai_analysis_runs
- id uuid primary key
- track_version_id uuid not null references track_versions(id)
- status text not null
- analysis_types jsonb not null
- score integer nullable
- summary text nullable
- artifact_object_key text nullable
- provider text nullable
- model_name text nullable
- error_message text nullable
- created_by_user_id uuid nullable references users(id)
- created_at timestamptz not null
- completed_at timestamptz nullable
```

Allowed statuses:

```txt
queued
running
completed
failed
```

Phase 7 can run analysis synchronously at first if transcripts are small enough, but the table should support async later.

---

### ai_findings

```txt
ai_findings
- id uuid primary key
- analysis_run_id uuid not null references ai_analysis_runs(id)
- track_version_id uuid not null references track_versions(id)
- type text not null
- severity text not null
- segment_id integer nullable
- word_index integer nullable
- message text not null
- suggestion text nullable
- metadata_json jsonb nullable
- created_at timestamptz not null
```

Severity values:

```txt
low
medium
high
critical
```

---

### ai_cleanup_suggestions

```txt
ai_cleanup_suggestions
- id uuid primary key
- track_version_id uuid not null references track_versions(id)
- analysis_run_id uuid nullable references ai_analysis_runs(id)
- type text not null
- status text not null
- segment_id integer nullable
- word_index integer nullable
- original_text text nullable
- suggested_text text nullable
- reason text nullable
- metadata_json jsonb nullable
- created_by_user_id uuid nullable references users(id)
- reviewed_by_user_id uuid nullable references users(id)
- created_at timestamptz not null
- reviewed_at timestamptz nullable
```

Status values:

```txt
pending
accepted
rejected
expired
```

---

### ai_review_notes

```txt
ai_review_notes
- id uuid primary key
- track_version_id uuid not null references track_versions(id)
- analysis_run_id uuid nullable references ai_analysis_runs(id)
- summary text not null
- recommended_actions jsonb not null
- artifact_object_key text nullable
- provider text nullable
- model_name text nullable
- created_by_user_id uuid nullable references users(id)
- created_at timestamptz not null
```

---

## API Endpoints

Add these endpoints.

```txt
POST /api/versions/{version_id}/ai/analyze
GET  /api/versions/{version_id}/ai/analysis-runs
GET  /api/ai/analysis-runs/{analysis_id}
GET  /api/ai/analysis-runs/{analysis_id}/findings

POST /api/versions/{version_id}/ai/review-notes
GET  /api/versions/{version_id}/ai/review-notes

POST /api/versions/{version_id}/ai/suggest-cleanup
GET  /api/versions/{version_id}/ai/cleanup-suggestions
POST /api/versions/{version_id}/ai/cleanup-suggestions/{suggestion_id}/accept
POST /api/versions/{version_id}/ai/cleanup-suggestions/{suggestion_id}/reject

POST /api/tracks/{track_id}/ai/enrich-metadata
```

If apply/accept behavior is too risky because transcript editing is not mature, implement reject/accept status only and do not mutate transcript artifacts yet.

---

## Event Design

Phase 7 can work synchronously at first, but event support is recommended.

Add event types:

```txt
ai.analysis.requested
ai.analysis.started
ai.analysis.completed
ai.analysis.failed
ai.suggestion.accepted
ai.suggestion.rejected
ai.review_notes.created
```

Recommended topic:

```txt
sounds-right.events
```

or if topics were split earlier:

```txt
ai.events
```

Do not block Phase 7 on a complex async AI worker unless needed.

Acceptable first implementation:

```txt
API receives analyze request.
API runs deterministic validator.
API calls Pydantic AI.
API stores result.
API emits ai.analysis.completed.
```

Better later implementation:

```txt
API emits ai.analysis.requested.
AI worker consumes event.
AI worker stores artifacts.
Projector updates state.
```

---

## Pydantic AI Integration

Create an AI module.

Suggested structure:

```txt
apps/api/src/sounds_right_api/ai/
  __init__.py
  config.py
  agents.py
  prompts.py
  schemas.py
  service.py
  routes.py
```

Or if using a separate AI worker later:

```txt
apps/ai_worker/src/sounds_right_ai_worker/
```

For Phase 7, keeping AI inside the API is acceptable if simple.

### Required Design Rules

```txt
Use typed inputs and outputs.
Validate all AI responses with Pydantic models.
Store raw-ish structured AI output as artifact.
Never trust free-form model text as database truth.
Keep prompts versioned in code.
Record provider and model name used.
Make AI provider configurable.
```

---

## AI Output Schemas

Create explicit schemas.

### AIQualityAnalysis

```python
class AIQualityAnalysis(BaseModel):
    summary: str
    score: int = Field(ge=0, le=100)
    findings: list[AITranscriptFinding]
    recommended_actions: list[str]
```

### AITranscriptFinding

```python
class AITranscriptFinding(BaseModel):
    type: str
    severity: Literal["low", "medium", "high", "critical"]
    segment_id: int | None = None
    word_index: int | None = None
    message: str
    suggestion: str | None = None
```

### AICleanupSuggestion

```python
class AICleanupSuggestion(BaseModel):
    type: str
    severity: Literal["low", "medium", "high"]
    segment_id: int | None = None
    word_index: int | None = None
    original_text: str | None = None
    suggested_text: str | None = None
    reason: str
```

### AIReviewNotes

```python
class AIReviewNotes(BaseModel):
    summary: str
    recommended_actions: list[str]
    risk_level: Literal["low", "medium", "high"]
```

---

## Prompting Guidelines

Prompts should tell the model:

```txt
You are assisting a human reviewer.
Do not claim certainty when uncertain.
Do not rewrite lyrics aggressively.
Do not censor lyrics.
Do not invent missing lyrics.
Only suggest changes that preserve meaning.
Prefer flagging issues over silently fixing them.
Return only the requested structured output.
```

Important:

```txt
The model should not hallucinate song metadata.
The model should not claim it listened to audio.
The model only sees transcript JSON and metadata unless explicitly provided otherwise.
```

---

## Frontend Requirements

Update the Review UI from Phase 5.

Add AI panel to version/review page.

### AI Review Panel

Show:

```txt
Run AI analysis button
latest analysis score
summary
findings grouped by severity
recommended actions
cleanup suggestions
review notes
model/provider used
analysis timestamp
```

### Findings UI

Group findings:

```txt
Critical
High
Medium
Low
```

Each finding should show:

```txt
type
severity
segment id
message
suggestion
jump-to-segment button if possible
```

### Cleanup Suggestions UI

Each suggestion should show:

```txt
original text
suggested text
reason
accept button
reject button
```

If applying suggestions is not implemented safely yet, show:

```txt
Mark accepted
Mark rejected
```

without mutating transcript artifacts.

---

## Safety and Guardrails

Follow these rules:

```txt
AI must not automatically publish.
AI must not automatically approve.
AI must not silently mutate transcript JSON.
AI suggestions must be auditable.
AI output must be schema-validated.
AI output must be stored with provider/model metadata.
Reviewer actions must be recorded.
```

If AI output fails validation:

```txt
mark run as failed
store safe error message
return controlled API error
```

Do not expose raw provider exceptions to the user.

---

## Configuration

Add config values:

```env
AI_ENABLED=true
AI_PROVIDER=openai
AI_MODEL=gpt-4.1-mini
AI_API_KEY=replace_me
AI_MAX_TRANSCRIPT_CHARS=120000
AI_STORE_ARTIFACTS=true
AI_ANALYSIS_SYNC=true
```

Provider-specific keys should be optional depending on provider.

Do not require AI config for normal app boot if `AI_ENABLED=false`.

---

## Transcript Size Handling

Large transcripts may exceed model context.

Implement a safe strategy:

```txt
1. Load manifest/transcript metadata.
2. If transcript is small, analyze whole transcript.
3. If transcript is large, chunk by segment ranges.
4. Run per-chunk analysis.
5. Merge findings.
6. Generate final summary from merged findings.
```

Initial limit:

```txt
AI_MAX_TRANSCRIPT_CHARS=120000
```

If transcript exceeds this, either:

```txt
chunk it
or return controlled error saying transcript is too large for current AI analysis
```

Chunking is preferred if not too complex.

---

## Artifact Format

AI analysis artifact example:

```json
{
  "schema_version": "1.0",
  "analysis_id": "uuid",
  "track_version_id": "uuid",
  "provider": "openai",
  "model": "gpt-4.1-mini",
  "created_at": "2026-07-04T12:00:00Z",
  "summary": "Transcript is generally usable but chorus timing needs review.",
  "score": 82,
  "deterministic_findings": [],
  "ai_findings": [],
  "recommended_actions": []
}
```

Store it in MinIO under:

```txt
ai-analysis/{artist_slug}/{track_slug}/v{version}/analysis-{analysis_id}.json
```

---

## Testing Requirements

Add tests for:

```txt
transcript validator detects overlapping words
transcript validator detects zero-duration words
transcript validator detects word outside segment range
AI disabled returns controlled error
AI analysis creates analysis run
AI analysis stores findings
AI analysis stores artifact object key
invalid AI output is handled safely
review notes endpoint works
cleanup suggestions endpoint works
accept suggestion changes status
reject suggestion changes status
non-reviewer cannot run AI analysis if restricted
```

Use fake/mock AI provider in tests.

Do not call real AI providers in automated tests.

---

## Suggested Task Order

### Task 1 — Add AI database tables

Create migrations for:

```txt
ai_analysis_runs
ai_findings
ai_cleanup_suggestions
ai_review_notes
```

---

### Task 2 — Add deterministic transcript validator

Implement validation for:

```txt
overlapping words
zero-duration words
word outside segment
invalid segment range
empty transcript
very long segments
```

---

### Task 3 — Add AI config

Add typed config for:

```txt
AI_ENABLED
AI_PROVIDER
AI_MODEL
AI_API_KEY
AI_MAX_TRANSCRIPT_CHARS
AI_STORE_ARTIFACTS
```

App should boot if AI is disabled.

---

### Task 4 — Add Pydantic AI service

Create typed AI service with fake provider support for tests.

Implement:

```txt
analyze_transcript
create_review_notes
suggest_cleanup
enrich_metadata
```

---

### Task 5 — Add AI routes

Implement endpoints under:

```txt
/api/versions/{version_id}/ai/...
/api/tracks/{track_id}/ai/...
```

---

### Task 6 — Store AI artifacts

Upload analysis JSON to MinIO.

Store artifact object key in Postgres.

---

### Task 7 — Add frontend AI panel

Update review page with:

```txt
run analysis
findings list
score
summary
cleanup suggestions
review notes
```

---

### Task 8 — Add tests

Add validator, service, route, and UI smoke tests if available.

---

### Task 9 — Update docs

Update README and docs with AI feature usage.

---

## API Examples

### Run AI analysis

```sh
curl -X POST http://localhost:8080/api/versions/$VERSION_ID/ai/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_types": ["timing_quality", "text_quality", "segment_quality"],
    "force_reanalysis": false
  }'
```

### Get findings

```sh
curl http://localhost:8080/api/ai/analysis-runs/$ANALYSIS_ID/findings \
  -H "Authorization: Bearer $TOKEN"
```

### Generate review notes

```sh
curl -X POST http://localhost:8080/api/versions/$VERSION_ID/ai/review-notes \
  -H "Authorization: Bearer $TOKEN"
```

---

## Acceptance Criteria

Phase 7 is complete when:

```txt
1. AI config exists and app boots with AI enabled or disabled.
2. Deterministic transcript validator works.
3. AI analysis endpoint exists.
4. AI analysis stores run metadata in Postgres.
5. AI analysis stores findings in Postgres.
6. AI analysis stores structured artifact in MinIO.
7. AI review notes can be generated and stored.
8. AI cleanup suggestions can be generated and stored.
9. Cleanup suggestions can be accepted/rejected as auditable reviewer actions.
10. Metadata enrichment suggestions can be generated without overwriting metadata.
11. Frontend review page shows AI analysis panel.
12. Frontend can trigger analysis and display findings.
13. AI output is schema-validated.
14. Invalid AI output fails safely.
15. No AI feature auto-approves, auto-publishes, or silently mutates transcripts.
16. Tests use fake/mock AI provider, not real paid model calls.
17. README/docs explain how to configure and use AI features.
```

---

## Definition of Done

Phase 7 is done when **Sounds Right** has a useful AI-assisted review layer:

```txt
Reviewers can run AI analysis.
The system highlights likely transcript issues.
The system suggests cleanup actions.
The system generates review notes.
AI results are stored and auditable.
Humans remain in control.
Published transcript data is never silently changed by AI.
```

After this phase, the core rewrite is feature-complete enough to become a polished portfolio project or a real internal tool.
