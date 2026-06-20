import json
import math
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from .embeddings import embed_text

try:
    import chromadb
except Exception:
    chromadb = None


BACKEND_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BACKEND_DIR / "data"
CHROMA_DIR = DATA_DIR / "chroma_db"
COMPLIANCE_DIR = DATA_DIR / "compliance"
FALLBACK_MEMORY_PATH = COMPLIANCE_DIR / "regulatory_memory.json"
COLLECTION_NAME = "rbi_regulatory_memory"
EMBEDDING_DIMENSIONS = 128

_client = None
_collection = None
_client_mode = None
_last_chroma_error = None


def _utc_now():
    return datetime.utcnow().isoformat()


def _ensure_dirs():
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    COMPLIANCE_DIR.mkdir(parents=True, exist_ok=True)


def _safe_metadata(metadata: dict[str, Any] | None) -> dict[str, str | int | float | bool]:
    safe = {}
    for key, value in (metadata or {}).items():
        if value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            safe[key] = value
        else:
            safe[key] = json.dumps(value, ensure_ascii=True, sort_keys=True)
    return safe


def _content_excerpt(content: str, limit: int = 220) -> str:
    text = " ".join((content or "").split())
    return text[:limit]


def _read_fallback_memory() -> list[dict[str, Any]]:
    _ensure_dirs()
    if not FALLBACK_MEMORY_PATH.exists():
        return []

    try:
        payload = json.loads(FALLBACK_MEMORY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    if isinstance(payload, dict):
        records = payload.get("items") or []
    elif isinstance(payload, list):
        records = payload
    else:
        records = []

    return [record for record in records if isinstance(record, dict)]


def _write_fallback_memory(records: list[dict[str, Any]]) -> None:
    _ensure_dirs()
    payload = {
        "offline_mode": True,
        "updated_at": "local_seed",
        "count": len(records),
        "items": records,
    }
    FALLBACK_MEMORY_PATH.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )


def _upsert_fallback_record(record: dict[str, Any]) -> None:
    records = _read_fallback_memory()
    circular_id = record["circular_id"]
    updated = False

    for index, existing in enumerate(records):
        if existing.get("circular_id") == circular_id:
            records[index] = record
            updated = True
            break

    if not updated:
        records.append(record)

    records.sort(key=lambda item: item.get("circular_id", ""))
    _write_fallback_memory(records)


def _fallback_record(circular_id: str, content: str, metadata: dict[str, Any] | None) -> dict[str, Any]:
    metadata = metadata or {}
    title = metadata.get("title") or metadata.get("file_name") or circular_id
    category = metadata.get("category") or "Regulatory Compliance"
    return {
        "circular_id": circular_id,
        "title": title,
        "category": category,
        "content": content or "",
        "content_excerpt": _content_excerpt(content),
        "metadata": metadata,
        "embedding": embed_text(content or "", dimensions=EMBEDDING_DIMENSIONS),
        "source": metadata.get("source", "local_seed"),
        "updated_at": metadata.get("stored_at") or metadata.get("issue_date") or "local_seed",
    }


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0

    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def _format_record(record: dict[str, Any], similarity_score: float | None = None, source: str | None = None) -> dict[str, Any]:
    metadata = record.get("metadata") or {}
    circular_id = record.get("circular_id") or record.get("id") or metadata.get("circular_id", "")
    content = record.get("content") or record.get("document") or ""
    return {
        "circular_id": circular_id,
        "id": circular_id,
        "title": record.get("title") or metadata.get("title") or circular_id,
        "category": record.get("category") or metadata.get("category") or "Regulatory Compliance",
        "content": content,
        "content_excerpt": record.get("content_excerpt") or _content_excerpt(content),
        "metadata": metadata,
        "similarity_score": round(float(similarity_score or 0.0), 4),
        "source": source or record.get("source") or metadata.get("source", "json_fallback"),
    }


def _chroma_available() -> bool:
    return chromadb is not None


def _get_collection():
    global _client, _collection, _client_mode, _last_chroma_error
    if not _chroma_available():
        _last_chroma_error = "chromadb package is not installed"
        return None

    if _collection is not None:
        return _collection

    _ensure_dirs()
    host = os.getenv("CHROMA_HOST")
    port = os.getenv("CHROMA_PORT", "8000")

    if host:
        try:
            _client = chromadb.HttpClient(host=host, port=int(port))
            _collection = _client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"description": "Offline RBI regulatory memory"},
            )
            _client_mode = "http"
            return _collection
        except Exception as exc:
            _last_chroma_error = f"HTTP Chroma unavailable: {exc}"
            _client = None
            _collection = None

    try:
        _client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "Offline RBI regulatory memory"},
        )
        _client_mode = "persistent"
        return _collection
    except Exception as exc:
        _last_chroma_error = f"Persistent Chroma unavailable: {exc}"
        _client = None
        _collection = None
        return None


def add_circular(circular: dict) -> dict:
    circular_id = circular.get("circular_id") or circular.get("id")
    content = circular.get("content") or circular.get("text") or ""
    metadata = {
        key: value
        for key, value in circular.items()
        if key not in {"content", "text", "embedding"}
    }
    return store_circular(circular_id, content, metadata)


def store_circular(circular_id: str, content: str, metadata: dict | None = None) -> dict:
    _ensure_dirs()
    if not circular_id:
        return {"status": "error", "reason": "circular_id is required", "circular_id": circular_id}

    metadata = metadata or {}
    metadata.setdefault("circular_id", circular_id)
    metadata.setdefault("source", "local_seed")
    metadata.setdefault("stored_at", metadata.get("issue_date") or "local_seed")
    record = _fallback_record(circular_id, content or "", metadata)

    _upsert_fallback_record(record)

    collection = _get_collection()
    if collection is None:
        return {
            "status": "stored_fallback",
            "reason": _last_chroma_error or "ChromaDB unavailable",
            "circular_id": circular_id,
            "fallback_memory_path": str(FALLBACK_MEMORY_PATH),
        }

    try:
        collection.upsert(
            ids=[circular_id],
            documents=[content or ""],
            embeddings=[record["embedding"]],
            metadatas=[_safe_metadata(metadata)],
        )
        return {
            "status": "stored",
            "circular_id": circular_id,
            "chroma_mode": _client_mode,
            "fallback_memory_path": str(FALLBACK_MEMORY_PATH),
        }
    except Exception as exc:
        return {
            "status": "stored_fallback",
            "reason": str(exc),
            "circular_id": circular_id,
            "fallback_memory_path": str(FALLBACK_MEMORY_PATH),
        }


def _search_fallback(query: str, n_results: int = 3) -> list[dict[str, Any]]:
    query_embedding = embed_text(query, dimensions=EMBEDDING_DIMENSIONS)
    scored = []

    for record in _read_fallback_memory():
        embedding = record.get("embedding")
        if not isinstance(embedding, list):
            embedding = embed_text(record.get("content", ""), dimensions=EMBEDDING_DIMENSIONS)
        score = _cosine_similarity(query_embedding, embedding)
        scored.append((score, record))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [
        _format_record(record, similarity_score=score, source="json_fallback")
        for score, record in scored[: max(0, n_results)]
        if score > 0
    ]


def search_similar(query: str, n_results: int = 3) -> list:
    if not query or not query.strip() or n_results <= 0:
        return []

    collection = _get_collection()
    if collection is not None:
        try:
            count = collection.count()
            if count == 0:
                return []

            results = collection.query(
                query_embeddings=[embed_text(query, dimensions=EMBEDDING_DIMENSIONS)],
                n_results=min(n_results, count),
                include=["documents", "metadatas", "distances"],
            )
            ids = results.get("ids", [[]])[0]
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]

            formatted = []
            for index, circular_id in enumerate(ids):
                distance = distances[index] if index < len(distances) else 1.0
                score = max(0.0, 1.0 - float(distance))
                metadata = metadatas[index] if index < len(metadatas) else {}
                content = documents[index] if index < len(documents) else ""
                formatted.append(
                    _format_record(
                        {
                            "circular_id": circular_id,
                            "title": metadata.get("title") or circular_id,
                            "category": metadata.get("category") or "Regulatory Compliance",
                            "content": content,
                            "metadata": metadata,
                            "source": f"chroma_{_client_mode}",
                        },
                        similarity_score=score,
                        source=f"chroma_{_client_mode}",
                    )
                )
            return formatted
        except Exception:
            return _search_fallback(query, n_results=n_results)

    return _search_fallback(query, n_results=n_results)


def list_circulars() -> list:
    return list_stored_circulars()


def list_stored_circulars() -> list:
    records = _read_fallback_memory()
    if records:
        return [_format_record(record, source="json_fallback") for record in records]

    collection = _get_collection()
    if collection is None:
        return []

    try:
        result = collection.get(include=["documents", "metadatas"])
        ids = result.get("ids", [])
        documents = result.get("documents", [])
        metadatas = result.get("metadatas", [])
        return [
            _format_record(
                {
                    "circular_id": ids[index],
                    "content": documents[index] if index < len(documents) else "",
                    "metadata": metadatas[index] if index < len(metadatas) else {},
                },
                source=f"chroma_{_client_mode}",
            )
            for index in range(len(ids))
        ]
    except Exception:
        return []


def clear_store() -> dict:
    global _collection
    deleted_fallback = False
    if FALLBACK_MEMORY_PATH.exists():
        FALLBACK_MEMORY_PATH.unlink()
        deleted_fallback = True

    collection = _get_collection()
    chroma_cleared = False
    if collection is not None:
        try:
            ids = collection.get().get("ids", [])
            if ids:
                collection.delete(ids=ids)
            chroma_cleared = True
        except Exception:
            chroma_cleared = False

    return {
        "status": "cleared",
        "fallback_deleted": deleted_fallback,
        "chroma_cleared": chroma_cleared,
    }


def store_status() -> dict:
    collection = _get_collection()
    count = 0
    if collection is not None:
        try:
            count = collection.count()
        except Exception:
            count = 0

    return {
        "chroma_available": collection is not None,
        "chroma_mode": _client_mode,
        "chroma_error": _last_chroma_error,
        "collection_count": count,
        "fallback_memory_path": str(FALLBACK_MEMORY_PATH),
        "fallback_count": len(_read_fallback_memory()),
    }


if __name__ == "__main__":
    print(json.dumps(store_status(), indent=2))
