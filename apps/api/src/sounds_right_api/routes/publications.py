from __future__ import annotations

import uuid
from typing import Any

from litestar import Request, get, post
from litestar.exceptions import HTTPException

from sounds_right_api.config import get_settings
from sounds_right_api.db.session import SessionLocal
from sounds_right_api.domain.schemas import (
    PublicationListResponse,
    PublicationPublic,
    PublicationStatus,
    PublicKaraokeDocument,
    PublicKaraokeManifest,
    PublishVersionRequest,
    UnpublishVersionRequest,
)
from sounds_right_api.routes.auth import get_current_user_from_request
from sounds_right_api.services.publications import (
    ForbiddenPublishActionError,
    PublicArtifactMissingError,
    PublicArtifactStorageError,
    PublicationAlreadyExistsError,
    PublicationNotFoundError,
    VersionNotApprovedError,
    VersionNotFoundError,
    VersionNotPublishedError,
    get_public_latest,
    get_public_manifest,
    get_public_version,
    get_publication,
    list_publications,
    publish_version,
    unpublish_version,
)
from sounds_right_api.services.review import (
    ForbiddenReviewActionError,
    TranscriptMissingError,
    TranscriptStorageError,
)


@post("/api/versions/{version_id:uuid}/publish")
async def publish_version_route(
    request: Request[Any, Any, Any],
    version_id: uuid.UUID,
    data: PublishVersionRequest,
) -> PublicationPublic:
    async with SessionLocal() as session:
        user = await get_current_user_from_request(request, session)
        try:
            return await publish_version(
                session,
                version_id,
                user,
                get_settings(),
                data.make_latest,
            )
        except VersionNotFoundError:
            raise HTTPException(status_code=404, detail="Version not found") from None
        except ForbiddenReviewActionError:
            raise HTTPException(status_code=403, detail="Reviewer or admin role required") from None
        except VersionNotApprovedError:
            raise HTTPException(
                status_code=409,
                detail="Only approved versions can be published",
            ) from None
        except PublicationAlreadyExistsError:
            raise HTTPException(status_code=409, detail="Version is already published") from None
        except TranscriptMissingError:
            raise HTTPException(
                status_code=404,
                detail="Transcript artifact was not found",
            ) from None
        except (TranscriptStorageError, PublicArtifactStorageError):
            raise HTTPException(
                status_code=500,
                detail="Publication artifacts could not be written",
            ) from None


@post("/api/versions/{version_id:uuid}/unpublish")
async def unpublish_version_route(
    request: Request[Any, Any, Any],
    version_id: uuid.UUID,
    data: UnpublishVersionRequest,
) -> PublicationPublic:
    _ = data
    async with SessionLocal() as session:
        user = await get_current_user_from_request(request, session)
        try:
            return await unpublish_version(session, version_id, user)
        except VersionNotFoundError:
            raise HTTPException(status_code=404, detail="Version not found") from None
        except ForbiddenPublishActionError:
            raise HTTPException(status_code=403, detail="Admin role required") from None
        except VersionNotPublishedError:
            raise HTTPException(
                status_code=409,
                detail="Version is not actively published",
            ) from None


@get("/api/publications")
async def list_publications_route(
    request: Request[Any, Any, Any],
    track_id: uuid.UUID | None = None,
    status: PublicationStatus | None = None,
    limit: int = 20,
    offset: int = 0,
) -> PublicationListResponse:
    bounded_limit = min(max(limit, 1), 100)
    bounded_offset = max(offset, 0)
    async with SessionLocal() as session:
        await get_current_user_from_request(request, session)
        return await list_publications(session, track_id, status, bounded_limit, bounded_offset)


@get("/api/publications/{publication_id:uuid}")
async def get_publication_route(
    request: Request[Any, Any, Any],
    publication_id: uuid.UUID,
) -> PublicationPublic:
    async with SessionLocal() as session:
        await get_current_user_from_request(request, session)
        try:
            return await get_publication(session, publication_id)
        except PublicationNotFoundError:
            raise HTTPException(status_code=404, detail="Publication not found") from None


@get("/api/public/karaoke/{artist_slug:str}/{track_slug:str}/manifest")
async def public_manifest_route(
    artist_slug: str,
    track_slug: str,
) -> PublicKaraokeManifest:
    async with SessionLocal() as session:
        try:
            return await get_public_manifest(session, artist_slug, track_slug, get_settings())
        except (PublicationNotFoundError, PublicArtifactMissingError):
            raise HTTPException(
                status_code=404,
                detail="Published karaoke manifest not found",
            ) from None
        except PublicArtifactStorageError:
            raise HTTPException(
                status_code=500,
                detail="Published karaoke manifest could not be loaded",
            ) from None


@get("/api/public/karaoke/{artist_slug:str}/{track_slug:str}/latest")
async def public_latest_route(
    artist_slug: str,
    track_slug: str,
) -> PublicKaraokeDocument:
    async with SessionLocal() as session:
        try:
            return await get_public_latest(session, artist_slug, track_slug, get_settings())
        except (PublicationNotFoundError, PublicArtifactMissingError):
            raise HTTPException(
                status_code=404,
                detail="Published karaoke transcript not found",
            ) from None
        except PublicArtifactStorageError:
            raise HTTPException(
                status_code=500,
                detail="Published karaoke transcript could not be loaded",
            ) from None


@get("/api/public/karaoke/{artist_slug:str}/{track_slug:str}/versions/{version:int}")
async def public_version_route(
    artist_slug: str,
    track_slug: str,
    version: int,
) -> PublicKaraokeDocument:
    async with SessionLocal() as session:
        try:
            return await get_public_version(
                session,
                artist_slug,
                track_slug,
                version,
                get_settings(),
            )
        except (PublicationNotFoundError, PublicArtifactMissingError):
            raise HTTPException(
                status_code=404,
                detail="Published karaoke version not found",
            ) from None
        except PublicArtifactStorageError:
            raise HTTPException(
                status_code=500,
                detail="Published karaoke version could not be loaded",
            ) from None
