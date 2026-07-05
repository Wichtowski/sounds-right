from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest

from sounds_right_api.domain.schemas import TranscriptDocument
from sounds_right_api.models import Artist, Publication, Track, TrackVersion, User
from sounds_right_api.services import publications
from sounds_right_api.services.publications import service


class FakeScalarResult:
    def __init__(self, items: list[Any]) -> None:
        self.items = items

    def all(self) -> list[Any]:
        return self.items


class FakeSession:
    def __init__(self, version: TrackVersion) -> None:
        self.version = version
        self.scalar_calls = 0
        self.added: list[Any] = []
        self.committed = False

    async def scalar(self, _statement: object) -> Any:
        self.scalar_calls += 1
        if self.scalar_calls == 1:
            return self.version
        return None

    async def scalars(self, _statement: object) -> FakeScalarResult:
        return FakeScalarResult([])

    def add(self, value: Any) -> None:
        self.added.append(value)

    async def commit(self) -> None:
        self.committed = True

    async def refresh(self, value: object) -> None:
        if isinstance(value, Publication):
            now = datetime.now(UTC)
            value.created_at = now
            value.updated_at = now


class FakeResponse:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def read(self) -> bytes:
        return self.body

    def close(self) -> None:
        return None

    def release_conn(self) -> None:
        return None


class FakeMinioClient:
    def __init__(self, transcript: dict[str, Any]) -> None:
        self.transcript = transcript
        self.objects: dict[str, bytes] = {}

    def get_object(self, _bucket: str, _key: str) -> FakeResponse:
        return FakeResponse(json.dumps(self.transcript).encode("utf-8"))

    def put_object(
        self,
        _bucket: str,
        object_key: str,
        data: Any,
        length: int,
        content_type: str,
    ) -> None:
        assert content_type == "application/json"
        self.objects[object_key] = data.read(length)


def make_user(role: str = "reviewer") -> User:
    return User(
        id=uuid.uuid4(),
        email="reviewer@example.com",
        username="reviewer",
        password_hash="hash",
        role=role,
        is_active=True,
    )


def make_version(status: str = "approved") -> TrackVersion:
    artist = Artist(
        id=uuid.uuid4(),
        slug="kendrick-lamar",
        display_name="Kendrick Lamar",
    )
    track = Track(
        id=uuid.uuid4(),
        artist_id=artist.id,
        artist=artist,
        title="squabble up",
        slug="squabble-up",
    )
    return TrackVersion(
        id=uuid.uuid4(),
        track_id=track.id,
        track=track,
        version=1,
        status=status,
        transcript_object_key="transcripts/version/transcript.json",
    )


def transcript_payload(version_id: uuid.UUID) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "track_version_id": str(version_id),
        "engine": {"name": "whisper.cpp", "model": "base", "language": "en"},
        "metadata": {"duration_seconds": 2.0, "word_count": 2, "segment_count": 1},
        "text": "hello world",
        "segments": [
            {
                "id": 1,
                "start": 0,
                "end": 2,
                "text": "hello world",
                "words": [
                    {"word": "hello", "start": 0, "end": 1},
                    {"word": "world", "start": 1, "end": 2},
                ],
            },
        ],
    }


@pytest.mark.asyncio
async def test_publish_approved_version_writes_public_artifacts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    version = make_version()
    session = FakeSession(version)
    client = FakeMinioClient(transcript_payload(version.id))
    settings = SimpleNamespace(
        minio_transcripts_bucket="transcripts",
        minio_public_bucket="public",
    )

    async def load_transcript(_version: TrackVersion, _settings: object) -> TranscriptDocument:
        return TranscriptDocument.model_validate(transcript_payload(version.id))

    monkeypatch.setattr(service, "create_minio_client", lambda _settings: client)
    monkeypatch.setattr(service, "load_internal_transcript", load_transcript)
    monkeypatch.setattr(service, "ensure_public_bucket", lambda _client, _settings: None)
    monkeypatch.setattr(
        service,
        "ensure_immutable_objects_absent",
        lambda _client, _settings, _keys: None,
    )

    result = await publications.publish_version(
        session, version.id, make_user(), settings  # type: ignore[arg-type]
    )

    assert result.status == "published"
    assert version.status == "published"
    assert session.committed is True
    assert "karaoke/kendrick-lamar/squabble-up/latest.json" in client.objects
    assert "karaoke/kendrick-lamar/squabble-up/versions/v1/transcript.json" in client.objects
    assert result.public_urls.latest == "/api/public/karaoke/kendrick-lamar/squabble-up/latest"


@pytest.mark.asyncio
async def test_publish_rejects_non_approved_version() -> None:
    version = make_version(status="rejected")
    session = FakeSession(version)

    with pytest.raises(publications.VersionNotApprovedError):
        await publications.publish_version(
            session,
            version.id,
            make_user(),
            object(),  # type: ignore[arg-type]
        )

    assert session.committed is False
