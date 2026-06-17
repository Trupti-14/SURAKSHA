"""FastAPI routes for the offline compliance MVP."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter

try:
    from engines.compliance.actions import generate_action_points
    from engines.compliance.priority import calculate_priority
except ModuleNotFoundError:
    from backend.engines.compliance.actions import generate_action_points
    from backend.engines.compliance.priority import calculate_priority


router = APIRouter(prefix="/api/compliance", tags=["compliance"])

DATA_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "compliance"
    / "mock_circulars.json"
)


def load_circulars() -> list[dict[str, Any]]:
    try:
        with DATA_PATH.open("r", encoding="utf-8") as circular_file:
            circulars = json.load(circular_file)
    except (OSError, json.JSONDecodeError):
        return []

    if not isinstance(circulars, list):
        return []

    return [
        {
            **circular,
            **calculate_priority(circular),
        }
        for circular in circulars
        if isinstance(circular, dict)
    ]


@router.get("/circulars")
def get_circulars() -> dict[str, Any]:
    return {"circulars": load_circulars()}


@router.get("/actions")
def get_actions() -> dict[str, Any]:
    circulars = load_circulars()
    return {"actions": generate_action_points(circulars)}


@router.get("/workflow")
def get_workflow() -> dict[str, Any]:
    circulars = load_circulars()
    actions = generate_action_points(circulars)
    return {
        "mode": "offline",
        "workflow": [
            "Local Circular",
            "Scout Parser",
            "Delta Check",
            "MAP Generator",
            "Priority Score",
            "Evidence Verify",
        ],
        "summary": {
            "circulars": len(circulars),
            "actions": len(actions),
            "critical": sum(
                1 for circular in circulars if circular["priority_label"] == "Critical"
            ),
        },
        "circulars": circulars,
        "actions": actions,
    }


@router.post("/evidence")
async def post_evidence() -> dict[str, Any]:
    return {
        "verified": True,
        "confidence": 0.82,
        "notes": "Evidence accepted for offline compliance review",
    }
