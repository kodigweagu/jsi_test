import os
from fastapi import FastAPI
from pathlib import Path
from app.parser import parse_file
from app.repository import InMemoryRepository
from app.api import router

app = FastAPI()

@app.on_event("startup")
def startup():
    repo = InMemoryRepository()
    resources_dir = Path(os.getenv("RESOURCES_DIR", "resources"))

    for file_path in resources_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() == ".txt":
            records = parse_file(file_path)
            repo.add(file_path.stem, records)

    app.state.repo = repo

app.include_router(router)
