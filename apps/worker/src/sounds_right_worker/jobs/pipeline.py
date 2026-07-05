from __future__ import annotations

import asyncio

from sounds_right_worker.audio.ffmpeg import normalize_to_wav
from sounds_right_worker.audio.ffprobe import probe_audio
from sounds_right_worker.audio.validation import AudioLimits, validate_audio
from sounds_right_worker.config import WorkerSettings
from sounds_right_worker.errors import (
    ARTIFACT_UPLOAD_FAILED,
    AUDIO_DOWNLOAD_FAILED,
    AUDIO_NOT_FOUND,
    UNKNOWN_WORKER_ERROR,
    UNSUPPORTED_OPTION,
    PipelineError,
)
from sounds_right_worker.events.producer import EventProducer
from sounds_right_worker.events.schemas import EventEnvelope, TranscriptionRequestedPayload
from sounds_right_worker.jobs.cleanup import delete_temp_audio
from sounds_right_worker.jobs.pipeline_events import PipelineEventPublisher
from sounds_right_worker.jobs.tempdir import JobTempDir
from sounds_right_worker.logging import get_logger
from sounds_right_worker.storage.minio_client import (
    ObjectNotFoundError,
    StorageClient,
    StorageError,
)
from sounds_right_worker.storage.object_keys import (
    input_extension,
    manifest_object_key,
    transcript_object_key,
)
from sounds_right_worker.transcription.manifest import build_manifest, compute_sha256
from sounds_right_worker.transcription.parser import build_transcript
from sounds_right_worker.transcription.schemas import TranscriptionOptions
from sounds_right_worker.transcription.whisper_cpp import WhisperCppEngine

logger = get_logger(__name__)


class TranscriptionPipeline:
    def __init__(
        self,
        settings: WorkerSettings,
        storage: StorageClient,
        engine: WhisperCppEngine,
        producer: EventProducer,
    ) -> None:
        self._settings = settings
        self._storage = storage
        self._engine = engine
        self._producer = producer
        self._events = PipelineEventPublisher(settings, producer)

    async def handle_requested(self, event: EventEnvelope) -> None:
        payload = event.payload
        if not isinstance(payload, TranscriptionRequestedPayload):
            logger.error("pipeline received non-requested event")
            return

        log_context = {
            "job_id": str(payload.job_id),
            "track_version_id": str(payload.track_version_id),
            "correlation_id": str(event.correlation_id),
            "event_id": str(event.event_id),
        }
        logger.info("received transcription.requested", extra=log_context)

        await self._events.started(event, payload)

        try:
            await self._run(event, payload, log_context)
        except PipelineError as exc:
            logger.warning(
                "transcription failed",
                extra={**log_context, "stage": exc.stage, "error_code": exc.error_code},
            )
            await self._events.failed(event, payload, exc)
        except Exception:
            logger.exception("unexpected worker error", extra=log_context)
            await self._events.failed(
                event,
                payload,
                PipelineError(
                    UNKNOWN_WORKER_ERROR,
                    "An unexpected error occurred during transcription",
                    stage="unknown",
                ),
            )

    async def _run(
        self,
        event: EventEnvelope,
        payload: TranscriptionRequestedPayload,
        log_context: dict[str, str],
    ) -> None:
        if payload.options.separate_vocals:
            raise PipelineError(
                UNSUPPORTED_OPTION,
                "Vocal separation is not supported yet",
                stage="options",
            )

        settings = self._settings
        transcript_key = transcript_object_key(
            settings.transcript_object_prefix,
            payload.track_version_id,
        )
        manifest_key = manifest_object_key(
            settings.transcript_object_prefix,
            payload.track_version_id,
        )

        # Idempotency: if a transcript already exists, re-emit completion.
        if await self._transcript_exists(transcript_key):
            logger.info("transcript already exists, skipping", extra=log_context)
            await self._events.completed_from_existing(event, payload, transcript_key, manifest_key)
            await delete_temp_audio(
                self._storage,
                settings.minio_temp_audio_bucket,
                payload.audio_object_key,
            )
            return

        with JobTempDir(
            settings.worker_temp_root,
            payload.job_id,
            keep_files=settings.worker_keep_temp_files,
        ) as temp:
            extension = input_extension(payload.audio_object_key)
            input_original = temp.file(f"input_original.{extension}")
            input_wav = temp.file("input.wav")

            # Download audio
            try:
                await asyncio.to_thread(
                    self._storage.download_to_path,
                    settings.minio_temp_audio_bucket,
                    payload.audio_object_key,
                    input_original,
                )
            except ObjectNotFoundError as exc:
                raise PipelineError(
                    AUDIO_NOT_FOUND,
                    "Uploaded audio could not be found",
                    stage="audio_download",
                ) from exc
            except StorageError as exc:
                raise PipelineError(
                    AUDIO_DOWNLOAD_FAILED,
                    "Could not download uploaded audio",
                    stage="audio_download",
                ) from exc
            logger.info("downloaded audio", extra=log_context)
            await self._events.progress(event, payload, 10, "audio_downloaded")

            # Validate audio
            probe = await probe_audio(settings.ffprobe_path, input_original)
            validate_audio(
                probe,
                AudioLimits(
                    max_size_bytes=settings.max_audio_size_bytes,
                    max_duration_seconds=settings.max_audio_duration_seconds,
                ),
            )
            logger.info("validated audio", extra=log_context)
            await self._events.progress(event, payload, 20, "audio_validated")

            # Normalize audio
            await normalize_to_wav(settings.ffmpeg_path, input_original, input_wav)
            logger.info("normalized audio", extra=log_context)
            await self._events.progress(event, payload, 30, "audio_normalized")

            # Transcribe
            options = TranscriptionOptions(
                language=payload.options.language,
                model=payload.options.model,
                separate_vocals=payload.options.separate_vocals,
            )
            await self._events.progress(event, payload, 40, "transcription_started")
            logger.info("started whisper.cpp", extra=log_context)
            result = await self._engine.transcribe(input_wav, temp.path, options)
            logger.info("finished whisper.cpp", extra=log_context)
            await self._events.progress(event, payload, 80, "transcription_finished")

            # Build artifacts
            transcript = build_transcript(
                result,
                schema_version=settings.transcript_schema_version,
                track_version_id=payload.track_version_id,
                job_id=payload.job_id,
                engine_name=payload.engine,
                model=settings.whisper_model_name,
                duration_seconds=probe.duration_seconds,
            )
            transcript_bytes = transcript.model_dump_json(indent=2).encode("utf-8")
            transcript_sha256 = compute_sha256(transcript_bytes)

            manifest = build_manifest(
                schema_version=settings.transcript_schema_version,
                transcript=transcript,
                transcript_object_key=transcript_key,
                transcript_sha256=transcript_sha256,
                probe=probe,
            )
            manifest_bytes = manifest.model_dump_json(indent=2).encode("utf-8")

            # Upload artifacts
            try:
                await asyncio.to_thread(
                    self._storage.upload_json,
                    settings.minio_transcripts_bucket,
                    transcript_key,
                    transcript_bytes,
                )
                logger.info("uploaded transcript", extra=log_context)
                await asyncio.to_thread(
                    self._storage.upload_json,
                    settings.minio_transcripts_bucket,
                    manifest_key,
                    manifest_bytes,
                )
                logger.info("uploaded manifest", extra=log_context)
            except StorageError as exc:
                raise PipelineError(
                    ARTIFACT_UPLOAD_FAILED,
                    "Could not upload transcript artifacts",
                    stage="artifact_upload",
                ) from exc
            await self._events.progress(event, payload, 90, "artifacts_uploaded")

            # Cleanup temp audio from MinIO (best effort)
            deleted = await delete_temp_audio(
                self._storage,
                settings.minio_temp_audio_bucket,
                payload.audio_object_key,
            )
            if deleted:
                logger.info("deleted temporary audio", extra=log_context)

            await self._events.completed(
                event,
                payload,
                transcript_object_key=transcript_key,
                manifest_object_key=manifest_key,
                duration_seconds=probe.duration_seconds,
                word_count=transcript.metadata.word_count,
                segment_count=transcript.metadata.segment_count,
                language=transcript.engine.language,
                sha256=transcript_sha256,
            )
            logger.info("emitted completed", extra=log_context)

    async def _transcript_exists(self, transcript_key: str) -> bool:
        try:
            return await asyncio.to_thread(
                self._storage.object_exists,
                self._settings.minio_transcripts_bucket,
                transcript_key,
            )
        except StorageError:
            return False


def build_pipeline(
    settings: WorkerSettings,
    storage: StorageClient,
    engine: WhisperCppEngine,
    producer: EventProducer,
) -> TranscriptionPipeline:
    return TranscriptionPipeline(settings, storage, engine, producer)
