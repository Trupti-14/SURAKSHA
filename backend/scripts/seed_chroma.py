"""Seed local regulatory memory from mock circular data.

Run from the project root:
python backend/scripts/seed_chroma.py
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.engines.compliance.chroma_store import MEMORY_PATH, add_circular


SOURCE_PATH = (
    PROJECT_ROOT / "backend" / "data" / "compliance" / "mock_circulars.json"
)


def _load_source() -> list[dict[str, Any]]:
    try:
        with SOURCE_PATH.open("r", encoding="utf-8") as source_file:
            payload = json.load(source_file)
    except (OSError, json.JSONDecodeError):
        return []

    if not isinstance(payload, list):
        return []

    return [record for record in payload if isinstance(record, dict)]


def main() -> int:
    circulars = _load_source()
    loaded_count = len(circulars)
    seeded_count = 0
    skipped_count = 0

    for circular in circulars:
        if add_circular(circular):
            seeded_count += 1
        else:
            skipped_count += 1

    print(f"loaded_count={loaded_count}")
    print(f"seeded_count={seeded_count}")
    print(f"skipped_count={skipped_count}")
    print(f"memory_path={MEMORY_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
