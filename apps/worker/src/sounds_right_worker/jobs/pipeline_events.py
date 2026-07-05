from sounds_right_worker.config import WorkerSettings
from sounds_right_worker.errors import PipelineError
from sounds_right_worker.events.producer import EventProducer
from sounds_right_worker.events.schemas import (
    EventEnvelope,
    TranscriptionCompletedPayload,
    TranscriptionFailedPayload,
    TranscriptionProgressPayload,
    TranscriptionRequestedPayload,
    TranscriptionStartedPayload,
)


class PipelineEventPublisher:
    def __init__(self, settings: WorkerSettings, producer: EventProducer) -> None:
        self._settings = settings
        self._producer = producer

    async def started(
        self,
        event: EventEnvelope,
        payload: TranscriptionRequestedPayload,
    ) -> None:
        await self._producer.publish(
            self._envelope(
                event,
                "transcription.started",
                TranscriptionStartedPayload(
                    job_id=payload.job_id,
                    track_version_id=payload.track_version_id,
                    worker_id=self._settings.worker_name,
                    engine=payload.engine,
                    message="Transcription started",
                ),
            ),
            payload.job_id,
        )

    async def progress(
        self,
        event: EventEnvelope,
        payload: TranscriptionRequestedPayload,
        progress: int,
        stage: str,
    ) -> None:
        await self._producer.publish(
            self._envelope(
                event,
                "transcription.progress",
                TranscriptionProgressPayload(
                    job_id=payload.job_id,
                    track_version_id=payload.track_version_id,
                    progress=progress,
                    stage=stage,
                    message=f"{stage} ({progress}%)",
                ),
            ),
            payload.job_id,
        )

    async def completed(
        self,
        event: EventEnvelope,
        payload: TranscriptionRequestedPayload,
        *,
        transcript_object_key: str,
        manifest_object_key: str,
        duration_seconds: float | None,
        word_count: int | None,
        segment_count: int | None,
        language: str | None,
        sha256: str | None,
        message: str = "Transcription completed",
    ) -> None:
        await self._producer.publish(
            self._envelope(
                event,
                "transcription.completed",
                TranscriptionCompletedPayload(
                    job_id=payload.job_id,
                    track_version_id=payload.track_version_id,
                    transcript_object_key=transcript_object_key,
                    manifest_object_key=manifest_object_key,
                    duration_seconds=duration_seconds,
                    word_count=word_count,
                    segment_count=segment_count,
                    engine=payload.engine,
                    model=self._settings.whisper_model_name,
                    language=language,
                    sha256=sha256,
                    message=message,
                ),
            ),
            payload.job_id,
        )

    async def completed_from_existing(
        self,
        event: EventEnvelope,
        payload: TranscriptionRequestedPayload,
        transcript_key: str,
        manifest_key: str,
    ) -> None:
        await self.completed(
            event,
            payload,
            transcript_object_key=transcript_key,
            manifest_object_key=manifest_key,
            duration_seconds=None,
            word_count=None,
            segment_count=None,
            language=None,
            sha256=None,
            message="Transcript already existed; re-emitted completion",
        )

    async def failed(
        self,
        event: EventEnvelope,
        payload: TranscriptionRequestedPayload,
        error: PipelineError,
    ) -> None:
        await self._producer.publish(
            self._envelope(
                event,
                "transcription.failed",
                TranscriptionFailedPayload(
                    job_id=payload.job_id,
                    track_version_id=payload.track_version_id,
                    error_code=error.error_code,
                    error_message=error.message,
                    retryable=error.retryable,
                ),
            ),
            payload.job_id,
        )

    def _envelope(
        self,
        event: EventEnvelope,
        event_type: str,
        inner: object,
    ) -> EventEnvelope:
        return EventEnvelope(
            event_type=event_type,  # type: ignore[arg-type]
            correlation_id=event.correlation_id,
            causation_id=event.event_id,
            producer=self._settings.worker_name,
            payload=inner,  # type: ignore[arg-type]
        )
