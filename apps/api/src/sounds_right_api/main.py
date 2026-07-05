from litestar import Litestar, get
from litestar.config.cors import CORSConfig

from sounds_right_api.config import get_settings
from sounds_right_api.events.producer import EventProducer, EventProducerConfig
from sounds_right_api.events.projector import start_projector, stop_projector
from sounds_right_api.health import HealthResponse, get_health
from sounds_right_api.routes import artists, auth, jobs, publications, review, tracks, versions


@get("/api/health")
async def health() -> HealthResponse:
    return await get_health()


async def start_producer(app: Litestar) -> None:
    settings = get_settings()
    config = EventProducerConfig.from_settings(settings)
    producer = EventProducer(config)
    await producer.start()
    app.state.event_producer = producer


async def stop_producer(app: Litestar) -> None:
    producer = getattr(app.state, "event_producer", None)
    if producer is not None:
        await producer.stop()


def create_app() -> Litestar:
    settings = get_settings()
    return Litestar(
        route_handlers=[
            health,
            auth.register,
            auth.login,
            auth.me,
            artists.create_artist_route,
            artists.list_artists_route,
            artists.get_artist_route,
            artists.update_artist_route,
            tracks.create_track_route,
            tracks.list_tracks_route,
            tracks.list_artist_tracks_route,
            tracks.get_track_route,
            tracks.update_track_route,
            versions.create_track_version_route,
            versions.list_track_versions_route,
            versions.get_track_version_route,
            versions.create_upload_url_route,
            versions.complete_upload_route,
            versions.start_transcription_route,
            jobs.get_job_route,
            jobs.list_job_events_route,
            review.review_queue_route,
            review.version_transcript_route,
            review.review_events_route,
            review.approve_version_route,
            review.reject_version_route,
            publications.publish_version_route,
            publications.unpublish_version_route,
            publications.list_publications_route,
            publications.get_publication_route,
            publications.public_manifest_route,
            publications.public_latest_route,
            publications.public_version_route,
        ],
        cors_config=CORSConfig(
            allow_origins=settings.cors_origins,
            allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type"],
        ),
        on_startup=[start_projector, start_producer],
        on_shutdown=[stop_projector, stop_producer],
    )


app = create_app()
