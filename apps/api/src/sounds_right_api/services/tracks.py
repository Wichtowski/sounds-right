from __future__ import annotations

import uuid

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from sounds_right_api.domain.schemas import ArtistSummary, TrackCreate, TrackPublic, TrackUpdate
from sounds_right_api.models import Artist, Track, User
from sounds_right_api.services.slug import slugify


class TrackNotFoundError(Exception):
    pass


class TrackArtistNotFoundError(Exception):
    pass


async def create_track(session: AsyncSession, payload: TrackCreate, user: User) -> TrackPublic:
    artist = await session.get(Artist, payload.artist_id)
    if artist is None:
        raise TrackArtistNotFoundError
    base_slug = slugify(payload.title)
    slug = await unique_track_slug(session, payload.artist_id, base_slug)
    track = Track(
        artist_id=payload.artist_id,
        title=payload.title,
        album=payload.album,
        slug=slug,
        created_by_user_id=user.id,
    )
    session.add(track)
    await session.commit()
    await session.refresh(track, attribute_names=["artist"])
    return serialize_track(track)


async def list_tracks(
    session: AsyncSession,
    search: str | None,
    artist_id: uuid.UUID | None,
    limit: int,
    offset: int,
) -> list[TrackPublic]:
    statement: Select[tuple[Track]] = (
        select(Track)
        .options(selectinload(Track.artist))
        .order_by(Track.title)
        .limit(limit)
        .offset(offset)
    )
    if search:
        statement = statement.where(Track.title.ilike(f"%{search}%"))
    if artist_id:
        statement = statement.where(Track.artist_id == artist_id)
    tracks = (await session.scalars(statement)).all()
    return [serialize_track(track) for track in tracks]


async def get_track(session: AsyncSession, track_id: uuid.UUID) -> TrackPublic:
    track = await session.scalar(
        select(Track).where(Track.id == track_id).options(selectinload(Track.artist)),
    )
    if track is None:
        raise TrackNotFoundError
    return serialize_track(track)


async def update_track(
    session: AsyncSession,
    track_id: uuid.UUID,
    payload: TrackUpdate,
) -> TrackPublic:
    track = await session.scalar(
        select(Track).where(Track.id == track_id).options(selectinload(Track.artist)),
    )
    if track is None:
        raise TrackNotFoundError
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(track, field, value)
    await session.commit()
    await session.refresh(track, attribute_names=["artist"])
    return serialize_track(track)


async def unique_track_slug(session: AsyncSession, artist_id: uuid.UUID, base_slug: str) -> str:
    existing = set(
        await session.scalars(
            select(Track.slug).where(
                Track.artist_id == artist_id,
                Track.slug.like(f"{base_slug}%"),
            ),
        ),
    )
    if base_slug not in existing:
        return base_slug
    suffix = 2
    while f"{base_slug}-{suffix}" in existing:
        suffix += 1
    return f"{base_slug}-{suffix}"


def serialize_track(track: Track) -> TrackPublic:
    artist = None
    if track.artist is not None:
        artist = ArtistSummary(
            id=track.artist.id,
            slug=track.artist.slug,
            display_name=track.artist.display_name,
        )
    return TrackPublic(
        id=track.id,
        artist_id=track.artist_id,
        title=track.title,
        album=track.album,
        slug=track.slug,
        created_at=track.created_at,
        updated_at=track.updated_at,
        artist=artist,
    )
