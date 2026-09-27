from datetime import datetime, timezone

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING, MongoClient, ReturnDocument
from pymongo.errors import PyMongoError


DEFAULT_DATABASE = "phonybusiness"


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
            # Return UTC-aware datetimes so the API serializes them with a timezone.
            tz_aware=True,
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
        self.ensure_indexes()

    def ensure_indexes(self) -> None:
        conversations = self.db["conversations"]
        conversations.create_index("conversation_id", unique=True)
        conversations.create_index("call_id")
        conversations.create_index([("started_at", DESCENDING)])
        conversations.create_index([("scenario_name", ASCENDING), ("started_at", DESCENDING)])
        self.db["calls"].create_index("conversation_id")

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
        # Fall back to "phonybusiness" when the connection string has no database name.
        return self.client.get_default_database(default=DEFAULT_DATABASE)

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

    def hangup_call(self, call_id: ObjectId) -> dict | None:
        """End the call, filling in outcome='pass' only if no outcome was already recorded."""
        return self.db["calls"].find_one_and_update(
            {"_id": call_id},
            [
                {
                    "$set": {
                        "status": "ended",
                        "updated_at": datetime.now(timezone.utc),
                        "outcome": {"$ifNull": ["$outcome", "pass"]},
                    }
                }
            ],
            return_document=ReturnDocument.AFTER,
        )

    def get_call(self, call_id: ObjectId) -> dict | None:
        return self.db["calls"].find_one({"_id": call_id})

    def record_outcome(
        self, call_id: ObjectId, result: str, flags: list[str], turn: int
    ) -> dict | None:
        """Save the live outcome reported by the agent mid-call. Always authoritative."""
        return self.db["calls"].find_one_and_update(
            {"_id": call_id},
            {
                "$set": {
                    "outcome": result,
                    "flags": flags,
                    "turn": turn,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
            return_document=ReturnDocument.AFTER,
        )

    def find_call_for_conversation(self, conversation_id: str, call_id: str | None) -> dict | None:
        """Match a webhook to our call by the call_id dynamic variable, else by conversation_id."""
        if call_id and ObjectId.is_valid(call_id):
            call = self.db["calls"].find_one({"_id": ObjectId(call_id)})
            if call is not None:
                return call
        return self.db["calls"].find_one({"conversation_id": conversation_id})

    def save_conversation(self, conversation: dict) -> None:
        """Upsert by conversation_id so webhook retries don't create duplicates."""
        self.db["conversations"].replace_one(
            {"conversation_id": conversation["conversation_id"]}, conversation, upsert=True
        )

    def close_call_from_webhook(self, call_id: ObjectId, conversation: dict) -> None:
        """Mark the call ended; fill in the outcome from the webhook only if none was recorded live."""
        outcome = conversation.get("outcome") or {}
        self.db["calls"].update_one(
            {"_id": call_id},
            [
                {
                    "$set": {
                        "status": "ended",
                        "conversation_id": conversation["conversation_id"],
                        "outcome": {"$ifNull": ["$outcome", outcome.get("result")]},
                        "flags": {"$ifNull": ["$flags", outcome.get("flags")]},
                        "updated_at": datetime.now(timezone.utc),
                    }
                }
            ],
        )

    def get_conversation(self, conversation_id: str) -> dict | None:
        return self.db["conversations"].find_one({"conversation_id": conversation_id}, {"_id": 0})

    def save_score(self, conversation_id: str, call_id: str | None, score: dict) -> None:
        """Store Gemini's rating on the conversation and, when linked, on the call for the recap."""
        self.db["conversations"].update_one(
            {"conversation_id": conversation_id},
            {"$set": {"score": score["rating"], "gemini": score}},
        )
        if call_id and ObjectId.is_valid(call_id):
            self.db["calls"].update_one(
                {"_id": ObjectId(call_id)},
                {"$set": {"score": score["rating"], "updated_at": datetime.now(timezone.utc)}},
            )
