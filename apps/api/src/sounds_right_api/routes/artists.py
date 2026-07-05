from __future__ import annotations

import uuid
from typing import Any

from litestar import Request, get, patch, post
from litestar.exceptions import HTTPException

from sounds_right_api.db.session import SessionLocal
from sounds_right_api.domain.schemas import (
    ArtistCreate,
    ArtistListResponse,
    ArtistPublic,
    ArtistUpdate,
)
from sounds_right_api.routes.auth import get_current_user_from_request
from sounds_right_api.services.artists import (
    ArtistNotFoundError,
    create_artist,
    get_artist,
    list_artists,
    update_artist,
)


@post("/api/artists", status_code=201)
async def create_artist_route(
    request: Request[Any, Any, Any],
    data: ArtistCreate,
) -> ArtistPublic:
    async with SessionLocal() as session:
        user = await get_current_user_from_request(request, session)
        return await create_artist(session, data, user)


@get("/api/artists")
async def list_artists_route(
    search: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> ArtistListResponse:
    safe_limit = min(max(limit, 1), 100)
    safe_offset = max(offset, 0)
    async with SessionLocal() as session:
        items = await list_artists(session, search, safe_limit, safe_offset)
        return ArtistListResponse(items=items, limit=safe_limit, offset=safe_offset)


@get("/api/artists/{artist_id:uuid}")
async def get_artist_route(artist_id: uuid.UUID) -> ArtistPublic:
    async with SessionLocal() as session:
        try:
            return await get_artist(session, artist_id)
        except ArtistNotFoundError:
            raise HTTPException(status_code=404, detail="Artist not found") from None


@patch("/api/artists/{artist_id:uuid}")
async def update_artist_route(
    request: Request[Any, Any, Any],
    artist_id: uuid.UUID,
    data: ArtistUpdate,
) -> ArtistPublic:
    async with SessionLocal() as session:
        await get_current_user_from_request(request, session)
        try:
            return await update_artist(session, artist_id, data)
        except ArtistNotFoundError:
            raise HTTPException(status_code=404, detail="Artist not found") from None
