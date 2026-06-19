from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from typing import Optional
from engines.compliance.workflow import run_compliance_workflow
from engines.compliance.scout import scan_circulars, get_circular_by_id
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
    content = request.circular_text or request.content
    return run_compliance_workflow(
        circular_text=content or "",
        file_name=request.file_name,
        mode=request.mode or "offline",
        circular_id=request.circular_id,
    )


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
