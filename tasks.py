from celery_app import celery
from transcriber.transcriber import Transcriber
from database.model.transcription_job import TranscriptionStatus
from database.connection import Database
from repository.storage_repository import StorageRepository
import whisper
import os
import json
from datetime import datetime, UTC
from io import BytesIO

@celery.task(name='transcribe_audio', bind=True)
def transcribe_audio(self, job_id: str, audio_file_path: str, lyrics: str = None):
    try:
        db = Database()
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

        # Save transcription result to GCS
        # Extract artist, album, and title from the job
        json_data = BytesIO(json.dumps(result, indent=4).encode('utf-8'))
        json_data.seek(0)
        storage.upload_file_object(
            json_data, 
            job.artist, 
            job.album, 
            job.title, 
            'transcription.json',
            'application/json'
        )

        # Clean up the temporary file
        if os.path.exists(local_audio_path):
            os.remove(local_audio_path)

        # Update job with success
        job.status = TranscriptionStatus.COMPLETED
        job.result = result
        job.updated_at = datetime.now(UTC)
        db.update_transcription_job(job)

        return result

    except Exception as e:
        # Update job with error
        if 'job' in locals():
            job.status = TranscriptionStatus.FAILED
            job.error = str(e)
            job.updated_at = datetime.now(UTC)
            db.update_transcription_job(job)
        
        # Clean up the temporary file if it exists
        if 'local_audio_path' in locals() and os.path.exists(local_audio_path):
            os.remove(local_audio_path)
            
        raise
