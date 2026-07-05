import uuid
from datetime import UTC, datetime

from markupsafe import escape

from database.connection import Database
from database.model.transcription_job import TranscriptionJob, TranscriptionStatus
from repository.storage_repository import StorageRepository
from core.rabbitmq.client import RabbitMQClient


class TranscriptionService:
    def __init__(self, db: Database, storage_repository: StorageRepository, rabbitmq_client: RabbitMQClient):
        self.db = db
        self.storage_repository = storage_repository
        self.rabbitmq_client = rabbitmq_client

    def validate_audio_file(self, audio_file):
        """Validate audio file format and size."""
        if not audio_file:
            return "No audio file provided"

        allowed_extensions = {"wav", "mp3", "flac"}
        if (
            "." in audio_file.filename
            and audio_file.filename.rsplit(".", 1)[1].lower() not in allowed_extensions
        ):
            return "Invalid audio file extension"

        audio_data = audio_file.read()
        if len(audio_data) == 0:
            return "Audio file is empty"
        if len(audio_data) > 100 * 1024 * 1024:  # 100 MB limit
            return "Audio file is too large"
        if audio_file.content_type not in [
            "audio/wav",
            "audio/mp3",
            "audio/flac",
            "audio/mpeg",
        ]:
            return "Invalid audio file format"

        audio_file.seek(0)
        return None

    def validate_lyrics_file(self, lyrics_file):
        """Validate lyrics file format."""
        if lyrics_file.content_type != "text/plain":
            return "Lyrics file must be a text file"
        if (
            "." in lyrics_file.filename
            and lyrics_file.filename.rsplit(".", 1)[1].lower() != "txt"
        ):
            return "Lyrics file must have a .txt extension"
        return None

    def create_transcription_job(
        self, artist: str, album: str, title: str, audio_file, lyrics_file=None
    ):
        """Create and initiate a new transcription job."""
        artist = escape(artist)
        album = escape(album)
        title = escape(title)

        lyrics = None
        if lyrics_file:
            lyrics = lyrics_file.read().decode("utf-8")
            lyrics_file.seek(0)
            self.storage_repository.upload_file(lyrics_file, artist, album, title)

        # Upload the audio file
        audio_url = self.storage_repository.upload_file(
            audio_file, artist, album, title
        )

        # Create a new transcription job
        job_id = str(uuid.uuid4())

        # Get the latest version for this song
        latest_job = self.db.transcription_data_collection.find_one(
            {
                "artist": artist,
                "album": album,
                "title": title,
            },
            sort=[("version", -1)],
        )
        version = (latest_job.get("version", 0) + 1) if latest_job else 1

        job = TranscriptionJob(
            id=job_id,
            artist=artist,
            album=album,
            title=title,
            audio_url=audio_url,
            status=TranscriptionStatus.PENDING,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version=version,
        )
        self.db.create_transcription_job(job)

        # Send the transcription task to RabbitMQ
        message = {
            "job_id": job_id,
            "audio_url": audio_url,
            "lyrics": lyrics,
            "task": "transcribe_audio"
        }
        
        # Publish the message to RabbitMQ
        self.rabbitmq_client.publish_message(
            exchange="transcription",
            routing_key="transcription",
            message=message
        )

        return job

    def get_transcription_job(self, job_id: str):
        """Get a transcription job by ID."""
        return self.db.get_transcription_job(job_id)

    def approve_transcription(self, job_id: str):
        """Approve a transcription by updating its status."""
        job = self.db.get_transcription_job(job_id)
        
        if not job or job.status != TranscriptionStatus.COMPLETED:
            return None
            
        # Update job status logic here
        # This is a placeholder for the actual implementation
        
        return {"id": job_id}
