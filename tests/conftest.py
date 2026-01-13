"""Test configuration and path setup."""

import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from passlib.context import CryptContext
from pymongo import MongoClient

# Ensure project root is importable
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

load_dotenv()
os.environ.setdefault("JWT_SECRET", "test-secret")

from tests.utils import DEFAULT_USERNAME, DEFAULT_PASSWORD


# Force all tests to use test_resources
os.environ["RESOURCES_DIR"] = "test_resources"

mongo_uri = os.environ["MONGODB_URI"]
base_db = os.environ["MONGODB_DB"]
test_db = f"{base_db}_test"
os.environ["MONGODB_DB"] = test_db

client = MongoClient(mongo_uri)
db = client[test_db]
db.records.delete_many({})
db.types.delete_many({})
db.users.delete_many({})
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
db.users.insert_one(
    {
        "username": DEFAULT_USERNAME,
        "password_hash": pwd_context.hash(DEFAULT_PASSWORD),
        "is_admin": True,
        "password_changed_at": int(time.time()),
    }
)
