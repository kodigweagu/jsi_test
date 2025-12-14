import csv
from datetime import datetime
from pathlib import Path
from secrets import token_hex


def parse_datetime(value: str) -> datetime:
    return datetime.strptime(value.strip(), "%d-%m-%Y %H:%M")


def parse_file(file_path: Path) -> list[dict]:
    with open(file_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="|")

        records = []
        for row in reader:
            record = {
                **row,
                "id": token_hex(12),
                "communicationType": file_path.stem,
                "time": parse_datetime(row["DateTime"])
            }
            record.pop("DateTime")
            records.append(record)

        return records
