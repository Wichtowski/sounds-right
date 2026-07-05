from __future__ import annotations

import uuid
from typing import Any

from litestar import Request, get, post
from litestar.exceptions import HTTPException

from sounds_right_api.config import get_settings
from sounds_right_api.db.session import SessionLocal
from sounds_right_api.domain.schemas import (
    ApproveVersionRequest,
    RejectVersionRequest,
    ReviewEventsResponse,
    ReviewQueueResponse,
    ReviewQueueStatus,
    TrackVersionPublic,
    TranscriptDocument,
)
from sounds_right_api.routes.auth import get_current_user_from_request
from sounds_right_api.services.review import (
    ForbiddenReviewActionError,
    TranscriptMissingError,
    TranscriptStorageError,
    VersionNotFoundError,
    VersionNotReviewableError,
    approve_version,
    ensure_reviewer,
    get_transcript,
    list_review_events,
    list_review_queue,
    reject_version,
)


@get("/api/review/queue")
async def review_queue_route(
    request: Request[Any, Any, Any],
    status: ReviewQueueStatus = "completed",
    limit: int = 20,
    offset: int = 0,
) -> ReviewQueueResponse:
    bounded_limit = min(max(limit, 1), 100)
    bounded_offset = max(offset, 0)
    async with SessionLocal() as session:
        user = await get_current_user_from_request(request, session)
        try:
            ensure_reviewer(user)
        except ForbiddenReviewActionError:
            raise HTTPException(status_code=403, detail="Reviewer or admin role required") from None
        return await list_review_queue(session, status, bounded_limit, bounded_offset)


@get("/api/versions/{version_id:uuid}/transcript")
async def version_transcript_route(
    request: Request[Any, Any, Any],
    version_id: uuid.UUID,
) -> TranscriptDocument:
    async with SessionLocal() as session:
        await get_current_user_from_request(request, session)
        try:
            return await get_transcript(session, version_id, get_settings())
        except VersionNotFoundError:
            raise HTTPException(status_code=404, detail="Version not found") from None
        except TranscriptMissingError:
            raise HTTPException(
                status_code=404,
                detail="Transcript artifact was not found",
            ) from None
        except TranscriptStorageError:
            raise HTTPException(
                status_code=500,
                detail="Transcript artifact could not be loaded",
            ) from None


@get("/api/versions/{version_id:uuid}/review-events")
async def review_events_route(
    request: Request[Any, Any, Any],
    version_id: uuid.UUID,
) -> ReviewEventsResponse:
    async with SessionLocal() as session:
        await get_current_user_from_request(request, session)
        try:
            return ReviewEventsResponse(items=await list_review_events(session, version_id))
        except VersionNotFoundError:
            raise HTTPException(status_code=404, detail="Version not found") from None


@post("/api/versions/{version_id:uuid}/approve")
async def approve_version_route(
    request: Request[Any, Any, Any],
    version_id: uuid.UUID,
    data: ApproveVersionRequest,
) -> TrackVersionPublic:
    async with SessionLocal() as session:
        user = await get_current_user_from_request(request, session)
        try:
            return await approve_version(session, version_id, user, data.note, get_settings())
        except VersionNotFoundError:
            raise HTTPException(status_code=404, detail="Version not found") from None
        except ForbiddenReviewActionError:
            raise HTTPException(status_code=403, detail="Reviewer or admin role required") from None
        except VersionNotReviewableError:
            raise HTTPException(
                status_code=409,
                detail="Only completed versions can be approved",
            ) from None
        except TranscriptMissingError:
            raise HTTPException(
                status_code=404,
                detail="Transcript artifact was not found",
            ) from None
        except TranscriptStorageError:
            raise HTTPException(
                status_code=500,
                detail="Transcript artifact could not be checked",
            ) from None


@post("/api/versions/{version_id:uuid}/reject")
async def reject_version_route(
    request: Request[Any, Any, Any],
    version_id: uuid.UUID,
    data: RejectVersionRequest,
) -> TrackVersionPublic:
    async with SessionLocal() as session:
        user = await get_current_user_from_request(request, session)
        try:
            return await reject_version(session, version_id, user, data.reason)
        except VersionNotFoundError:
            raise HTTPException(status_code=404, detail="Version not found") from None
        except ForbiddenReviewActionError:
            raise HTTPException(status_code=403, detail="Reviewer or admin role required") from None
        except VersionNotReviewableError:
            raise HTTPException(
                status_code=409,
                detail="Only completed versions can be rejected",
            ) from None
