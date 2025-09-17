"""Service for handling connection to MongoDB."""

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import ConnectionFailure

HOST = "mongodb"
PORT = "27017"

DATABASE_NAME = "miskatonic"


class ServiceMongo:
    """Static class for handling MongoDB."""

    client: MongoClient

    @classmethod
    def connect(cls) -> None:
        """Create MongoClient."""
        try:
            cls.client = MongoClient(host=HOST, port=PORT, connect=True)
        except ConnectionFailure as e:
            raise RuntimeError from e

    @classmethod
    def disconnect(cls) -> None:
        """Close MongoClient."""
        cls.client.close()

    @classmethod
    def get_collection(cls, name: str) -> Collection:
        """Get MongoDB collection by {name}."""
        database = cls.get_database()
        return database.get_collection(name=name)

    @classmethod
    def get_database(cls) -> Database:
        """Get MongoDB database."""
        return cls.client.get_database(DATABASE_NAME)
