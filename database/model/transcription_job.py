from datetime import datetime
from enum import Enum

class TranscriptionStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class TranscriptionJob:
    def __init__(self, id: str, artist: str, album: str, title: str, audio_url: str, status: TranscriptionStatus, created_at: datetime, updated_at: datetime, result: dict = None, error: str = None):
        self.id = id
        self.artist = artist
        self.album = album
        self.title = title
        self.audio_url = audio_url
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at
        self.result = result
        self.error = error

    def to_dict(self):
        return {
            "id": self.id,
            "artist": self.artist,
            "album": self.album,
            "title": self.title,
            "audio_url": self.audio_url,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "result": self.result,
            "error": self.error
        }

    @staticmethod
    def from_dict(data: dict):
        return TranscriptionJob(
            id=data.get("id"),
            artist=data.get("artist"),
            album=data.get("album"),
            title=data.get("title"),
            audio_url=data.get("audio_url"),
            status=TranscriptionStatus(data.get("status")),
            created_at=datetime.fromisoformat(data.get("created_at")),
            updated_at=datetime.fromisoformat(data.get("updated_at")),
            result=data.get("result"),
            error=data.get("error")
        ) 