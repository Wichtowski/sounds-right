from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional, Dict, Any, List
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database as MongoDatabase
from database.model.transcription_job import TranscriptionJob


class Database:
    def __init__(self, mongo_uri: str):
        self.mongo_uri = mongo_uri
        self.client: MongoClient = MongoClient(mongo_uri)
        print(f"Connected to MongoDB at {mongo_uri.split('@')[1].split('/')[0]}")
        self.db: MongoDatabase = self.client["sounds_right"]
        self.karaoke_data_collection: Collection = self.db["karaoke_data"]
        self.artist_data_collection: Collection = self.db["artist_data"]
        self.transcription_data_collection: Collection = self.db["transcription_data"]
        self.user_collection: Collection = self.db["users"]

    def insert_transcription(self, transcription: Dict[str, Any]) -> str:
        return str(
            self.transcription_data_collection.insert_one(transcription).inserted_id
        )

    def get_collection(self, name: str) -> Collection:
        return self.db[name]

    def create_transcription_job(self, job: TranscriptionJob) -> TranscriptionJob:
        """Create a new transcription job."""
        self.transcription_data_collection.insert_one(job.to_dict())
        return job

    def get_transcription_job(self, job_id: str) -> Optional[TranscriptionJob]:
        """Get a transcription job by ID."""
        doc = self.transcription_data_collection.find_one({"id": job_id})
        if not doc:
            return None
        return TranscriptionJob.from_dict(doc)

    def update_transcription_job(self, job: TranscriptionJob) -> TranscriptionJob:
        """Update a transcription job."""
        job.updated_at = datetime.now(ZoneInfo("UTC"))
        self.transcription_data_collection.update_one(
            {"id": job.id}, {"$set": job.to_dict()}
        )
        return job

    def get_artist_by_pseudonym(self, pseudonym: str) -> Optional[Dict[str, Any]]:
        """Get artist by pseudonym."""
        doc = self.artist_data_collection.find_one({"pseudonym": pseudonym})
        if not doc:
            return None
        return {
            "id": str(doc["_id"]),
            "pseudonym": doc["pseudonym"],
            "fullname": doc["fullname"],
            "genre": doc["genre"],
        }

    def create_artist(self, artist_data: Dict[str, Any]) -> None:
        """Create a new artist."""
        self.artist_data_collection.insert_one(artist_data)

    def get_all_artists(self) -> List[Dict[str, Any]]:
        """Get all artists."""
        return list(
            self.artist_data_collection.find(
                {}, {"_id": 0, "pseudonym": 1, "fullname": 1, "genre": 1}
            )
        )

    def delete_artist(self, pseudonym: str) -> None:
        """Delete an artist by pseudonym."""
        self.artist_data_collection.delete_one({"pseudonym": pseudonym})

    def delete_all_artists(self) -> None:
        """Delete all artists."""
        self.artist_data_collection.delete_many({})
