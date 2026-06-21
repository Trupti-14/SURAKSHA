import json
import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from engines.compliance.chroma_store import (  # noqa: E402
    FALLBACK_MEMORY_PATH,
    clear_store,
    list_stored_circulars,
    store_circular,
    store_status,
)


CIRCULAR_DIR = BACKEND_DIR / "data" / "circulars"
CIRCULAR_FILES = [
    CIRCULAR_DIR / "rbi_circular_001.txt",
    CIRCULAR_DIR / "rbi_circular_002.txt",
    CIRCULAR_DIR / "rbi_circular_003.txt",
    CIRCULAR_DIR / "rbi_it_outsourcing_master_direction_2023.txt",
]
USER_REFERENCE_PREFIX = "USER-REF-"


def _parse_circular_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    metadata = {}
    body_lines = []
    in_metadata = True

    for line in text.splitlines():
        if in_metadata and ":" in line:
            key, value = line.split(":", 1)
            normalized_key = key.strip().lower()
            if normalized_key in {
                "circular_id",
                "title",
                "category",
                "issue_date",
                "regulator",
                "effective_from",
                "status",
                "source_type",
            }:
                metadata[normalized_key] = value.strip()
                continue

        if line.strip():
            in_metadata = False
        body_lines.append(line)

    circular_id = metadata.get("circular_id") or path.stem
    metadata.setdefault("circular_id", circular_id)
    metadata.setdefault("title", path.stem.replace("_", " ").title())
    metadata.setdefault("category", "Regulatory Compliance")
    metadata.setdefault("source", "local_seed")
    metadata.setdefault("file_name", path.name)
    metadata.setdefault("path", str(path))

    return {
        "circular_id": circular_id,
        "content": text,
        "metadata": metadata,
    }


def _is_user_reference_id(circular_id: str | None) -> bool:
    return bool(circular_id and circular_id.startswith(USER_REFERENCE_PREFIX))


def _record_from_stored_item(item: dict) -> dict | None:
    circular_id = item.get("circular_id") or item.get("id")
    content = item.get("content") or item.get("text") or ""
    if not _is_user_reference_id(circular_id) or not content:
        return None

    metadata = dict(item.get("metadata") or {})
    metadata.setdefault("circular_id", circular_id)
    metadata.setdefault("title", item.get("title") or circular_id)
    metadata.setdefault("category", item.get("category") or "Regulatory Compliance")
    metadata.setdefault("source", "user_added_reference")
    metadata.setdefault("source_type", "User added approved reference")
    metadata.setdefault("file_name", f"{circular_id}.txt")

    return {
        "circular_id": circular_id,
        "content": content,
        "metadata": metadata,
    }


def _record_from_user_reference_file(path: Path) -> dict | None:
    circular_id = path.stem
    if not _is_user_reference_id(circular_id):
        return None

    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return None

    if not content.strip():
        return None

    metadata = {
        "circular_id": circular_id,
        "title": circular_id.replace("-", " ").title(),
        "category": "Regulatory Compliance",
        "source": "user_added_reference",
        "source_type": "User added approved reference",
        "file_name": path.name,
        "path": str(path),
        "stored_at": "preserved_user_reference_file",
    }
    return {
        "circular_id": circular_id,
        "content": content,
        "metadata": metadata,
    }


def _preserved_user_references() -> list[dict]:
    preserved = {}

    for item in list_stored_circulars():
        record = _record_from_stored_item(item)
        if record:
            preserved[record["circular_id"]] = record

    for path in CIRCULAR_DIR.glob(f"{USER_REFERENCE_PREFIX}*.txt"):
        record = _record_from_user_reference_file(path)
        if record and record["circular_id"] not in preserved:
            preserved[record["circular_id"]] = record

    return [preserved[key] for key in sorted(preserved)]


def seed() -> dict:
    loaded_count = 0
    seeded_count = 0
    skipped_count = 0
    preserved_user_references = _preserved_user_references()
    restored_user_reference_count = 0
    results = []
    clear_result = clear_store()

    for path in CIRCULAR_FILES:
        if not path.exists():
            skipped_count += 1
            results.append({"file": str(path), "status": "missing"})
            continue

        try:
            circular = _parse_circular_file(path)
            loaded_count += 1
            result = store_circular(
                circular["circular_id"],
                circular["content"],
                circular["metadata"],
            )
            if result.get("status") in {"stored", "stored_fallback"}:
                seeded_count += 1
            else:
                skipped_count += 1
            results.append(
                {
                    "file": path.name,
                    "circular_id": circular["circular_id"],
                    "status": result.get("status"),
                    "reason": result.get("reason"),
                }
            )
        except Exception as exc:
            skipped_count += 1
            results.append({"file": path.name, "status": "error", "reason": str(exc)})

    for circular in preserved_user_references:
        try:
            result = store_circular(
                circular["circular_id"],
                circular["content"],
                circular["metadata"],
            )
            if result.get("status") in {"stored", "stored_fallback"}:
                restored_user_reference_count += 1
            else:
                skipped_count += 1
            results.append(
                {
                    "file": circular["metadata"].get("file_name", f"{circular['circular_id']}.txt"),
                    "circular_id": circular["circular_id"],
                    "status": result.get("status"),
                    "preserved_user_reference": True,
                    "reason": result.get("reason"),
                }
            )
        except Exception as exc:
            skipped_count += 1
            results.append(
                {
                    "circular_id": circular["circular_id"],
                    "status": "error",
                    "preserved_user_reference": True,
                    "reason": str(exc),
                }
            )

    status = store_status()
    summary = {
        "loaded_count": loaded_count,
        "seeded_count": seeded_count,
        "skipped_count": skipped_count,
        "preserved_user_reference_count": len(preserved_user_references),
        "restored_user_reference_count": restored_user_reference_count,
        "fallback_memory_path": str(FALLBACK_MEMORY_PATH),
        "chroma_available": status["chroma_available"],
        "chroma_mode": status["chroma_mode"],
        "collection_count": status["collection_count"],
        "fallback_count": status["fallback_count"],
        "stored_count": len(list_stored_circulars()),
        "clear_status": clear_result.get("status"),
        "results": results,
    }
    return summary


if __name__ == "__main__":
    print(json.dumps(seed(), indent=2))
