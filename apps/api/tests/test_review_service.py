from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest

from sounds_right_api.models import TrackVersion, User
from sounds_right_api.services import review


class FakeSession:
    def __init__(self, version: TrackVersion | None) -> None:
        self.version = version
        self.added: list[Any] = []
        self.committed = False

    async def get(self, _model: object, _id: uuid.UUID, **_kwargs: object) -> TrackVersion | None:
        return self.version

    def add(self, value: Any) -> None:
        self.added.append(value)

    async def commit(self) -> None:
        self.committed = True

    async def refresh(self, _value: object) -> None:
        return None


def make_user(role: str = "reviewer") -> User:
    return User(
        id=uuid.uuid4(),
        email="reviewer@example.com",
        username="reviewer",
        password_hash="hash",
        role=role,
        is_active=True,
    )


def make_version(status: str = "completed") -> TrackVersion:
    now = datetime.now(UTC)
    return TrackVersion(
        id=uuid.uuid4(),
        track_id=uuid.uuid4(),
        version=1,
        status=status,
        transcript_object_key="transcripts/version/transcript.json",
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_approve_completed_version_creates_review_event(monkeypatch: pytest.MonkeyPatch) -> None:
    async def transcript_exists(_version: TrackVersion, _settings: object) -> None:
        return None

    monkeypatch.setattr(review, "_ensure_transcript_exists", transcript_exists)
    version = make_version()
    session = FakeSession(version)
    user = make_user()

    result = await review.approve_version(session, version.id, user, "Looks good", object())  # type: ignore[arg-type]

    assert result.status == "approved"
    assert version.approved_by_user_id == user.id
    assert version.approved_at is not None
    assert session.committed is True
    assert session.added[0].action == "approved"
    assert session.added[0].reason == "Looks good"


@pytest.mark.asyncio
async def test_reject_completed_version_creates_review_event() -> None:
    version = make_version()
    session = FakeSession(version)
    user = make_user()

    result = await review.reject_version(session, version.id, user, "Timing drifts")

    assert result.status == "rejected"
    assert result.rejection_reason == "Timing drifts"
    assert version.rejected_by_user_id == user.id
    assert session.committed is True
    assert session.added[0].action == "rejected"
    assert session.added[0].reason == "Timing drifts"


@pytest.mark.asyncio
async def test_cannot_approve_draft_version(monkeypatch: pytest.MonkeyPatch) -> None:
    async def transcript_exists(_version: TrackVersion, _settings: object) -> None:
        return None

    monkeypatch.setattr(review, "_ensure_transcript_exists", transcript_exists)
    version = make_version(status="draft")
    session = FakeSession(version)

    with pytest.raises(review.VersionNotReviewableError):
        await review.approve_version(session, version.id, make_user(), None, object())  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_cannot_reject_processing_version() -> None:
    version = make_version(status="processing")
    session = FakeSession(version)

    with pytest.raises(review.VersionNotReviewableError):
        await review.reject_version(session, version.id, make_user(), "Still running")


@pytest.mark.asyncio
async def test_approve_requires_reviewer_role(monkeypatch: pytest.MonkeyPatch) -> None:
    async def transcript_exists(_version: TrackVersion, _settings: object) -> None:
        return None

    monkeypatch.setattr(review, "_ensure_transcript_exists", transcript_exists)
    version = make_version()
    session = FakeSession(version)

    with pytest.raises(review.ForbiddenReviewActionError):
        await review.approve_version(session, version.id, make_user(role="user"), None, object())  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_get_transcript_loads_minio_object(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        def read(self) -> bytes:
            return json.dumps(
                {
                    "schema_version": "1.0",
                    "track_version_id": str(uuid.uuid4()),
                    "job_id": str(uuid.uuid4()),
                    "engine": {"name": "whisper.cpp", "model": "base", "language": "en"},
                    "metadata": {"duration_seconds": 12.5, "word_count": 2, "segment_count": 1},
                    "text": "hello world",
                    "segments": [
                        {
                            "id": 1,
                            "start": 0,
                            "end": 1.2,
                            "text": "hello world",
                            "words": [
                                {"word": "hello", "start": 0, "end": 0.5},
                                {"word": "world", "start": 0.5, "end": 1.2},
                            ],
                        },
                    ],
                },
            ).encode()

        def close(self) -> None:
            return None

        def release_conn(self) -> None:
            return None

    class FakeClient:
        def get_object(self, _bucket: str, _key: str) -> FakeResponse:
            return FakeResponse()

    monkeypatch.setattr(review, "create_minio_client", lambda _settings: FakeClient())
    version = make_version()
    session = FakeSession(version)
    settings = SimpleNamespace(minio_transcripts_bucket="transcripts")

    transcript = await review.get_transcript(session, version.id, settings)  # type: ignore[arg-type]

    assert transcript.schema_version == "1.0"
    assert transcript.engine.name == "whisper.cpp"
    assert transcript.segments[0].words[1].word == "world"
