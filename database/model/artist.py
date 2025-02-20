from pymongo import MongoClient
from bson.objectid import ObjectId
from database.connection import Database

class Artist:
    def __init__(self, db: Database, pseudonym, fullname, genre=None, _id=None):
        self._id = _id if _id else ObjectId()
        self.pseudonym = pseudonym
        self.fullname = fullname
        self.genre = genre
        self.collection = db.artist_data_collection
        self.collection.create_index("pseudonym", unique=True)

    def save(self):
        artist_data = {
            "pseudonym": self.pseudonym,
            "fullname": self.fullname,
            "genre": self.genre
        }
        self.collection.insert_one(artist_data)

    def delete(self):
        self.collection.delete_one({'_id': self._id})

    def to_dict(self):
        return {
            "_id": str(self._id),
            "pseudonym": self.pseudonym,
            "fullname": self.fullname,
            "genre": self.genre
        }

    @staticmethod
    def get_by_pseudonym(db: Database, pseudonym):
        data = db.artist_data_collection.find_one({'pseudonym': pseudonym})
        if data:
            return Artist(db=db, **data)
        return None

    def __repr__(self):
        return f"<Artist(pseudonym='{self.pseudonym}', fullname='{self.fullname}', genre='{self.genre}')>"