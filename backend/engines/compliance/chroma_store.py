"""JSON-backed local regulatory memory for offline compliance search.

This module stores circular records in a local JSON file and uses simple
bag-of-words similarity for offline retrieval.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from engines.compliance.embeddings import (
        cosine_similarity,
        embed_text,
        keyword_overlap,
    )
except ModuleNotFoundError:
    from backend.engines.compliance.embeddings import (
        cosine_similarity,
        embed_text,
        keyword_overlap,
    )


MEMORY_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "compliance"
    / "regulatory_memory.json"
)

TEXT_FIELDS = (
    "title",
    "category",
    "summary",
    "old_policy",
    "new_policy",
    "detected_gap",
    "text",
)


def _record_text(circular: dict[str, Any]) -> str:
    return " ".join(str(circular.get(field, "")) for field in TEXT_FIELDS)


def _safe_record(circular: dict[str, Any]) -> dict[str, Any]:
    record = dict(circular)
    record["_embedding"] = embed_text(_record_text(record))
    return record


def _public_record(record: dict[str, Any]) -> dict[str, Any]:
    public = dict(record)
    public.pop("_embedding", None)
    return public


def _load_records() -> list[dict[str, Any]]:
    if not MEMORY_PATH.exists():
        return []

    try:
        with MEMORY_PATH.open("r", encoding="utf-8") as memory_file:
            payload = json.load(memory_file)
    except (OSError, json.JSONDecodeError):
        return []

    if isinstance(payload, dict):
        records = payload.get("circulars", [])
    elif isinstance(payload, list):
        records = payload
    else:
        return []

    return [record for record in records if isinstance(record, dict)]


def _write_records(records: list[dict[str, Any]]) -> None:
    MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {"circulars": records}
    with MEMORY_PATH.open("w", encoding="utf-8") as memory_file:
        json.dump(payload, memory_file, indent=2, ensure_ascii=False)
        memory_file.write("\n")


def add_circular(circular: dict[str, Any]) -> bool:
    """Add a circular to local memory.

    Returns True when the record is added and False for invalid or duplicate
    circular IDs.
    """

    if not isinstance(circular, dict):
        return False

    circular_id = str(circular.get("circular_id", "")).strip()
    if not circular_id:
        return False

    records = _load_records()
    existing_ids = {str(record.get("circular_id", "")).strip() for record in records}
    if circular_id in existing_ids:
        return False

    records.append(_safe_record(circular))
    _write_records(records)
    return True


def search_similar(query: str, top_k: int = 3) -> list[dict[str, Any]]:
    """Search local regulatory memory and return records with similarity scores."""

    if top_k <= 0 or not query:
        return []

    query_embedding = embed_text(query)
    if not query_embedding:
        return []

    ranked: list[dict[str, Any]] = []
    for record in _load_records():
        record_text = _record_text(record)
        record_embedding = record.get("_embedding")
        if not isinstance(record_embedding, dict):
            record_embedding = embed_text(record_text)

        cosine_score = cosine_similarity(query_embedding, record_embedding)
        overlap_score = keyword_overlap(query, record_text)
        similarity_score = round((0.85 * cosine_score) + (0.15 * overlap_score), 6)

        result = _public_record(record)
        result["similarity_score"] = similarity_score
        ranked.append(result)

    ranked.sort(key=lambda item: item["similarity_score"], reverse=True)
    return ranked[:top_k]


def list_circulars() -> list[dict[str, Any]]:
    """Return all circulars stored in local regulatory memory."""

    return [_public_record(record) for record in _load_records()]


def clear_store() -> None:
    """Clear local regulatory memory."""

    _write_records([])
