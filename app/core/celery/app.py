import os
from datetime import UTC, datetime
from celery import Celery
from dotenv import load_dotenv
import whisper
from container.config import get_config
from database.connection import Database
from database.model.transcription_job import TranscriptionStatus
from repository.storage_repository import StorageRepository
from transcriber.transcriber import Transcriber

load_dotenv()

# Create the Celery app
app = Celery(
    "sounds-right",
    broker=os.getenv("REDIS_URL", "redis://redis:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://redis:6379/0"),
)

# Configure Celery
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Configure task queues
app.conf.task_routes = {
    "transcribe_audio": {"queue": "transcription"},
    "high_priority_task": {"queue": "high_priority"},
    "default_task": {"queue": "default"},
}

# Configure task queues with their own settings
app.conf.task_queues = {
    "transcription": {
        "exchange": "transcription",
        "routing_key": "transcription",
    },
    "high_priority": {
        "exchange": "high_priority",
        "routing_key": "high_priority",
    },
    "default": {
        "exchange": "default",
        "routing_key": "default",
    },
}

@app.task(name="transcribe_audio", bind=True)
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

        model = whisper.load_model("base")
        transcriber = Transcriber(model)

        result = transcriber.transcribe_audio(local_audio_path, lyrics)

        if os.path.exists(local_audio_path):
            os.remove(local_audio_path)

        job.status = TranscriptionStatus.COMPLETED
        job.result = result
        job.updated_at = datetime.now(UTC)
        db.update_transcription_job(job)

        return result

    except Exception as e:
        if "job" in locals():
            job.status = TranscriptionStatus.FAILED
            job.error = str(e)
            job.updated_at = datetime.now(UTC)
            db.update_transcription_job(job)

        if "local_audio_path" in locals() and os.path.exists(local_audio_path):
            os.remove(local_audio_path)

        raise

@app.task(queue="high_priority")
def high_priority_task(data):
    return f"Processed high priority task: {data}"

@app.task(queue="default")
def default_task(data):
    return f"Processed default task: {data}" 

if __name__ == "__main__":
    app.start()