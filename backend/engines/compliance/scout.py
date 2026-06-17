import os
from pathlib import Path

CIRCULARS_DIR = Path("data/circulars")


def scan_circulars():
    circulars = []

    if not CIRCULARS_DIR.exists():
        return circulars

    for file in CIRCULARS_DIR.glob("*.txt"):
        circulars.append(
            {
                "id": file.stem,
                "path": str(file),
                "ingested_at": file.stat().st_mtime,
            }
        )

    return circulars


def get_circular_by_id(circular_id):
    file_path = CIRCULARS_DIR / f"{circular_id}.txt"

    if not file_path.exists():
        return None

    return {
        "id": circular_id,
        "content": file_path.read_text(encoding="utf-8")
    }