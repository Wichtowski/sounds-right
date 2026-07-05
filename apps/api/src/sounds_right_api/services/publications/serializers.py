from sounds_right_api.domain.schemas import (
    ArtistSummary,
    PublicationPublic,
    PublicationUrls,
    PublicKaraokeManifest,
    PublicKaraokeVersion,
    ReviewTrackSummary,
    TranscriptDocument,
)
from sounds_right_api.models import Publication, TrackVersion


def public_object_keys(version: TrackVersion) -> dict[str, str]:
    artist_slug = version.track.artist.slug
    track_slug = version.track.slug
    root = f"karaoke/{artist_slug}/{track_slug}"
    version_root = f"{root}/versions/v{version.version}"
    return {
        "root_manifest": f"{root}/manifest.json",
        "latest": f"{root}/latest.json",
        "version_manifest": f"{version_root}/manifest.json",
        "transcript": f"{version_root}/transcript.json",
        "segments": f"{version_root}/segments.json",
        "words": f"{version_root}/words.json",
    }


def version_manifest_key(artist_slug: str, track_slug: str, version: int) -> str:
    return f"karaoke/{artist_slug}/{track_slug}/versions/v{version}/manifest.json"


def public_manifest(
    version: TrackVersion,
    versions: list[PublicKaraokeVersion],
    latest_version: int | None,
) -> PublicKaraokeManifest:
    return PublicKaraokeManifest(
        artist=ArtistSummary(
            id=version.track.artist.id,
            slug=version.track.artist.slug,
            display_name=version.track.artist.display_name,
        ),
        track=ReviewTrackSummary(
            id=version.track.id,
            title=version.track.title,
            slug=version.track.slug,
            album=version.track.album,
        ),
        latest_version=latest_version,
        versions=sorted(versions, key=lambda item: item.version),
    )


def public_manifest_version(
    publication: Publication,
    artist_slug: str,
    track_slug: str,
) -> PublicKaraokeVersion:
    return PublicKaraokeVersion(
        version=publication.version,
        publication_id=publication.id,
        status=publication.status,  # type: ignore[arg-type]
        published_at=publication.published_at,
        manifest_url=f"/api/public/karaoke/{artist_slug}/{track_slug}/manifest",
        transcript_url=f"/api/public/karaoke/{artist_slug}/{track_slug}/versions/{publication.version}",
    )


def publication_public(
    publication: Publication,
    artist_slug: str,
    track_slug: str,
) -> PublicationPublic:
    return PublicationPublic(
        id=publication.id,
        track_id=publication.track_id,
        track_version_id=publication.track_version_id,
        version=publication.version,
        status=publication.status,  # type: ignore[arg-type]
        public_manifest_object_key=publication.public_manifest_object_key,
        public_latest_object_key=publication.public_latest_object_key,
        public_transcript_object_key=publication.public_transcript_object_key,
        public_segments_object_key=publication.public_segments_object_key,
        public_words_object_key=publication.public_words_object_key,
        public_urls=PublicationUrls(
            manifest=f"/api/public/karaoke/{artist_slug}/{track_slug}/manifest",
            latest=(
                f"/api/public/karaoke/{artist_slug}/{track_slug}/latest"
                if publication.public_latest_object_key
                else None
            ),
            version=f"/api/public/karaoke/{artist_slug}/{track_slug}/versions/{publication.version}",
        ),
        published_by_user_id=publication.published_by_user_id,
        published_at=publication.published_at,
        unpublished_at=publication.unpublished_at,
        created_at=publication.created_at,
        updated_at=publication.updated_at,
    )


def word_artifact(transcript: TranscriptDocument) -> list[dict[str, object]]:
    words: list[dict[str, object]] = []
    for segment in transcript.segments:
        for word in segment.words:
            words.append(
                {
                    "segment_id": segment.id,
                    **word.model_dump(mode="json"),
                },
            )
    return words
