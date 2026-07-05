from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from sounds_right_api.config import ApiSettings
from sounds_right_api.domain.schemas import (
    PublicationListResponse,
    PublicationPublic,
    PublicationStatus,
    PublicKaraokeDocument,
    PublicKaraokeManifest,
    TranscriptDocument,
)
from sounds_right_api.models import Publication, Track, User
from sounds_right_api.services.review import ensure_reviewer
from sounds_right_api.storage.minio_client import create_minio_client

from .artifacts import (
    ensure_immutable_objects_absent,
    ensure_public_bucket,
    load_internal_transcript,
    read_public_json,
    write_json_object,
)
from .errors import (
    PublicArtifactMissingError,
    PublicationAlreadyExistsError,
    PublicationNotFoundError,
    VersionNotApprovedError,
    VersionNotPublishedError,
)
from .permissions import ensure_admin
from .queries import get_publication_by_slugs, get_version_for_publish
from .serializers import (
    public_manifest,
    public_manifest_version,
    public_object_keys,
    publication_public,
    version_manifest_key,
    word_artifact,
)


async def publish_version(
    session: AsyncSession,
    version_id: uuid.UUID,
    user: User,
    settings: ApiSettings,
    make_latest: bool = True,
) -> PublicationPublic:
    ensure_reviewer(user)
    version = await get_version_for_publish(session, version_id)
    existing = await session.scalar(
        select(Publication).where(Publication.track_version_id == version_id),
    )
    if existing is not None:
        raise PublicationAlreadyExistsError
    if version.status != "approved":
        raise VersionNotApprovedError

    transcript = await load_internal_transcript(version, settings)
    client = create_minio_client(settings)
    ensure_public_bucket(client, settings)

    object_keys = public_object_keys(version)
    root_manifest_key = object_keys["root_manifest"]
    latest_key = object_keys["latest"] if make_latest else None
    ensure_immutable_objects_absent(
        client,
        settings,
        [
            object_keys["version_manifest"],
            object_keys["transcript"],
            object_keys["segments"],
            object_keys["words"],
        ],
    )

    publication = Publication(
        id=uuid.uuid4(),
        track_id=version.track_id,
        track_version_id=version.id,
        version=version.version,
        status="published",
        public_manifest_object_key=root_manifest_key,
        public_latest_object_key=latest_key,
        public_transcript_object_key=object_keys["transcript"],
        public_segments_object_key=object_keys["segments"],
        public_words_object_key=object_keys["words"],
        published_by_user_id=user.id,
        published_at=datetime.now(UTC),
    )

    previous_publications: Sequence[Publication] = []
    if make_latest:
        previous_publications = (
            await session.scalars(
                select(Publication).where(
                    Publication.track_id == version.track_id,
                    Publication.status == "published",
                ),
            )
        ).all()
        for previous_publication in previous_publications:
            previous_publication.status = "superseded"

    artist_slug = version.track.artist.slug
    track_slug = version.track.slug
    active_versions = [
        public_manifest_version(existing_publication, artist_slug, track_slug)
        for existing_publication in previous_publications
    ]
    active_versions.append(public_manifest_version(publication, artist_slug, track_slug))
    manifest = public_manifest(version, active_versions, version.version if make_latest else None)
    document = PublicKaraokeDocument(manifest=manifest, transcript=transcript)

    write_json_object(client, settings, object_keys["version_manifest"], manifest)
    write_json_object(client, settings, object_keys["transcript"], transcript)
    write_json_object(
        client,
        settings,
        object_keys["segments"],
        [segment.model_dump(mode="json") for segment in transcript.segments],
    )
    write_json_object(client, settings, object_keys["words"], word_artifact(transcript))
    write_json_object(client, settings, root_manifest_key, manifest)
    if latest_key is not None:
        write_json_object(client, settings, latest_key, document)

    version.status = "published"
    session.add(publication)
    await session.commit()
    await session.refresh(publication)
    return publication_public(publication, version.track.artist.slug, version.track.slug)


async def unpublish_version(
    session: AsyncSession,
    version_id: uuid.UUID,
    user: User,
) -> PublicationPublic:
    ensure_admin(user)
    version = await get_version_for_publish(session, version_id)
    publication = await session.scalar(
        select(Publication)
        .where(
            Publication.track_version_id == version_id,
            Publication.status == "published",
        )
        .options(selectinload(Publication.track).selectinload(Track.artist)),
    )
    if publication is None:
        raise VersionNotPublishedError

    publication.status = "unpublished"
    publication.unpublished_at = datetime.now(UTC)
    version.status = "approved"
    await session.commit()
    await session.refresh(publication)
    return publication_public(publication, version.track.artist.slug, version.track.slug)


async def list_publications(
    session: AsyncSession,
    track_id: uuid.UUID | None,
    status: PublicationStatus | None,
    limit: int,
    offset: int,
) -> PublicationListResponse:
    conditions = []
    if track_id is not None:
        conditions.append(Publication.track_id == track_id)
    if status is not None:
        conditions.append(Publication.status == status)

    total_statement = select(func.count()).select_from(Publication)
    statement: Select[tuple[Publication]] = (
        select(Publication)
        .options(selectinload(Publication.track).selectinload(Track.artist))
        .order_by(Publication.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if conditions:
        total_statement = total_statement.where(*conditions)
        statement = statement.where(*conditions)

    total = await session.scalar(total_statement)
    publications = (await session.scalars(statement)).all()
    return PublicationListResponse(
        items=[
            publication_public(publication, publication.track.artist.slug, publication.track.slug)
            for publication in publications
        ],
        limit=limit,
        offset=offset,
        total=int(total or 0),
    )


async def get_publication(session: AsyncSession, publication_id: uuid.UUID) -> PublicationPublic:
    publication = await session.scalar(
        select(Publication)
        .where(Publication.id == publication_id)
        .options(selectinload(Publication.track).selectinload(Track.artist)),
    )
    if publication is None:
        raise PublicationNotFoundError
    return publication_public(publication, publication.track.artist.slug, publication.track.slug)


async def get_public_manifest(
    session: AsyncSession,
    artist_slug: str,
    track_slug: str,
    settings: ApiSettings,
) -> PublicKaraokeManifest:
    publication = await get_publication_by_slugs(session, artist_slug, track_slug)
    return read_public_json(
        settings,
        publication.public_manifest_object_key,
        PublicKaraokeManifest,
    )


async def get_public_latest(
    session: AsyncSession,
    artist_slug: str,
    track_slug: str,
    settings: ApiSettings,
) -> PublicKaraokeDocument:
    publication = await get_publication_by_slugs(session, artist_slug, track_slug)
    if publication.public_latest_object_key is None:
        raise PublicArtifactMissingError
    return read_public_json(settings, publication.public_latest_object_key, PublicKaraokeDocument)


async def get_public_version(
    session: AsyncSession,
    artist_slug: str,
    track_slug: str,
    version: int,
    settings: ApiSettings,
) -> PublicKaraokeDocument:
    publication = await get_publication_by_slugs(session, artist_slug, track_slug, version)
    manifest = read_public_json(
        settings,
        version_manifest_key(artist_slug, track_slug, publication.version),
        PublicKaraokeManifest,
    )
    transcript = read_public_json(
        settings,
        publication.public_transcript_object_key,
        TranscriptDocument,
    )
    return PublicKaraokeDocument(manifest=manifest, transcript=transcript)
