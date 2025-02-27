from database.model.transcription_job import TranscriptionStatus
from formatter.api_response_formatter import ApiResponseFormatter
from service.transcription_service import TranscriptionService
from database.connection import Database


class TranscriptionController:
    def __init__(
        self,
        db: Database,
        transcription_service: TranscriptionService,
        res_formatter: ApiResponseFormatter,
    ):
        self.db = db
        self.transcription_service = transcription_service
        self.res_formatter = res_formatter

    def validate_transcription_data(self, request):
        """Validate and process transcription request data."""
        # Get metadata from form data
        artist = request.form.get("artist")
        album = request.form.get("album")
        title = request.form.get("title")
        audio_file = request.files.get("audio")

        if not artist:
            return (
                self.res_formatter.with_errors("No artist provided")
                .with_status(400)
                .response()
            )
        if not album:
            return (
                self.res_formatter.with_errors("No album provided")
                .with_status(400)
                .response()
            )
        if not title:
            return (
                self.res_formatter.with_errors("No title provided")
                .with_status(400)
                .response()
            )

        # Validate audio file
        error = self.transcription_service.validate_audio_file(audio_file)
        if error:
            return self.res_formatter.with_errors(error).with_status(400).response()

        lyrics_file = request.files.get("lyrics")
        if lyrics_file:
            error = self.transcription_service.validate_lyrics_file(lyrics_file)
            if error:
                return self.res_formatter.with_errors(error).with_status(400).response()

        try:
            job = self.transcription_service.create_transcription_job(
                artist=artist,
                album=album,
                title=title,
                audio_file=audio_file,
                lyrics_file=lyrics_file,
            )

            return (
                self.res_formatter.with_data(
                    {
                        "job_id": job.id,
                        "status": job.status.value,
                        "message": "Transcription job started",
                    }
                )
                .with_status(202)
                .response()
            )

        except Exception as e:
            return self.res_formatter.with_exception(e).response()

    def get_transcription_status(self, job_id: str):
        """Get the status of a transcription job."""
        job = self.transcription_service.get_transcription_job(job_id)
        if not job:
            return (
                self.res_formatter.with_errors("Transcription job not found")
                .with_status(404)
                .response()
            )

        response_data = {
            "job_id": job.id,
            "status": job.status.value,
            "created_at": job.created_at.isoformat(),
            "updated_at": job.updated_at.isoformat(),
            "version": job.version,
            "artist": job.artist,
            "album": job.album,
            "title": job.title,
        }

        if job.status == TranscriptionStatus.COMPLETED:
            response_data["result"] = job.result
        elif job.status == TranscriptionStatus.FAILED:
            response_data["error"] = job.error

        return self.res_formatter.with_data(response_data).response()

    def approve_transcription(self, job_id: str):
        """Approve transcription by updating its status in MongoDB using job_id."""
        try:
            job = self.transcription_service.approve_transcription(job_id)

            if not job:
                return (
                    self.res_formatter.with_errors(
                        f"No completed transcription found for job ID: {job_id}"
                    )
                    .with_status(404)
                    .response()
                )

            return (
                self.res_formatter.with_data(
                    {
                        "message": "Transcription approved successfully",
                        "job_id": job["id"],
                    }
                )
                .with_status(200)
                .response()
            )

        except Exception as e:
            return self.res_formatter.with_exception(e).response()
