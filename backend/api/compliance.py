from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from engines.compliance.workflow import run_compliance_workflow
from engines.compliance.scout import (
    scan_circulars,
    get_circular_by_id
)
from engines.compliance.actions import (
    extract_action_points
)
from engines.compliance.priority import (
    calculate_priority
)

router = APIRouter(
    prefix="/api/compliance",
    tags=["compliance"]
)


class CircularRequest(BaseModel):
    circular_id: str | None = None
    content: str | None = None


class ActionPointsRequest(BaseModel):
    content: str


@router.post("/analyze")
def analyze_circular(request: CircularRequest):

    if not request.circular_id and not request.content:
        raise HTTPException(
            status_code=400,
            detail="Provide circular_id or content"
        )

    result = run_compliance_workflow(
        circular_id=request.circular_id,
        new_content=request.content
    )

    if "error" in result:
        raise HTTPException(
            status_code=404,
            detail=result["error"]
        )

    return result


@router.get("/circulars")
def list_circulars():

    circulars = scan_circulars()

    return {
        "total": len(circulars),
        "circulars": circulars
    }


@router.get("/circulars/{circular_id}")
def get_circular(circular_id: str):

    circular = get_circular_by_id(circular_id)

    if not circular:
        raise HTTPException(
            status_code=404,
            detail="Circular not found"
        )

    return circular


@router.post("/action-points")
def get_action_points(
    request: ActionPointsRequest
):

    result = extract_action_points(
        request.content
    )

    prioritized = calculate_priority(
        result.get("action_points", [])
    )

    result["action_points"] = prioritized

    return result


@router.get("/health")
def compliance_health():

    return {
        "status": "Compliance engine online",
        "module": "compliance"
    }