import asyncio
import signal

from sounds_right_worker.config import get_settings
from sounds_right_worker.events.consumer import ConsumerConfig, consume_requested_events
from sounds_right_worker.events.producer import EventProducer, EventProducerConfig
from sounds_right_worker.events.schemas import (
    EventEnvelope,
    TranscriptionCompletedPayload,
    TranscriptionFailedPayload,
    TranscriptionProgressPayload,
    TranscriptionStartedPayload,
)
from sounds_right_worker.health import get_health
from sounds_right_worker.jobs.pipeline import build_pipeline
from sounds_right_worker.logging import configure_logging, get_logger
from sounds_right_worker.storage.minio_client import create_storage_client
from sounds_right_worker.transcription.engine import create_engine

configure_logging()
logger = get_logger("sounds_right_worker")

running = True


def stop_worker(signum: int, frame: object) -> None:
    global running
    logger.info("received stop signal", extra={"signal": signum})
    running = False


async def process_requested_event(
    event: EventEnvelope,
    producer: EventProducer,
    worker_name: str,
    should_fail: bool,
    step_delay_seconds: float,
) -> None:
    requested = event.payload
    if not hasattr(requested, "job_id") or not hasattr(requested, "track_version_id"):
        return

    await producer.publish(
        EventEnvelope(
            event_type="transcription.started",
            correlation_id=event.correlation_id,
            causation_id=event.event_id,
            producer=worker_name,
            payload=TranscriptionStartedPayload(
                job_id=requested.job_id,
                track_version_id=requested.track_version_id,
                worker_id=worker_name,
                engine="mock",
                message="Mock transcription started",
            ),
        ),
        requested.job_id,
    )

    for progress in (10, 30, 60, 90):
        await asyncio.sleep(step_delay_seconds)
        await producer.publish(
            EventEnvelope(
                event_type="transcription.progress",
                correlation_id=event.correlation_id,
                causation_id=event.event_id,
                producer=worker_name,
                payload=TranscriptionProgressPayload(
                    job_id=requested.job_id,
                    track_version_id=requested.track_version_id,
                    progress=progress,
                    stage="mock_processing",
                    message=f"Mock processing {progress}% complete",
                ),
            ),
            requested.job_id,
        )
        if should_fail:
            await producer.publish(
                EventEnvelope(
                    event_type="transcription.failed",
                    correlation_id=event.correlation_id,
                    causation_id=event.event_id,
                    producer=worker_name,
                    payload=TranscriptionFailedPayload(
                        job_id=requested.job_id,
                        track_version_id=requested.track_version_id,
                        error_code="mock_failure",
                        error_message="Mock worker failed intentionally",
                        retryable=True,
                    ),
                ),
                requested.job_id,
            )
            return

    await asyncio.sleep(step_delay_seconds)
    await producer.publish(
        EventEnvelope(
            event_type="transcription.completed",
            correlation_id=event.correlation_id,
            causation_id=event.event_id,
            producer=worker_name,
            payload=TranscriptionCompletedPayload(
                job_id=requested.job_id,
                track_version_id=requested.track_version_id,
                message="Mock transcription completed",
            ),
        ),
        requested.job_id,
    )


async def run_worker() -> None:
    settings = get_settings()
    consumer_config = ConsumerConfig.from_settings(settings)
    producer = EventProducer(EventProducerConfig.from_settings(settings))

    pipeline = None
    if not settings.worker_mock_mode:
        engine = create_engine(settings)
        engine.ensure_available()
        storage = create_storage_client(settings)
        pipeline = build_pipeline(settings, storage, engine, producer)

    await producer.start()
    try:
        async for event in consume_requested_events(consumer_config):
            if not running:
                break
            logger.info(
                "consumed event",
                extra={
                    "event_id": str(event.event_id),
                    "event_type": event.event_type,
                    "consumer_group": consumer_config.group_id,
                    "result": "processing",
                },
            )
            if pipeline is not None:
                await pipeline.handle_requested(event)
            else:
                await process_requested_event(
                    event,
                    producer,
                    settings.worker_name,
                    settings.worker_mock_should_fail,
                    settings.worker_mock_step_delay_seconds,
                )
    finally:
        await producer.stop()


def main() -> None:
    signal.signal(signal.SIGTERM, stop_worker)
    signal.signal(signal.SIGINT, stop_worker)

    settings = get_settings()
    consumer_config = ConsumerConfig.from_settings(settings)
    health = get_health(settings.worker_name, settings.app_env)

    logger.info(
        "worker ready",
        extra={
            "service": health.service,
            "environment": health.environment,
            "kafka_bootstrap_servers": consumer_config.bootstrap_servers,
            "mode": "mock" if settings.worker_mock_mode else "whisper.cpp",
        },
    )

    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
