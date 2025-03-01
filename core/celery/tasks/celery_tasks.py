import os
from datetime import UTC, datetime

import whisper

from core.celery.celery_app import celery
from core.celery.celery_config import app
from container.config import get_config
from database.connection import Database
from database.model.transcription_job import TranscriptionStatus
from repository.storage_repository import StorageRepository
from transcriber.transcriber import Transcriber


@celery.task(name="transcribe_audio", bind=True)
def transcribe_audio(self, job_id: str, audio_file_path: str, lyrics: str = None):
    try:
        config = get_config()
        db = Database(config)
        storage = StorageRepository()

        # Update job status to processing
        job = db.get_transcription_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        job.status = TranscriptionStatus.PROCESSING
        job.updated_at = datetime.now(UTC)
        db.update_transcription_job(job)

        # Download the file locally
        local_audio_path = storage.download_file(audio_file_path)
        if not os.path.exists(local_audio_path):
            raise FileNotFoundError(f"Downloaded file not found at {local_audio_path}")

        # Initialize transcriber
        model = whisper.load_model("base")
        transcriber = Transcriber(model)

        # Perform transcription
        result = transcriber.transcribe_audio(local_audio_path, lyrics)

        # Clean up the temporary file
        if os.path.exists(local_audio_path):
            os.remove(local_audio_path)

        # Update job with success and store result in MongoDB
        job.status = TranscriptionStatus.COMPLETED
        job.result = result
        job.updated_at = datetime.now(UTC)
        db.update_transcription_job(job)

        return result

    except Exception as e:
        # Update job with error
        if "job" in locals():
            job.status = TranscriptionStatus.FAILED
            job.error = str(e)
            job.updated_at = datetime.now(UTC)
            db.update_transcription_job(job)

        # Clean up the temporary file if it exists
        if "local_audio_path" in locals() and os.path.exists(local_audio_path):
            os.remove(local_audio_path)

        raise


@app.task(queue="high_priority")
def high_priority_task(data):
    # Your high priority task logic
    return f"Processed high priority task: {data}"


@app.task(queue="default")
def default_task(data):
    # Your default task logic
    return f"Processed default task: {data}"
