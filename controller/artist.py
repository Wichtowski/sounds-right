import json
from flask import request, jsonify
from html import escape
from pymongo.errors import DuplicateKeyError
from database.connection import Database
from bson import ObjectId
from database.model.artist import Artist
from urllib.parse import unquote
from formatter.api_response_formatter import ApiResponseFormatter
import os


class ArtistController:
    def __init__(self, db: Database, res_formatter: ApiResponseFormatter):
        self.db = db
        self.res_formatter = res_formatter
        self.UPLOAD_DIR = "/uploads"

    def get_all_artists(self):
        artists = self.db.artist_data_collection.find()
        artists_list = []
        for artist_data in artists:
            artist = Artist(db=self.db, **artist_data)
            artist_dict = artist.to_dict()
            artist_dict["_id"] = str(artist_data["_id"])
            artists_list.append(artist_dict)
        return self.res_formatter.with_data({"artists": artists_list}).response()

    def get_artist(self, pseudonym: str):
        try:
            query = {"_id": ObjectId(pseudonym)}
        except Exception:
            query = {"pseudonym": unquote(pseudonym)}

        artist_data = self.db.artist_data_collection.find_one(query)
        print(artist_data)
        if not artist_data:
            return (
                self.res_formatter.with_errors("Artist not found")
                .with_message("failure")
                .with_status(404)
                .with_additional_data({"pseudonym": pseudonym})
                .response()
            )
        else:
            artist = Artist(db=self.db, **artist_data)
            artist_dict = artist.to_dict()
            artist_dict["_id"] = str(artist_data["_id"])
            return self.res_formatter.with_data(artist_dict).response()

    def create_artist(self, request: json) -> jsonify:
        if request.json and "pseudonym" not in request.json:
            return (
                self.res_formatter.with_errors("No pseudonym provided")
                .with_status(400)
                .response()
            )
        elif request.json and "fullname" not in request.json:
            return (
                self.res_formatter.with_errors("No fullname provided")
                .with_status(400)
                .response()
            )
        elif request.json and "genre" not in request.json:
            return (
                self.res_formatter.with_errors("No genre provided")
                .with_status(400)
                .response()
            )
        elif isinstance(request.json, dict):
            artist_data = request.json
            artist = Artist(
                db=self.db,
                pseudonym=escape(artist_data["pseudonym"]),
                fullname=escape(artist_data["fullname"]),
                genre=escape(artist_data.get("genre")),
            )
            try:
                artist.save()
                artist_dir = os.path.join(self.UPLOAD_DIR, artist.pseudonym)
                os.makedirs(artist_dir, exist_ok=True)

                return (
                    self.res_formatter.with_message("Artist inserted successfully")
                    .with_status(201)
                    .response()
                )
            except DuplicateKeyError:
                return (
                    self.res_formatter.with_errors("Pseudonym already exists")
                    .with_status(400)
                    .response()
                )
        else:
            return (
                self.res_formatter.with_errors("Invalid JSON format")
                .with_status(400)
                .response()
            )

    def delete_artist(self, pseudonym: str):
        try:
            query = {"_id": ObjectId(pseudonym)}
        except Exception:
            query = {"pseudonym": unquote(pseudonym)}

        artist_data = self.db.artist_data_collection.find_one(query)

        if not artist_data:
            return (
                self.res_formatter.with_errors("Artist not found")
                .with_status(404)
                .response()
            )
        else:
            artist = Artist(db=self.db, **artist_data)
            artist.delete()
            return (
                self.res_formatter.with_message("Artist deleted successfully")
                .with_status(200)
                .response()
            )

    def force_delete_all_artists(self):
        self.db.artist_data_collection.delete_many({})
        return (
            self.res_formatter.with_message("All artists deleted successfully")
            .with_status(200)
            .response()
        )

    def update_artist(self, pseudonym: str, request: json):
        try:
            query = {"_id": ObjectId(pseudonym)}
        except Exception:
            query = {"pseudonym": unquote(pseudonym)}

        artist_data = self.db.artist_data_collection.find_one(query)

        if not artist_data:
            return (
                self.res_formatter.with_errors("Artist not found")
                .with_status(404)
                .response()
            )
        else:
            artist = Artist(db=self.db, **artist_data)
            artist_data = request.json
            artist.pseudonym = escape(artist_data.get("pseudonym", artist.pseudonym))
            artist.fullname = escape(artist_data.get("fullname", artist.fullname))
            artist.genre = escape(artist_data.get("genre", artist.genre))
            artist.save()
            return (
                self.res_formatter.with_message("Artist updated successfully")
                .with_status(200)
                .response()
            )
