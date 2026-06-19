import os
import json
from datetime import datetime

try:
    import chromadb
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

CHROMA_DIR = os.path.join(os.path.dirname(__file__), "../../data/chroma_db")

_client = None
_collection = None

def _get_collection():
    global _client, _collection
    if not CHROMA_AVAILABLE:
        return None
    if _collection is None:
        _client = chromadb.PersistentClient(path=CHROMA_DIR)
        _collection = _client.get_or_create_collection(
            name="rbi_circulars",
            metadata={"description": "RBI regulatory circulars vector store"}
        )
    return _collection

def store_circular(circular_id: str, content: str, metadata: dict = None) -> dict:
    """Store a circular in ChromaDB vector store."""
    collection = _get_collection()
    if collection is None:
        return {"status": "skipped", "reason": "ChromaDB unavailable", "circular_id": circular_id}

    try:
        collection.upsert(
            documents=[content],
            ids=[circular_id],
            metadatas=[metadata or {"circular_id": circular_id, "stored_at": datetime.utcnow().isoformat()}]
        )
        return {"status": "stored", "circular_id": circular_id}
    except Exception as e:
        return {"status": "error", "reason": str(e), "circular_id": circular_id}

def search_similar(query: str, n_results: int = 3) -> list:
    """Search for similar circulars using vector similarity."""
    collection = _get_collection()
    if collection is None:
        return []

    try:
        results = collection.query(
            query_texts=[query],
            n_results=min(n_results, collection.count())
        )
        documents = results.get("documents", [[]])[0]
        ids = results.get("ids", [[]])[0]
        return [{"id": ids[i], "content": documents[i]} for i in range(len(ids))]
    except Exception:
        return []

def list_stored_circulars() -> list:
    """List all circulars stored in ChromaDB."""
    collection = _get_collection()
    if collection is None:
        return []

    try:
        result = collection.get()
        ids = result.get("ids", [])
        metadatas = result.get("metadatas", [])
        return [{"id": ids[i], "metadata": metadatas[i]} for i in range(len(ids))]
    except Exception:
        return []

def delete_circular(circular_id: str) -> dict:
    """Delete a circular from ChromaDB."""
    collection = _get_collection()
    if collection is None:
        return {"status": "skipped", "reason": "ChromaDB unavailable"}

    try:
        collection.delete(ids=[circular_id])
        return {"status": "deleted", "circular_id": circular_id}
    except Exception as e:
        return {"status": "error", "reason": str(e)}

if __name__ == "__main__":
    print("Storing test circular...")
    result = store_circular("test_001", "Banks must implement KYC within 30 days.", {"source": "test"})
    print(result)

    print("Searching...")
    results = search_similar("KYC banking requirements")
    print(results)

    print("Listing all...")
    all_circulars = list_stored_circulars()
    print(all_circulars)