from __future__ import annotations

import uuid
from typing import Any

from litestar import Request, get, patch, post
from litestar.exceptions import HTTPException

from sounds_right_api.db.session import SessionLocal
from sounds_right_api.domain.schemas import TrackCreate, TrackListResponse, TrackPublic, TrackUpdate
from sounds_right_api.routes.auth import get_current_user_from_request
from sounds_right_api.services.tracks import (
    TrackArtistNotFoundError,
    TrackNotFoundError,
    create_track,
    get_track,
    list_tracks,
    update_track,
)


@post("/api/tracks", status_code=201)
async def create_track_route(
    request: Request[Any, Any, Any],
    data: TrackCreate,
) -> TrackPublic:
    async with SessionLocal() as session:
        user = await get_current_user_from_request(request, session)
        try:
            return await create_track(session, data, user)
        except TrackArtistNotFoundError:
            raise HTTPException(status_code=404, detail="Artist not found") from None


@get("/api/tracks")
async def list_tracks_route(
    search: str | None = None,
    artist_id: uuid.UUID | None = None,
    limit: int = 20,
    offset: int = 0,
) -> TrackListResponse:
    safe_limit = min(max(limit, 1), 100)
    safe_offset = max(offset, 0)
    async with SessionLocal() as session:
        items = await list_tracks(session, search, artist_id, safe_limit, safe_offset)
        return TrackListResponse(items=items, limit=safe_limit, offset=safe_offset)


@get("/api/artists/{artist_id:uuid}/tracks")
async def list_artist_tracks_route(
    artist_id: uuid.UUID,
    limit: int = 20,
    offset: int = 0,
) -> TrackListResponse:
    safe_limit = min(max(limit, 1), 100)
    safe_offset = max(offset, 0)
    async with SessionLocal() as session:
        items = await list_tracks(session, None, artist_id, safe_limit, safe_offset)
        return TrackListResponse(items=items, limit=safe_limit, offset=safe_offset)


@get("/api/tracks/{track_id:uuid}")
async def get_track_route(track_id: uuid.UUID) -> TrackPublic:
    async with SessionLocal() as session:
        try:
            return await get_track(session, track_id)
        except TrackNotFoundError:
            raise HTTPException(status_code=404, detail="Track not found") from None


@patch("/api/tracks/{track_id:uuid}")
async def update_track_route(
    request: Request[Any, Any, Any],
    track_id: uuid.UUID,
    data: TrackUpdate,
) -> TrackPublic:
    async with SessionLocal() as session:
        await get_current_user_from_request(request, session)
        try:
            return await update_track(session, track_id, data)
        except TrackNotFoundError:
            raise HTTPException(status_code=404, detail="Track not found") from None
