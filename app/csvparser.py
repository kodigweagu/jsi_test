"""Parse resource files into normalized communication records."""

import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path
from dateutil import parser


def compute_record_hash(payload: dict) -> str:
    """Return a deterministic hash for a record payload."""
    serialized = json.dumps(payload, sort_keys=True,
                            separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def parse_datetime(value: str) -> datetime:
    """Parse a DateTime field in supported formats."""
    try:
        return parser.parse(value)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Unsupported DateTime format: {value}") from exc


def parse_file(file_path: Path) -> list[dict]:
    """Read a delimited file and return normalized records."""
    with open(file_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="|")

        records = []
        for row in reader:
            parsed_time = parse_datetime(row["DateTime"])
            hash_payload = {
                **row,
                "communicationType": file_path.stem,
                "time": parsed_time.isoformat()
            }
            record = {
                **row,
                "id": compute_record_hash(hash_payload),
                "communicationType": file_path.stem,
                "time": parsed_time
            }
            record.pop("DateTime")
            records.append(record)

        return records
