from __future__ import annotations

import uuid
from typing import Any

from litestar import Request, get, post
from litestar.exceptions import HTTPException

from sounds_right_api.config import get_settings
from sounds_right_api.db.session import SessionLocal
from sounds_right_api.domain.schemas import (
    StartTranscriptionRequest,
    StartTranscriptionResponse,
    TrackVersionCreate,
    TrackVersionPublic,
    UploadCompleteRequest,
    UploadUrlRequest,
    UploadUrlResponse,
)
from sounds_right_api.routes.auth import get_current_user_from_request
from sounds_right_api.services.jobs import (
    ActiveJobExistsError,
    MissingAudioObjectError,
    VersionNotUploadedError,
    start_transcription,
)
from sounds_right_api.services.jobs import (
    VersionNotFoundError as JobVersionNotFoundError,
)
from sounds_right_api.services.versions import (
    InvalidVersionStatusError,
    UploadObjectNotFoundError,
    UploadSessionNotFoundError,
    UploadTooLargeError,
    VersionNotFoundError,
    VersionTrackNotFoundError,
    complete_upload,
    create_track_version,
    create_upload_url,
    get_track_version,
    list_track_versions,
)


@post("/api/tracks/{track_id:uuid}/versions", status_code=201)
async def create_track_version_route(
    request: Request[Any, Any, Any],
    track_id: uuid.UUID,
    data: TrackVersionCreate,
) -> TrackVersionPublic:
    _ = data
    async with SessionLocal() as session:
        user = await get_current_user_from_request(request, session)
        try:
            return await create_track_version(session, track_id, user)
        except VersionTrackNotFoundError:
            raise HTTPException(status_code=404, detail="Track not found") from None


@get("/api/tracks/{track_id:uuid}/versions")
async def list_track_versions_route(track_id: uuid.UUID) -> list[TrackVersionPublic]:
    async with SessionLocal() as session:
        return await list_track_versions(session, track_id)


@get("/api/versions/{version_id:uuid}")
async def get_track_version_route(version_id: uuid.UUID) -> TrackVersionPublic:
    async with SessionLocal() as session:
        try:
            return await get_track_version(session, version_id)
        except VersionNotFoundError:
            raise HTTPException(status_code=404, detail="Version not found") from None


@post("/api/versions/{version_id:uuid}/upload-url")
async def create_upload_url_route(
    request: Request[Any, Any, Any],
    version_id: uuid.UUID,
    data: UploadUrlRequest,
) -> UploadUrlResponse:
    async with SessionLocal() as session:
        await get_current_user_from_request(request, session)
        try:
            return await create_upload_url(session, version_id, data, get_settings())
        except VersionNotFoundError:
            raise HTTPException(status_code=404, detail="Version not found") from None
        except InvalidVersionStatusError:
            raise HTTPException(status_code=409, detail="Version is not in draft status") from None
        except UploadTooLargeError:
            raise HTTPException(status_code=413, detail="Audio file is too large") from None


@post("/api/versions/{version_id:uuid}/upload-complete")
async def complete_upload_route(
    request: Request[Any, Any, Any],
    version_id: uuid.UUID,
    data: UploadCompleteRequest,
) -> TrackVersionPublic:
    async with SessionLocal() as session:
        await get_current_user_from_request(request, session)
        try:
            return await complete_upload(session, version_id, data, get_settings())
        except VersionNotFoundError:
            raise HTTPException(status_code=404, detail="Version not found") from None
        except UploadSessionNotFoundError:
            raise HTTPException(status_code=404, detail="Upload session not found") from None
        except UploadObjectNotFoundError:
            raise HTTPException(status_code=404, detail="Uploaded object was not found") from None
        except InvalidVersionStatusError:
            raise HTTPException(
                status_code=409,
                detail="Version is not waiting for upload",
            ) from None
        except UploadTooLargeError:
            raise HTTPException(status_code=413, detail="Audio file is too large") from None


@post("/api/versions/{version_id:uuid}/start-transcription", status_code=202)
async def start_transcription_route(
    request: Request[Any, Any, Any],
    version_id: uuid.UUID,
    data: StartTranscriptionRequest,
) -> StartTranscriptionResponse:
    async with SessionLocal() as session:
        user = await get_current_user_from_request(request, session)
        try:
            producer = request.app.state.event_producer
            return await start_transcription(
                session,
                version_id,
                data,
                user,
                producer,
            )
        except JobVersionNotFoundError:
            raise HTTPException(status_code=404, detail="Version not found") from None
        except VersionNotUploadedError:
            raise HTTPException(
                status_code=409,
                detail="Version audio has not been uploaded",
            ) from None
        except MissingAudioObjectError:
            raise HTTPException(
                status_code=409,
                detail="Version is missing uploaded audio metadata",
            ) from None
        except ActiveJobExistsError:
            raise HTTPException(
                status_code=409,
                detail="A transcription job is already active for this version",
            ) from None
