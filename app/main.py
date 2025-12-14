import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pathlib import Path
from app.csvparser import parse_file
from app.repository import InMemoryRepository
from app.api import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    repo = InMemoryRepository()
    resources_dir = Path(os.getenv("RESOURCES_DIR", "resources"))

    for file_path in resources_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() == ".txt":
            records = parse_file(file_path)
            repo.add(file_path.stem, records)

    app.state.repo = repo
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(router)
