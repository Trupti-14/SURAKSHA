from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from typing import Optional
from engines.compliance.workflow import run_compliance_workflow
from engines.compliance.scout import scan_circulars, get_circular_by_id
from engines.compliance.chroma_store import search_similar, store_circular
from engines.compliance.vision import verify_evidence_from_upload

router = APIRouter(prefix="/api/compliance", tags=["compliance"])


class CircularRequest(BaseModel):
    circular_text: Optional[str] = None
    file_name: Optional[str] = None
    mode: Optional[str] = "offline"
    circular_id: Optional[str] = None
    content: Optional[str] = None


@router.post("/analyze")
def analyze_circular(request: CircularRequest):
    # Support both Trupti's format and our internal format
    content = request.circular_text or request.content
    circular_id = request.circular_id

    if not content and not circular_id:
        raise HTTPException(status_code=400, detail="Provide circular_text or circular_id")

    result = run_compliance_workflow(
        circular_id=circular_id,
        new_content=content
    )

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    # Extract data from workflow result
    delta = result.get("delta", {})
    actions = result.get("actions", {})
    action_points = actions.get("action_points", [])

    # Build policy gaps from delta
    policy_gaps = []
    if delta.get("gap_found"):
        policy_gaps = [
            {"gap": control, "severity": "MEDIUM"}
            for control in delta.get("missing_controls", [])[:5]
        ]

    # Build MAPs in Trupti's format
    maps = []
    for ap in action_points:
        if isinstance(ap, dict):
            maps.append({
                "id": ap.get("id", "MAP-001"),
                "action": ap.get("action", str(ap)),
                "department": ap.get("department", "Compliance"),
                "deadline_days": ap.get("deadline_days", 30),
                "priority_label": ap.get("priority_label", "HIGH"),
                "priority_score": ap.get("priority_score", 6)
            })
        else:
            maps.append({
                "id": "MAP-001",
                "action": str(ap),
                "department": "Compliance",
                "deadline_days": 30,
                "priority_label": "HIGH",
                "priority_score": 6
            })

    # Search similar circulars from ChromaDB
    query = content or ""
    similar = search_similar(query, n_results=3)

    # Store this circular in ChromaDB
    if content:
        store_circular(
            request.file_name or "uploaded_circular",
            content,
            {"file_name": request.file_name or "unknown", "mode": request.mode}
        )

    # Top priority
    top_priority = maps[0] if maps else {}
    priority_score = top_priority.get("priority_score", 5)
    priority_label = top_priority.get("priority_label", "MEDIUM")

    return {
        "offline_mode": True,
        "summary": delta.get("summary", "Compliance analysis complete"),
        "obligations": [ap.get("action", "") for ap in maps],
        "similar_circulars": [s.get("id", "") for s in similar],
        "policy_gaps": policy_gaps,
        "measurable_action_points": maps,
        "priority": {
            "priority_score": priority_score,
            "priority_label": priority_label,
            "priority_reason": f"Based on {len(maps)} action points detected"
        },
        "workflow": [
            {"step": 1, "agent": "Scout", "status": "done"},
            {"step": 2, "agent": "Delta", "status": "done"},
            {"step": 3, "agent": "Actions", "status": "done"},
            {"step": 4, "agent": "Priority", "status": "done"}
        ],
        "engine_notes": [
            f"Analysis by: {delta.get('analysis_by', 'keyword')}",
            f"Gap found: {delta.get('gap_found', False)}",
            f"Risk level: {delta.get('risk_level', 'MEDIUM')}",
            "Offline mode: Phi-3 + keyword fallback"
        ]
    }


@router.post("/evidence/verify")
async def verify_evidence(
    file: Optional[UploadFile] = File(default=None),
    required_evidence: Optional[str] = Form(default=None),
    action_id: Optional[str] = Form(default=None),
):
    del action_id  # Action context can be logged later; verification is file-based.

    if file is None:
        return verify_evidence_from_upload(
            file_bytes=None,
            filename=None,
            required_evidence=required_evidence,
        )

    try:
        file_bytes = await file.read()
    except Exception as exc:
        return {
            "status": "REJECTED",
            "tampered": False,
            "risk_score": 100,
            "confidence": 1,
            "file_type": "unknown",
            "summary": f"Evidence rejected: upload could not be read ({exc}).",
            "findings": [
                {
                    "severity": "High",
                    "page": 1,
                    "location": "file header",
                    "reason": "The uploaded evidence stream could not be read by the backend.",
                    "suggested_action": "Upload the evidence file again from local storage.",
                }
            ],
            "checks": {
                "file_exists": False,
                "allowed_type": False,
                "metadata_consistent": False,
                "tamper_indicators_found": False,
                "content_matches_required_evidence": False,
            },
        }

    return verify_evidence_from_upload(
        file_bytes=file_bytes,
        filename=file.filename,
        content_type=file.content_type,
        required_evidence=required_evidence,
    )


@router.get("/circulars")
def list_circulars():
    circulars = scan_circulars()
    return {
        "total": len(circulars),
        "circulars": [{"id": c["id"], "ingested_at": c["ingested_at"]} for c in circulars]
    }


@router.get("/circulars/{circular_id}")
def get_circular(circular_id: str):
    circular = get_circular_by_id(circular_id)
    if not circular:
        raise HTTPException(status_code=404, detail="Circular not found")
    return circular


@router.get("/health")
def compliance_health():
    return {"status": "Compliance engine online", "module": "compliance"}
