"""Offline evidence file verification for compliance action points."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from engines.compliance.embeddings import keyword_overlap, tokenize
except ModuleNotFoundError:
    from backend.engines.compliance.embeddings import keyword_overlap, tokenize


ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024


def _map_text(map_item: dict[str, Any] | None) -> str:
    if not isinstance(map_item, dict):
        return ""

    return " ".join(
        str(map_item.get(field, ""))
        for field in ("id", "action", "evidence_required", "reason", "owner")
    )


def _filename_matches(file_name: str, map_item: dict[str, Any] | None) -> bool:
    map_text = _map_text(map_item)
    if not file_name or not map_text:
        return False

    file_stem = Path(file_name).stem
    file_terms = set(tokenize(file_stem))
    map_terms = set(tokenize(map_text))
    if file_terms & map_terms:
        return True

    return keyword_overlap(file_stem, map_text) >= 0.12


def verify_evidence_file(
    file_name: str,
    file_size: int,
    map_item: dict[str, Any] | None,
) -> dict[str, Any]:
    """Verify basic evidence metadata fully offline.

    This performs deterministic filename, type, and size checks. Local
    OpenCV/local vision checks can be connected later for document-image review.
    """

    suffix = Path(file_name or "").suffix.lower()
    checks = {
        "allowed_type": suffix in ALLOWED_EXTENSIONS,
        "has_content": file_size > 0,
        "within_size_limit": 0 < file_size <= MAX_FILE_SIZE_BYTES,
        "filename_matches_action": _filename_matches(file_name, map_item),
    }

    if not checks["allowed_type"]:
        return {
            "status": "rejected",
            "confidence": 0.0,
            "checks": checks,
            "reason": "Evidence file type is not permitted. Upload PDF, PNG, JPG, or JPEG.",
            "manual_review_required": True,
        }

    if not checks["has_content"]:
        return {
            "status": "rejected",
            "confidence": 0.0,
            "checks": checks,
            "reason": "Evidence file is empty and cannot support compliance closure.",
            "manual_review_required": True,
        }

    if not checks["within_size_limit"]:
        return {
            "status": "rejected",
            "confidence": 0.0,
            "checks": checks,
            "reason": "Evidence file exceeds the 10 MB offline review limit.",
            "manual_review_required": True,
        }

    if checks["filename_matches_action"]:
        return {
            "status": "verified_offline",
            "confidence": 0.82,
            "checks": checks,
            "reason": "Evidence metadata matches the selected action point and is ready for compliance review.",
            "manual_review_required": False,
        }

    return {
        "status": "needs_manual_review",
        "confidence": 0.48,
        "checks": checks,
        "reason": "Evidence type and size are acceptable, but the filename does not clearly match the selected action point. Local OpenCV/local vision checks can be connected later.",
        "manual_review_required": True,
    }
