"""FastAPI app setup and lifecycle wiring."""

import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from app.csvparser import parse_file
from app.repository import MongoRecordsRepository, MongoUserRepository
from app.api import router


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    """Initialize repositories and load seed data."""
    load_dotenv()
    mongo_uri = os.environ["MONGODB_URI"]
    mongo_db = os.environ["MONGODB_DB"]
    client = AsyncIOMotorClient(mongo_uri)
    repo = MongoRecordsRepository(client[mongo_db])
    user_repo = MongoUserRepository(client[mongo_db])
    resources_dir = Path(os.environ["RESOURCES_DIR"])

    await repo.ensure_indexes()
    await user_repo.ensure_indexes()

    for file_path in resources_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() == ".txt":
            records = parse_file(file_path)
            await repo.add(records)

    fastapi_app.state.repo = repo
    fastapi_app.state.user_repo = user_repo
    fastapi_app.state.mongo_client = client
    yield
    client.close()

app = FastAPI(lifespan=lifespan)

app.include_router(router)
