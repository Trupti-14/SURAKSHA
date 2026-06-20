from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from typing import Optional
from engines.compliance.workflow import run_compliance_workflow
from engines.compliance.scout import get_circular_by_id, parse_circular_text, scan_circulars
from engines.compliance.vision import verify_evidence_from_upload

router = APIRouter(prefix="/api/compliance", tags=["compliance"])

ROUTES = ["analyze", "evidence/verify", "circulars", "actions"]

SAMPLE_CIRCULARS = [
    {
        "id": "RBI-SYN-2026-001",
        "circular_id": "RBI-SYN-2026-001",
        "title": "Enhanced Digital Fraud Reporting Circular",
        "regulator": "Reserve Bank of India",
        "issue_date": "2026-06-01",
        "deadline": "within 4 hours",
        "category": "Digital Fraud / Reporting",
        "source": "local_seed",
        "status": "available",
        "summary": "Banks must accelerate digital fraud reporting, customer notification, evidence retention, and branch escalation.",
        "text": "Banks must report digital fraud cases within 4 hours, notify affected customers within 24 hours, retain fraud evidence for 5 years, and submit monthly fraud monitoring reports.",
        "priority_score": 10,
        "priority_label": "Critical",
        "priority_reason": "Digital fraud reporting has short regulatory timelines and evidence expectations.",
    }
]

SAMPLE_ACTIONS = [
    {
        "id": "MAP-001",
        "action": "Update fraud reporting SOP to enforce four-hour reporting.",
        "owner": "Fraud Risk Department Lead",
        "department": "Digital Banking Services / Internet Banking (IB)",
        "business_vertical": "Digital Banking Services",
        "sub_vertical": "Internet Banking (IB)",
        "deadline": "within 4 hours",
        "priority_score": 10,
        "priority_label": "Critical",
        "evidence_required": "Updated SOP, incident register, reporting timestamp, customer impact note, and audit trail",
        "status": "Pending Review",
        "reason": "Offline sample MAP available before a circular analysis has been run.",
        "linked_gap_id": "GAP-001",
        "source_obligation": "Banks must report digital fraud cases within 4 hours.",
        "acceptance_criteria": [
            "Fraud reporting SOP shows four-hour SLA.",
            "Incident register captures detection and reporting timestamps.",
            "Compliance Office has approved the evidence pack.",
        ],
        "regulatory_reference": "Master Direction on Digital Payment Security Controls",
        "official_link": "https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=12032",
        "assignment_basis": "Offline fallback MAP mapped to bank advisory table for digital fraud reporting.",
    }
]


class CircularRequest(BaseModel):
    circular_text: Optional[str] = None
    file_name: Optional[str] = None
    mode: Optional[str] = "offline"
    circular_id: Optional[str] = None
    content: Optional[str] = None


def _normalize_analyze_response(result: dict) -> dict:
    result = result or {}
    priority = result.get("priority") or {}
    return {
        "offline_mode": bool(result.get("offline_mode", True)),
        "summary": result.get("summary") or "Compliance analysis completed in offline mode.",
        "obligations": result.get("obligations") or [],
        "similar_circulars": result.get("similar_circulars") or [],
        "policy_gaps": result.get("policy_gaps") or [],
        "measurable_action_points": result.get("measurable_action_points") or [],
        "priority": {
            "priority_score": priority.get("priority_score", 0),
            "priority_label": priority.get("priority_label", "Low"),
            "priority_reason": priority.get("priority_reason", "Offline compliance priority fallback."),
        },
        "workflow": result.get("workflow") or [],
        "engine_notes": result.get("engine_notes") or [],
    }


def _circular_item_from_local(local_circular: dict) -> dict:
    circular_id = local_circular.get("id", "local_circular")
    content = ""
    parsed = {}

    try:
        full_circular = get_circular_by_id(circular_id)
        content = (full_circular or {}).get("content", "")
        parsed = parse_circular_text(content, file_name=f"{circular_id}.txt")
    except Exception:
        parsed = {}

    title = parsed.get("title") or circular_id.replace("_", " ").title()
    category = parsed.get("category") or "General Regulatory Compliance"
    summary = parsed.get("normalized_summary") or "Local regulatory circular available for offline analysis."

    return {
        "id": circular_id,
        "circular_id": circular_id,
        "title": title,
        "regulator": "Reserve Bank of India",
        "issue_date": parsed.get("issue_date") or "Local",
        "deadline": parsed.get("deadline") or "To be assessed",
        "category": category,
        "source": "local_seed",
        "status": "available",
        "summary": summary,
        "old_policy": "Existing local policy baseline will be compared during analysis.",
        "new_policy": summary,
        "detected_gap": "Run analysis to generate policy gaps.",
        "text": content,
        "priority_score": 5,
        "priority_label": "Medium",
        "priority_reason": "Priority is assigned after workflow analysis.",
    }


@router.post("/analyze")
def analyze_circular(request: CircularRequest):
    content = request.circular_text or request.content
    result = run_compliance_workflow(
        circular_text=content or "",
        file_name=request.file_name,
        mode=request.mode or "offline",
        circular_id=request.circular_id,
    )
    return _normalize_analyze_response(result)


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
    try:
        circulars = scan_circulars()
        items = [_circular_item_from_local(circular) for circular in circulars]
    except Exception:
        items = []

    if not items:
        items = SAMPLE_CIRCULARS

    return {
        "items": items,
        "circulars": items,
        "count": len(items),
        "total": len(items),
        "offline_mode": True,
    }


@router.get("/actions")
def list_actions():
    return {
        "items": SAMPLE_ACTIONS,
        "actions": SAMPLE_ACTIONS,
        "count": len(SAMPLE_ACTIONS),
        "offline_mode": True,
    }


@router.get("/circulars/{circular_id}")
def get_circular(circular_id: str):
    circular = get_circular_by_id(circular_id)
    if not circular:
        raise HTTPException(status_code=404, detail="Circular not found")
    return circular


@router.get("/health")
def compliance_health():
    return {
        "status": "ok",
        "module": "Member D Compliance",
        "offline_mode": True,
        "routes": ROUTES,
    }
