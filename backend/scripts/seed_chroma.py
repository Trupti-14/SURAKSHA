"""
Seed script — loads all RBI circulars from data/circulars/
into ChromaDB vector store for semantic search.
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from engines.compliance.chroma_store import store_circular, list_stored_circulars
from engines.compliance.scout import scan_circulars, get_circular_by_id

def seed():
    print("Starting ChromaDB seeding...")
    circulars = scan_circulars()

    if not circulars:
        print("No circulars found in data/circulars/")
        return

    print(f"Found {len(circulars)} circulars to seed")

    for c in circulars:
        circular_id = c["id"]
        full = get_circular_by_id(circular_id)
        if not full:
            print(f"Skipping {circular_id} — could not load content")
            continue

        result = store_circular(
            circular_id=circular_id,
            content=full["content"],
            metadata={
                "circular_id": circular_id,
                "source": "rbi",
                "file": c.get("path", "")
            }
        )
        print(f"Seeded {circular_id}: {result['status']}")

    print("\nAll circulars seeded. Current ChromaDB contents:")
    stored = list_stored_circulars()
    for s in stored:
        print(f"  - {s['id']}")

if __name__ == "__main__":
    seed()