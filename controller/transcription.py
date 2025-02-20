import uuid
from datetime import datetime, UTC
from werkzeug.utils import secure_filename
from markupsafe import escape
from database.connection import Database
from database.model.transcription_job import TranscriptionJob, TranscriptionStatus
from formatter.api_response_formatter import ApiResponseFormatter
from transcriber.transcriber import Transcriber
from repository.storage_repository import StorageRepository
from tasks import transcribe_audio


class TranscriptionController:
    def __init__(self, db: Database, res_formatter: ApiResponseFormatter, transcriber: Transcriber):
        self.db = db
        self.res_formatter = res_formatter
        self.transcriber = transcriber
        self.storage_repository = StorageRepository()

    def _validate_audio_file(self, audio_file):
        """Validate audio file format and size."""
        if not audio_file:
            return self.res_formatter.with_errors("No audio file provided").with_status(400).response()

        allowed_extensions = {'wav', 'mp3', 'flac'}
        if ('.' in audio_file.filename and
                audio_file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions):
            return self.res_formatter.with_errors("Invalid audio file extension").with_status(400).response()

        audio_data = audio_file.read()
        if len(audio_data) == 0:
            return self.res_formatter.with_errors("Audio file is empty").with_status(400).response()
        if len(audio_data) > 100 * 1024 * 1024:  # 100 MB limit
            return self.res_formatter.with_errors("Audio file is too large").with_status(400).response()
        if audio_file.content_type not in ['audio/wav', 'audio/mp3', 'audio/flac', 'audio/mpeg']:
            return self.res_formatter.with_errors("Invalid audio file format").with_status(400).response()

        audio_file.seek(0)
        return None

    def _validate_lyrics_file(self, lyrics_file):
        """Validate lyrics file format."""
        if lyrics_file.content_type != 'text/plain':
            return self.res_formatter.with_errors("Lyrics file must be a text file").with_status(400).response()
        if ('.' in lyrics_file.filename and
                lyrics_file.filename.rsplit('.', 1)[1].lower() != 'txt'):
            return self.res_formatter.with_errors(
                "Lyrics file must have a .txt extension"
            ).with_status(400).response()
        return None

    def validate_transcription_data(self, request):
        """Validate and process transcription request data."""
        # Get metadata from form data
        artist = request.form.get("artist")
        album = request.form.get("album")
        title = request.form.get("title")
        audio_file = request.files.get("audio")
        lyrics = None

        if not artist:
            return self.res_formatter.with_errors("No artist provided").with_status(400).response()
        if not album:
            return self.res_formatter.with_errors("No album provided").with_status(400).response()
        if not title:
            return self.res_formatter.with_errors("No title provided").with_status(400).response()

        error_response = self._validate_audio_file(audio_file)
        if error_response:
            return error_response

        if "lyrics" in request.files:
            lyrics_file = request.files["lyrics"]
            error_response = self._validate_lyrics_file(lyrics_file)
            if error_response:
                return error_response

            lyrics = lyrics_file.read().decode("utf-8")
            lyrics_file.seek(0)
            self.storage_repository.upload_file(lyrics_file, artist, album, title)

        artist = escape(artist)
        album = escape(album)
        title = escape(title)

        try:
            # Upload the audio file
            audio_url = self.storage_repository.upload_file(audio_file, artist, album, title)

            # Create a new transcription job
            job_id = str(uuid.uuid4())
            job = TranscriptionJob(
                id=job_id,
                artist=artist,
                album=album,
                title=title,
                audio_url=audio_url,
                status=TranscriptionStatus.PENDING,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
            self.db.create_transcription_job(job)

            # Start the transcription task asynchronously
            transcribe_audio.delay(job_id, audio_url, lyrics)

            return self.res_formatter.with_data({
                "job_id": job_id,
                "status": TranscriptionStatus.PENDING.value,
                "message": "Transcription job started"
            }).with_status(202).response()

        except Exception as e:
            return self.res_formatter.with_exception(e).response()

    def get_transcription_status(self, job_id: str):
        """Get the status of a transcription job."""
        job = self.db.get_transcription_job(job_id)
        if not job:
            return self.res_formatter.with_errors("Transcription job not found").with_status(404).response()

        response_data = {
            "job_id": job.id,
            "status": job.status.value,
            "created_at": job.created_at.isoformat(),
            "updated_at": job.updated_at.isoformat()
        }

        if job.status == TranscriptionStatus.COMPLETED:
            response_data["result"] = job.result
        elif job.status == TranscriptionStatus.FAILED:
            response_data["error"] = job.error

        return self.res_formatter.with_data(response_data).response()

    def approve_transcription(self, artist: str, album: str, title: str, version: int):
        """Approve and move transcription files to production bucket."""
        try:
            artist = artist.strip()
            album = album.strip()
            title = title.strip()

            moved_files = self.storage_repository.move_approved_transcription(artist, album, title, version)
            
            return self.res_formatter.with_data({
                "message": "Transcription approved and moved successfully",
                "files": moved_files
            }).with_status(200).response()

        except FileNotFoundError as e:
            return self.res_formatter.with_errors(str(e)).with_status(404).response()
        except Exception as e:
            return self.res_formatter.with_exception(e).response()
