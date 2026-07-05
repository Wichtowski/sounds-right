import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass

from aiokafka import AIOKafkaConsumer  # type: ignore[import-untyped]

from sounds_right_worker.config import WorkerSettings
from sounds_right_worker.events.schemas import (
    EventEnvelope,
    TranscriptionRequestedPayload,
    event_envelope_adapter,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ConsumerConfig:
    bootstrap_servers: str
    client_id: str
    topic: str
    group_id: str

    @classmethod
    def from_settings(cls, settings: WorkerSettings) -> "ConsumerConfig":
        return cls(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            client_id=settings.kafka_client_id,
            topic=settings.kafka_topic,
            group_id=settings.kafka_worker_consumer_group,
        )


async def consume_requested_events(config: ConsumerConfig) -> AsyncIterator[EventEnvelope]:
    consumer = AIOKafkaConsumer(
        config.topic,
        bootstrap_servers=config.bootstrap_servers,
        client_id=config.client_id,
        group_id=config.group_id,
        auto_offset_reset="earliest",
    )
    await consumer.start()
    try:
        async for message in consumer:
            try:
                event = event_envelope_adapter.validate_json(message.value)
            except Exception:
                logger.exception("skipping malformed event")
                continue
            if event.event_type != "transcription.requested":
                continue
            if not isinstance(event.payload, TranscriptionRequestedPayload):
                logger.error(
                    "requested event has invalid payload",
                    extra={"event_id": str(event.event_id)},
                )
                continue
            yield event
    finally:
        await consumer.stop()
