from datetime import datetime, timezone

from bson import ObjectId
from pymongo import MongoClient
from pymongo.errors import PyMongoError


class MongoDatabase:
    """Owns the MongoDB client and exposes a startup ping."""

    def __init__(self, uri: str) -> None:
        self.uri = uri
        self.client: MongoClient | None = None

    def connect(self) -> None:
        if not self.uri:
            raise RuntimeError("MONGODB_URI is not set")

        client = MongoClient(
            self.uri,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000,
            timeoutMS=15000,
        )
        try:
            result = client.admin.command("ping")
        except PyMongoError:
            client.close()
            raise

        if result.get("ok") != 1:
            client.close()
            raise RuntimeError("MongoDB ping was not successful")

        self.client = client

    def close(self) -> None:
        if self.client is not None:
            self.client.close()
            self.client = None

    @property
    def is_connected(self) -> bool:
        return self.client is not None

    @property
    def db(self):
        if self.client is None:
            raise RuntimeError("MongoDatabase is not connected")
        return self.client.get_default_database()

    def insert_call(self, document: dict) -> str:
        result = self.db["calls"].insert_one(document)
        return str(result.inserted_id)

    def set_conversation_id(self, call_id: ObjectId, conversation_id: str) -> bool:
        result = self.db["calls"].update_one(
            {"_id": call_id},
            {
                "$set": {
                    "conversation_id": conversation_id,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        return result.matched_count > 0
