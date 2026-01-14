"""Tests for repository behaviors and error handling."""

import types

import pytest
from pymongo.errors import DuplicateKeyError, PyMongoError

import app.repository as repository_module
from app.repository import (
    MongoRecordsRepository,
    MongoUserRepository,
    UserAlreadyExistsError,
    UserCreateError,
    UserLookupError,
)


class _BulkResult:  # pylint: disable=too-few-public-methods
    """Bulk write result stub."""

    def __init__(self, upserted_ids):
        self.upserted_ids = upserted_ids


class _RecordsCollection:  # pylint: disable=too-few-public-methods
    """Records collection stub."""

    def __init__(self):
        self.bulk_args = None
        self.created_indexes = []

    async def bulk_write(self, ops, ordered=False):
        """Return stubbed upserted ids."""
        self.bulk_args = (ops, ordered)
        return _BulkResult({0: "id0", 2: "id2"})

    async def delete_many(self, _query):
        """No-op delete."""
        return None

    async def distinct(self, _field):
        """Return distinct types."""
        return ["Chats", "Emails"]

    def find(self, _query, _projection):
        """Return a cursor stub."""
        async def _to_list(length=None):
            return [{"communicationType": "Chats"}]
        return types.SimpleNamespace(to_list=_to_list)

    async def create_index(self, key, unique=False):
        """Capture index creation."""
        self.created_indexes.append((key, unique))

    def aggregate(self, _pipeline):
        """Return aggregate cursor stub."""
        async def _to_list(length=None):
            return [{"_id": "Chats", "count": 2}]
        return types.SimpleNamespace(to_list=_to_list)


class _TypesCollection:  # pylint: disable=too-few-public-methods
    """Types collection stub."""

    def __init__(self):
        self.type_ops = []
        self.created_indexes = []

    async def bulk_write(self, ops, ordered=False):
        """Capture type updates."""
        self.type_ops = ops
        return None

    def find(self, _query, _projection):
        """Return a cursor stub."""
        async def _to_list(length=None):
            return [{"type": "Chats"}, {"type": "Emails"}]
        return types.SimpleNamespace(to_list=_to_list)

    async def create_index(self, key, unique=False):
        """Capture index creation."""
        self.created_indexes.append((key, unique))

    async def delete_many(self, _query):
        """No-op delete."""
        return None

    async def insert_many(self, _docs):
        """No-op insert."""
        return None


class _UsersCollection:  # pylint: disable=too-few-public-methods
    """Users collection stub."""

    def __init__(self):
        self.insert_calls = []
        self.find_result = None
        self.raise_duplicate = False
        self.raise_error = False
        self.created_indexes = []

    async def insert_one(self, doc):
        """Insert or raise errors."""
        if self.raise_duplicate:
            raise DuplicateKeyError("dup")
        if self.raise_error:
            raise PyMongoError("db")
        self.insert_calls.append(doc)
        return None

    async def find_one(self, _query, _projection):
        """Return or raise errors."""
        if self.raise_error:
            raise PyMongoError("db")
        return self.find_result

    async def create_index(self, key, unique=False):
        """No-op index creation."""
        self.created_indexes.append((key, unique))


@pytest.fixture(autouse=True)
def _stub_threadpool(monkeypatch):
    """Stub run_in_threadpool to avoid real hashing work."""
    async def _fake_run_in_threadpool(func, *_args, **_kwargs):
        if getattr(func, "__name__", "") == "verify":
            return True
        return "hash"

    monkeypatch.setattr(repository_module,
                        "run_in_threadpool", _fake_run_in_threadpool)


@pytest.mark.asyncio
async def test_records_add_updates_types_counts():
    """Update types counts for upserted records."""
    db = {"records": _RecordsCollection(), "types": _TypesCollection()}
    repo = MongoRecordsRepository(db)
    records = [
        {"id": "a", "communicationType": "Chats"},
        {"id": "b", "communicationType": "Emails"},
        {"id": "c", "communicationType": "Emails"},
    ]
    await repo.add(records)
    assert len(db["types"].type_ops) == 2


@pytest.mark.asyncio
async def test_records_clear_and_filter():
    """Exercise clear and filter helpers."""
    db = {"records": _RecordsCollection(), "types": _TypesCollection()}
    repo = MongoRecordsRepository(db)
    await repo.clear()
    result = await repo.filter_by_time(["Chats"], None, None)
    assert result == [{"communicationType": "Chats"}]


@pytest.mark.asyncio
async def test_records_get_types_from_types_collection():
    """Return types from the types collection."""
    db = {"records": _RecordsCollection(), "types": _TypesCollection()}
    repo = MongoRecordsRepository(db)
    result = await repo.get_types()
    assert result == ["Chats", "Emails"]


@pytest.mark.asyncio
async def test_records_collection_distinct_stub():
    """Cover records collection distinct stub."""
    records = _RecordsCollection()
    result = await records.distinct("communicationType")
    assert result == ["Chats", "Emails"]


@pytest.mark.asyncio
async def test_records_reconcile_types_returns_counts():
    """Return reconciled type counts."""
    db = {"records": _RecordsCollection(), "types": _TypesCollection()}
    repo = MongoRecordsRepository(db)
    result = await repo.reconcile_types()
    assert result == [{"type": "Chats", "count": 2}]


@pytest.mark.asyncio
async def test_records_ensure_indexes():
    """Create required indexes."""
    db = {"records": _RecordsCollection(), "types": _TypesCollection()}
    repo = MongoRecordsRepository(db)
    await repo.ensure_indexes()
    assert ("id", True) in db["records"].created_indexes
    assert ([("communicationType", 1), ("time", 1)],
            False) in db["records"].created_indexes
    assert ("type", True) in db["types"].created_indexes


@pytest.mark.asyncio
async def test_user_create_duplicate_raises():
    """Raise when creating a duplicate user."""
    users = _UsersCollection()
    users.raise_duplicate = True
    repo = MongoUserRepository({"users": users})
    with pytest.raises(UserAlreadyExistsError):
        await repo.create_user("u", "p")


@pytest.mark.asyncio
async def test_user_create_db_error_raises():
    """Raise on DB errors."""
    users = _UsersCollection()
    users.raise_error = True
    repo = MongoUserRepository({"users": users})
    with pytest.raises(UserCreateError):
        await repo.create_user("u", "p")


@pytest.mark.asyncio
async def test_user_create_missing_fields_raises():
    """Reject missing username or password."""
    repo = MongoUserRepository({"users": _UsersCollection()})
    with pytest.raises(UserCreateError):
        await repo.create_user("", "p")
    with pytest.raises(UserCreateError):
        await repo.create_user("u", "")


@pytest.mark.asyncio
async def test_user_create_success():
    """Insert a user document on success."""
    users = _UsersCollection()
    repo = MongoUserRepository({"users": users})
    await repo.create_user("u", "p")
    assert users.insert_calls
    assert users.insert_calls[0]["password_hash"] == "hash"


@pytest.mark.asyncio
async def test_user_get_lookup_error_raises():
    """Raise when user lookup fails."""
    users = _UsersCollection()
    users.raise_error = True
    repo = MongoUserRepository({"users": users})
    with pytest.raises(UserLookupError):
        await repo.get_user("u")


@pytest.mark.asyncio
async def test_verify_password_returns_false_for_missing_user():
    """Return False when user is missing."""
    users = _UsersCollection()
    users.find_result = None
    repo = MongoUserRepository({"users": users})
    assert await repo.verify_password("u", "p") is False


@pytest.mark.asyncio
async def test_verify_password_returns_true_for_match():
    """Return True when password verifies."""
    users = _UsersCollection()
    users.find_result = {"password_hash": "hash"}
    repo = MongoUserRepository({"users": users})
    assert await repo.verify_password("u", "p") is True


@pytest.mark.asyncio
async def test_user_ensure_indexes():
    """Create required user indexes."""
    users = _UsersCollection()
    repo = MongoUserRepository({"users": users})
    await repo.ensure_indexes()
    assert ("username", True) in users.created_indexes


@pytest.mark.asyncio
async def test_verify_password_lookup_error_raises():
    """Raise when lookup fails."""
    users = _UsersCollection()
    users.raise_error = True
    repo = MongoUserRepository({"users": users})
    with pytest.raises(UserLookupError):
        await repo.verify_password("u", "p")
