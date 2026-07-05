import logging
import uuid
from dataclasses import dataclass

from aiokafka import AIOKafkaProducer  # type: ignore[import-untyped]

from sounds_right_api.config import ApiSettings
from sounds_right_api.events.schemas import EventEnvelope

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EventProducerConfig:
    bootstrap_servers: str
    client_id: str
    topic: str

    @classmethod
    def from_settings(cls, settings: ApiSettings) -> "EventProducerConfig":
        return cls(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            client_id=settings.kafka_client_id,
            topic=settings.kafka_topic,
        )


class EventProducer:
    def __init__(self, config: EventProducerConfig) -> None:
        self.config = config
        self._producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self.config.bootstrap_servers,
            client_id=self.config.client_id,
        )
        await self._producer.start()

    async def stop(self) -> None:
        if self._producer is not None:
            await self._producer.stop()
            self._producer = None

    async def publish(self, event: EventEnvelope, key: uuid.UUID) -> None:
        if self._producer is None:
            raise RuntimeError("event producer is not started")

        await self._producer.send_and_wait(
            self.config.topic,
            key=str(key).encode("utf-8"),
            value=event.model_dump_json().encode("utf-8"),
        )
        logger.info(
            "published event",
            extra={
                "event_id": str(event.event_id),
                "event_type": event.event_type,
                "job_id": str(key),
                "producer": event.producer,
                "topic": self.config.topic,
            },
        )
