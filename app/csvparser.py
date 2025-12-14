import csv
from datetime import datetime
from pathlib import Path

def parse_datetime(value: str) -> datetime:
    return datetime.strptime(value.strip(), "%d-%m-%Y %H:%M")

def parse_file(file_path: Path) -> list[dict]:
    with open(file_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="|")

        return [
            {
                **row, 
                "communicationType": file_path.stem, 
                "DateTime": parse_datetime(row["DateTime"])
            }
            for row in reader
        ]
