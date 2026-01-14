"""Repository implementations for MongoDB storage."""

import logging
import time

from fastapi.concurrency import run_in_threadpool
from pymongo import UpdateOne
from pymongo.errors import PyMongoError, DuplicateKeyError
from passlib.context import CryptContext

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserAlreadyExistsError(Exception):
    """Raised when attempting to create an existing user."""


class UserCreateError(Exception):
    """Raised when a user cannot be created."""


class UserLookupError(Exception):
    """Raised when a user cannot be retrieved."""


class MongoRecordsRepository:
    """MongoDB repository for communication records."""

    def __init__(self, db):
        """Bind to the MongoDB records collection."""
        self._records_collection = db["records"]
        self._types_collection = db["types"]

    async def add(self, records):
        """Upsert records into MongoDB."""
        if records:
            ops = [
                UpdateOne({"id": record["id"]}, {"$set": record}, upsert=True)
                for record in records
            ]
            result = await self._records_collection.bulk_write(ops, ordered=False)

            upserted = result.upserted_ids or {}
            if upserted:
                counts = {}
                for record_index in upserted.keys():
                    comm_type = records[record_index]["communicationType"]
                    counts[comm_type] = counts.get(comm_type, 0) + 1
                type_ops = [
                    UpdateOne(
                        {"type": comm_type},
                        {"$inc": {"count": count}},
                        upsert=True,
                    )
                    for comm_type, count in counts.items()
                ]
                await self._types_collection.bulk_write(type_ops, ordered=False)

    async def clear(self):
        """Remove all records from the collection."""
        await self._records_collection.delete_many({})

    async def get_types(self):
        """Return distinct communication types from MongoDB."""
        record_types = await self._types_collection.find(
            {},
            {"_id": 0, "type": 1},
        ).to_list(length=None)
        return [record_type["type"] for record_type in record_types]

    async def filter_by_time(self, data_types, from_time, to_time):
        """Filter records by type and time range."""
        query = {
            "communicationType": {"$in": data_types},
            "time": {"$gte": from_time, "$lte": to_time},
        }
        cursor = self._records_collection.find(query, {"_id": 0})
        return await cursor.to_list(length=None)

    async def ensure_indexes(self):
        """Ensure required indexes exist for the records collection."""
        await self._records_collection.create_index("id", unique=True)
        await self._records_collection.create_index([("communicationType", 1), ("time", 1)])
        await self._types_collection.create_index("type", unique=True)

    async def reconcile_types(self):
        """Rebuild the types collection from records."""
        pipeline = [
            {"$group": {"_id": "$communicationType", "count": {"$sum": 1}}},
        ]
        grouped = await self._records_collection.aggregate(pipeline).to_list(length=None)
        await self._types_collection.delete_many({})
        if grouped:
            await self._types_collection.insert_many(
                [{"type": record_type["_id"], "count": record_type["count"]}
                    for record_type in grouped]
            )
        return [{"type": record_type["_id"], "count": record_type["count"]}
                for record_type in grouped]


class MongoUserRepository:
    """MongoDB repository for user accounts."""

    def __init__(self, db):
        """Bind to the MongoDB users collection."""
        self._collection = db["users"]

    async def create_user(self, username, password, is_admin=False):
        """Create a user if the username is not already taken."""
        if not username or not password:
            raise UserCreateError("Username and password are required")
        try:
            password_hash = await run_in_threadpool(pwd_context.hash, password)
            await self._collection.insert_one(
                {
                    "username": username,
                    "password_hash": password_hash,
                    "is_admin": is_admin,
                    "password_changed_at": int(time.time()),
                }
            )
        except DuplicateKeyError as exc:
            raise UserAlreadyExistsError(
                f"User '{username}' already exists") from exc
        except PyMongoError as exc:
            logger.exception("Failed to create user '%s'", username)
            raise UserCreateError("Failed to create user") from exc

    async def get_user(self, username):
        """Fetch a user document by username."""
        try:
            return await self._collection.find_one(
                {"username": username},
                {"_id": 0},
            )
        except PyMongoError as exc:
            logger.exception("Failed to load user '%s'", username)
            raise UserLookupError("Failed to load user") from exc

    async def ensure_indexes(self):
        """Ensure required indexes exist for the users collection."""
        await self._collection.create_index("username", unique=True)

    async def verify_password(self, username, password):
        """Verify a plaintext password against the stored hash."""
        try:
            user = await self._collection.find_one(
                {"username": username},
                {"_id": 0, "password_hash": 1},
            )
        except PyMongoError as exc:
            logger.exception(
                "Failed to load user '%s' for password verification", username)
            raise UserLookupError("Failed to verify credentials") from exc
        if not user:
            return False
        return await run_in_threadpool(
            pwd_context.verify,
            password,
            user.get("password_hash", ""),
        )
