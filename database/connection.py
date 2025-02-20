from flask import Flask, request
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from datetime import datetime, UTC
from database.model.transcription_job import TranscriptionJob, TranscriptionStatus

class Database:
    def __init__(self):
        _mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
        self.client = MongoClient(_mongo_uri)
        print(f"Connected to MongoDB at {_mongo_uri}")
        self.db = self.client['sounds_right']
        self.karaoke_data_collection = self.db['karaoke_data']
        self.artist_data_collection = self.db['artist_data']
        self.transcription_data_collection = self.db['transcription_data']

    def insert_transcription(self, transcription):
        return self.collection.insert_one(transcription).inserted_id

    def get_collection(self, name):
        return self.db[name]

    def create_transcription_job(self, job: TranscriptionJob):
        """Create a new transcription job."""
        self.transcription_data_collection.insert_one(job.to_dict())
        return job

    def get_transcription_job(self, job_id: str) -> TranscriptionJob:
        """Get a transcription job by ID."""
        doc = self.transcription_data_collection.find_one({"id": job_id})
        if not doc:
            return None
        return TranscriptionJob.from_dict(doc)

    def update_transcription_job(self, job: TranscriptionJob):
        """Update a transcription job."""
        job.updated_at = datetime.now(UTC)
        self.transcription_data_collection.update_one(
            {"id": job.id},
            {"$set": job.to_dict()}
        )
        return job

    def get_artist_by_pseudonym(self, pseudonym: str):
        """Get artist by pseudonym."""
        doc = self.artist_data_collection.find_one({"pseudonym": pseudonym})
        if not doc:
            return None
        return {
            'id': doc['_id'],
            'pseudonym': doc['pseudonym'],
            'fullname': doc['fullname'],
            'genre': doc['genre']
        }

    def create_artist(self, artist_data: dict):
        """Create a new artist."""
        self.artist_data_collection.insert_one(artist_data)

    def get_all_artists(self):
        """Get all artists."""
        return list(self.artist_data_collection.find({}, {'_id': 0, 'pseudonym': 1, 'fullname': 1, 'genre': 1}))

    def delete_artist(self, pseudonym: str):
        """Delete an artist by pseudonym."""
        self.artist_data_collection.delete_one({"pseudonym": pseudonym})

    def delete_all_artists(self):
        """Delete all artists."""
        self.artist_data_collection.delete_many({})