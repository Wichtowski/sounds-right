from __future__ import annotations

import os
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock

import pytest
import pytest_asyncio
from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from sounds_right_api.config import ApiSettings
from sounds_right_api.db.base import Base
from sounds_right_api.domain.schemas import UploadCompleteRequest, UploadUrlRequest
from sounds_right_api.models import Artist, Track, TrackVersion, UploadSession
from sounds_right_api.services import versions

SETTINGS = ApiSettings.model_construct(
    minio_temp_audio_bucket="temp-audio",
    max_audio_upload_size_bytes=1024,
    upload_url_expires_seconds=900,
)
PAYLOAD = UploadUrlRequest(filename="song.mp3", content_type="audio/mpeg", size_bytes=100)


@pytest_asyncio.fixture
async def session() -> AsyncIterator[AsyncSession]:
    database_url = os.environ.get("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Set TEST_DATABASE_URL to run PostgreSQL upload integration tests")
    schema = f"test_upload_{uuid.uuid4().hex}"
    engine = create_async_engine(
        database_url,
        connect_args={"server_settings": {"search_path": schema}},
    )
    try:
        async with engine.begin() as connection:
            await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
            await connection.run_sync(Base.metadata.create_all)
        async with AsyncSession(engine, expire_on_commit=False) as db_session:
            artist = Artist(slug="test-artist", display_name="Test Artist")
            track = Track(artist=artist, slug="test-track", title="Test Track")
            db_session.add(TrackVersion(track=track, version=1, status="draft"))
            await db_session.commit()
            yield db_session
    finally:
        async with engine.begin() as connection:
            await connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        await engine.dispose()


@pytest.fixture
def storage(monkeypatch: pytest.MonkeyPatch) -> Mock:
    client = Mock()
    client.presigned_put_object.return_value = "http://storage.test/signed-upload"
    client.stat_object.return_value.size = 100
    monkeypatch.setattr(versions, "create_public_minio_client", lambda _settings: client)
    monkeypatch.setattr(versions, "create_minio_client", lambda _settings: client)
    return client


@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["uploaded", "queued_for_processing", "processing", "published"])
async def test_cannot_replace_submitted_audio(status: str) -> None:
    session = AsyncMock()
    session.get.return_value = TrackVersion(status=status)

    with pytest.raises(versions.InvalidVersionStatusError):
        await versions.create_upload_url(session, uuid.uuid4(), PAYLOAD, SETTINGS)

    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_retry_replaces_session_and_completes_new_file(
    session: AsyncSession,
    storage: Mock,
) -> None:
    version = (await session.scalars(select(TrackVersion))).one()
    first = await versions.create_upload_url(session, version.id, PAYLOAD, SETTINGS)
    replacement = PAYLOAD.model_copy(
        update={"filename": "replacement.wav", "content_type": "audio/wav"}
    )
    second = await versions.create_upload_url(session, version.id, replacement, SETTINGS)

    assert first.object_key != second.object_key
    assert second.object_key.endswith("/input.wav")
    with pytest.raises(versions.UploadSessionNotFoundError):
        await versions.complete_upload(
            session,
            version.id,
            UploadCompleteRequest(object_key=first.object_key),
            SETTINGS,
        )
    storage.stat_object.assert_not_called()

    result = await versions.complete_upload(
        session,
        version.id,
        UploadCompleteRequest(object_key=second.object_key),
        SETTINGS,
    )
    assert result.status == "uploaded"
    assert result.temporary_audio_object_key == second.object_key
    assert result.original_audio_filename == "replacement.wav"
    assert result.audio_content_type == "audio/wav"
    assert result.audio_size_bytes == 100


@pytest.mark.asyncio
async def test_expired_session_can_be_renewed(session: AsyncSession, storage: Mock) -> None:
    version = (await session.scalars(select(TrackVersion))).one()
    first = await versions.create_upload_url(session, version.id, PAYLOAD, SETTINGS)
    await session.execute(
        update(UploadSession).values(expires_at=datetime.now(UTC) - timedelta(seconds=1)),
    )
    await session.commit()

    with pytest.raises(versions.UploadSessionNotFoundError):
        await versions.complete_upload(
            session,
            version.id,
            UploadCompleteRequest(object_key=first.object_key),
            SETTINGS,
        )

    second = await versions.create_upload_url(session, version.id, PAYLOAD, SETTINGS)
    result = await versions.complete_upload(
        session,
        version.id,
        UploadCompleteRequest(object_key=second.object_key),
        SETTINGS,
    )
    assert result.status == "uploaded"


@pytest.mark.asyncio
async def test_signing_failure_preserves_previous_session(
    session: AsyncSession,
    storage: Mock,
) -> None:
    version = (await session.scalars(select(TrackVersion))).one()
    first = await versions.create_upload_url(session, version.id, PAYLOAD, SETTINGS)
    storage.presigned_put_object.side_effect = RuntimeError("Storage unavailable")

    with pytest.raises(RuntimeError, match="Storage unavailable"):
        await versions.create_upload_url(session, version.id, PAYLOAD, SETTINGS)
    await session.rollback()
    await session.refresh(version)

    result = await versions.complete_upload(
        session,
        version.id,
        UploadCompleteRequest(object_key=first.object_key),
        SETTINGS,
    )
    assert result.status == "uploaded"


@pytest.mark.asyncio
async def test_oversized_upload_can_be_retried(session: AsyncSession, storage: Mock) -> None:
    version = (await session.scalars(select(TrackVersion))).one()
    first = await versions.create_upload_url(session, version.id, PAYLOAD, SETTINGS)
    storage.stat_object.return_value.size = SETTINGS.max_audio_upload_size_bytes + 1

    with pytest.raises(versions.UploadTooLargeError):
        await versions.complete_upload(
            session,
            version.id,
            UploadCompleteRequest(object_key=first.object_key),
            SETTINGS,
        )

    storage.stat_object.return_value.size = 100
    second = await versions.create_upload_url(session, version.id, PAYLOAD, SETTINGS)
    result = await versions.complete_upload(
        session,
        version.id,
        UploadCompleteRequest(object_key=second.object_key),
        SETTINGS,
    )
    assert result.status == "uploaded"
