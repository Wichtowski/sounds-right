from __future__ import annotations

import uuid

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from sounds_right_api.domain.schemas import ArtistCreate, ArtistPublic, ArtistUpdate
from sounds_right_api.models import Artist, User
from sounds_right_api.services.slug import slugify


class ArtistNotFoundError(Exception):
    pass


async def create_artist(session: AsyncSession, payload: ArtistCreate, user: User) -> ArtistPublic:
    base_slug = slugify(payload.display_name)
    slug = await unique_artist_slug(session, base_slug)
    artist = Artist(
        slug=slug,
        display_name=payload.display_name,
        full_name=payload.full_name,
        created_by_user_id=user.id,
    )
    session.add(artist)
    await session.commit()
    await session.refresh(artist)
    return ArtistPublic.model_validate(artist)


async def list_artists(
    session: AsyncSession,
    search: str | None,
    limit: int,
    offset: int,
) -> list[ArtistPublic]:
    statement: Select[tuple[Artist]] = (
        select(Artist).order_by(Artist.display_name).limit(limit).offset(offset)
    )
    if search:
        statement = statement.where(Artist.display_name.ilike(f"%{search}%"))
    artists = (await session.scalars(statement)).all()
    return [ArtistPublic.model_validate(artist) for artist in artists]


async def get_artist(session: AsyncSession, artist_id: uuid.UUID) -> ArtistPublic:
    artist = await session.get(Artist, artist_id)
    if artist is None:
        raise ArtistNotFoundError
    return ArtistPublic.model_validate(artist)


async def update_artist(
    session: AsyncSession,
    artist_id: uuid.UUID,
    payload: ArtistUpdate,
) -> ArtistPublic:
    artist = await session.get(Artist, artist_id)
    if artist is None:
        raise ArtistNotFoundError
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(artist, field, value)
    await session.commit()
    await session.refresh(artist)
    return ArtistPublic.model_validate(artist)


async def unique_artist_slug(session: AsyncSession, base_slug: str) -> str:
    existing = set(
        await session.scalars(select(Artist.slug).where(Artist.slug.like(f"{base_slug}%"))),
    )
    if base_slug not in existing:
        return base_slug
    suffix = 2
    while f"{base_slug}-{suffix}" in existing:
        suffix += 1
    return f"{base_slug}-{suffix}"
