from datetime import UTC, datetime

from bson.objectid import ObjectId
from werkzeug.security import check_password_hash, generate_password_hash

from database.connection import Database


class User:
    def __init__(
        self,
        db: Database,
        username: str,
        email: str,
        password: str = None,
        is_active: bool = True,
        is_admin: bool = False,
        _id=None,
        created_at=None,
        updated_at=None,
    ):
        self._id = _id if _id else ObjectId()
        self.username = username
        self.email = email
        self.password_hash = generate_password_hash(password) if password else None
        self.is_active = is_active
        self.is_admin = is_admin
        self.created_at = created_at if created_at else datetime.now(UTC)
        self.updated_at = updated_at if updated_at else datetime.now(UTC)
        self.collection = db.user_collection
        self.collection.create_index("username", unique=True)
        self.collection.create_index("email", unique=True)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def save(self):
        user_data = {
            "username": self.username,
            "email": self.email,
            "password_hash": self.password_hash,
            "is_active": self.is_active,
            "is_admin": self.is_admin,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if not self._id:
            self._id = self.collection.insert_one(user_data).inserted_id
        else:
            self.collection.update_one(
                {"_id": self._id},
                {"$set": {**user_data, "updated_at": datetime.now(UTC)}},
            )

    def delete(self):
        self.collection.delete_one({"_id": self._id})

    def to_dict(self, include_sensitive=False):
        data = {
            "_id": str(self._id),
            "username": self.username,
            "email": self.email,
            "is_active": self.is_active,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if include_sensitive:
            data["password_hash"] = self.password_hash
        return data

    @staticmethod
    def get_by_username(db: Database, username: str):
        data = db.user_collection.find_one({"username": username})
        if data:
            return User(db=db, password=None, **data)
        return None

    @staticmethod
    def get_by_email(db: Database, email: str):
        data = db.user_collection.find_one({"email": email})
        if data:
            return User(db=db, password=None, **data)
        return None

    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"
