from typing import Literal

UserRole = Literal["user", "reviewer", "admin"]
TrackVersionStatus = Literal[
    "draft",
    "upload_url_created",
    "uploaded",
    "queued_for_processing",
    "processing",
    "completed",
    "failed",
    "approved",
    "rejected",
    "published",
]
TranscriptionJobStatus = Literal[
    "queued",
    "started",
    "processing",
    "completed",
    "failed",
    "cancelled",
]

ALLOWED_AUDIO_CONTENT_TYPES = {
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/x-wav",
    "audio/flac",
    "audio/ogg",
    "audio/mp4",
}
ALLOWED_AUDIO_EXTENSIONS = {"mp3", "wav", "flac", "m4a", "ogg"}
