from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from sounds_right_api.models import Artist, Publication, Track, TrackVersion

from .errors import PublicationNotFoundError, VersionNotFoundError


async def get_version_for_publish(session: AsyncSession, version_id: uuid.UUID) -> TrackVersion:
    version = await session.scalar(
        select(TrackVersion)
        .where(TrackVersion.id == version_id)
        .options(selectinload(TrackVersion.track).selectinload(Track.artist))
        .with_for_update(),
    )
    if version is None:
        raise VersionNotFoundError
    return version


async def get_publication_by_slugs(
    session: AsyncSession,
    artist_slug: str,
    track_slug: str,
    version: int | None = None,
) -> Publication:
    statement = (
        select(Publication)
        .join(Publication.track)
        .join(Track.artist)
        .options(selectinload(Publication.track).selectinload(Track.artist))
    )
    if version is None:
        statement = statement.where(
            Publication.status == "published",
            Publication.public_latest_object_key.is_not(None),
        )
    else:
        statement = statement.where(
            Publication.status.in_(["published", "superseded"]),
            Publication.version == version,
        )
    statement = statement.where(Track.slug == track_slug, Artist.slug == artist_slug)
    publication = await session.scalar(statement)
    if publication is None:
        raise PublicationNotFoundError
    return publication
