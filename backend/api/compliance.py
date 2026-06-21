import re
from io import BytesIO
from datetime import datetime

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from typing import Optional
from engines.compliance.workflow import run_compliance_workflow
from engines.compliance.scout import CIRCULARS_DIR, get_circular_by_id, parse_circular_text, scan_circulars
from engines.compliance.vision import verify_evidence_from_upload
from engines.compliance.chroma_store import (
    add_circular,
    clean_reference_text,
    list_circulars as list_memory_circulars,
)

router = APIRouter(prefix="/api/compliance", tags=["compliance"])

ROUTES = ["analyze", "evidence/verify", "circulars", "actions", "references"]

REFERENCE_DOMAINS = {
    "digital_fraud",
    "it_outsourcing",
    "kyc_aml",
    "cyber_incident",
    "digital_payment",
    "mobile_banking",
    "digital_lending",
    "bcp_drp",
    "audit_governance",
    "general_compliance",
}

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


class ReferenceCircularRequest(BaseModel):
    title: Optional[str] = None
    domain: Optional[str] = None
    category: Optional[str] = None
    circular_text: Optional[str] = None
    file_name: Optional[str] = None


def _clean_required(value: Optional[str], field_name: str) -> str:
    cleaned = (value or "").strip()
    if not cleaned:
        raise HTTPException(status_code=400, detail=f"{field_name} is required")
    return cleaned


def _safe_title_slug(title: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", title.strip()).strip("-").upper()
    return slug[:48] or "REFERENCE"


def _new_reference_circular_id(title: str) -> str:
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    return f"USER-REF-{_safe_title_slug(title)}-{timestamp}"


def _store_reference_file(circular_id: str, circular_text: str) -> None:
    CIRCULARS_DIR.mkdir(parents=True, exist_ok=True)
    reference_path = CIRCULARS_DIR / f"{circular_id}.txt"
    reference_path.write_text(circular_text, encoding="utf-8")


def _validate_reference_domain(domain: str) -> None:
    if domain not in REFERENCE_DOMAINS:
        allowed = ", ".join(sorted(REFERENCE_DOMAINS))
        raise HTTPException(status_code=400, detail=f"domain must be one of: {allowed}")


def _store_reference_circular(
    *,
    title: str,
    domain: str,
    category: str,
    circular_text: str,
    file_name: str = "",
) -> dict:
    circular_text = clean_reference_text(circular_text)
    if len(circular_text) < 100:
        raise HTTPException(
            status_code=400,
            detail="circular_text must be at least 100 characters",
        )

    _validate_reference_domain(domain)

    circular_id = _new_reference_circular_id(title)
    stored_at = datetime.utcnow().isoformat()
    metadata = {
        "circular_id": circular_id,
        "title": title,
        "domain": domain,
        "category": category,
        "regulator": "Reserve Bank of India",
        "source": "user_added_reference",
        "source_type": "User added approved reference",
        "file_name": file_name or f"{circular_id}.txt",
        "stored_at": stored_at,
        "status": "available",
    }

    try:
        _store_reference_file(circular_id, circular_text)
        storage_result = add_circular({**metadata, "content": circular_text})
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Reference circular could not be stored: {exc}",
        ) from exc

    if storage_result.get("status") not in {"stored", "stored_fallback"}:
        raise HTTPException(
            status_code=500,
            detail=storage_result.get("reason") or "Reference circular could not be stored",
        )

    return {
        "status": "stored",
        "circular_id": circular_id,
        "title": title,
        "domain": domain,
        "message": "Reference circular added to Policy Reference Library",
    }


def _decode_txt_upload(file_bytes: bytes) -> str:
    try:
        return file_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="TXT file must be UTF-8 encoded.") from exc


def _extract_pdf_text(file_bytes: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise HTTPException(
            status_code=500,
            detail="PDF extraction dependency is not available. Paste the PDF text manually or install pypdf.",
        ) from exc

    try:
        reader = PdfReader(BytesIO(file_bytes))
        page_text = [page.extract_text() or "" for page in reader.pages]
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="PDF text extraction failed. Paste the PDF text manually for this prototype.",
        ) from exc

    extracted_text = "\n\n".join(text.strip() for text in page_text if text.strip()).strip()
    if not extracted_text:
        raise HTTPException(
            status_code=400,
            detail="No readable text found in this PDF. Paste the text manually for this prototype.",
        )
    return extracted_text


def _normalize_analyze_response(result: dict) -> dict:
    result = result or {}
    priority = result.get("priority") or {}
    return {
        "offline_mode": bool(result.get("offline_mode", True)),
        "summary": result.get("summary") or "Compliance analysis completed in offline mode.",
        "obligations": result.get("obligations") or [],
        "similar_circulars": result.get("similar_circulars") or [],
        "policy_gaps": _normalize_policy_gap_references(result.get("policy_gaps") or []),
        "measurable_action_points": result.get("measurable_action_points") or [],
        "priority": {
            "priority_score": priority.get("priority_score", 0),
            "priority_label": priority.get("priority_label", "Low"),
            "priority_reason": priority.get("priority_reason", "Offline compliance priority fallback."),
        },
        "workflow": result.get("workflow") or [],
        "engine_notes": result.get("engine_notes") or [],
    }


def _normalize_policy_gap_references(policy_gaps: list) -> list:
    normalized = []
    for gap in policy_gaps:
        if not isinstance(gap, dict):
            normalized.append(gap)
            continue

        existing_reference = (
            gap.get("existing_reference")
            or gap.get("old_requirement")
            or gap.get("old_policy")
            or gap.get("existing_requirement")
            or gap.get("current_policy")
        )
        if existing_reference:
            gap = {
                **gap,
                "existing_reference": existing_reference,
                "old_requirement": gap.get("old_requirement") or existing_reference,
            }
        normalized.append(gap)
    return normalized


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


def _circular_item_from_memory(memory_circular: dict) -> dict:
    metadata = memory_circular.get("metadata") or {}
    circular_id = memory_circular.get("circular_id") or memory_circular.get("id") or metadata.get("circular_id")
    title = memory_circular.get("title") or metadata.get("title") or circular_id
    category = memory_circular.get("category") or metadata.get("category") or "Regulatory Compliance"
    content = memory_circular.get("content") or ""
    summary = memory_circular.get("content_excerpt") or "Seeded regulatory memory circular available for analysis."
    return {
        "id": circular_id,
        "circular_id": circular_id,
        "title": title,
        "regulator": metadata.get("regulator", "Reserve Bank of India"),
        "issue_date": metadata.get("issue_date", "Local"),
        "deadline": metadata.get("deadline", "To be assessed"),
        "category": category,
        "domain": metadata.get("domain", "general_compliance"),
        "source": memory_circular.get("source", "regulatory_memory"),
        "source_type": metadata.get("source_type", "Regulatory memory"),
        "file_name": metadata.get("file_name", ""),
        "stored_at": metadata.get("stored_at", ""),
        "status": "available",
        "summary": summary,
        "old_policy": "Seeded regulatory memory baseline.",
        "new_policy": summary,
        "detected_gap": "Run analysis to compare a new circular against this memory.",
        "text": content,
        "priority_score": 5,
        "priority_label": "Medium",
        "priority_reason": "Priority is assigned after workflow analysis.",
        "regulatory_reference": metadata.get("title", title),
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


@router.post("/references")
def add_reference_circular(request: ReferenceCircularRequest):
    title = _clean_required(request.title, "title")
    domain = _clean_required(request.domain, "domain")
    circular_text = _clean_required(request.circular_text, "circular_text")
    category = (request.category or "").strip() or "Regulatory Compliance"
    file_name = (request.file_name or "").strip()

    return _store_reference_circular(
        title=title,
        domain=domain,
        category=category,
        circular_text=circular_text,
        file_name=file_name,
    )


@router.post("/references/upload")
async def upload_reference_circular(
    title: Optional[str] = Form(default=None),
    domain: Optional[str] = Form(default=None),
    category: Optional[str] = Form(default=None),
    file: Optional[UploadFile] = File(default=None),
):
    title = _clean_required(title, "title")
    domain = _clean_required(domain, "domain")
    category = (category or "").strip() or "Regulatory Compliance"
    _validate_reference_domain(domain)

    if file is None:
        raise HTTPException(status_code=400, detail="file is required")

    file_name = (file.filename or "").strip()
    extension = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
    if extension not in {"txt", "pdf"}:
        raise HTTPException(status_code=400, detail="Only TXT or PDF upload is supported here.")

    try:
        file_bytes = await file.read()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Uploaded file could not be read: {exc}") from exc

    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if extension == "txt":
        circular_text = _decode_txt_upload(file_bytes).strip()
    else:
        circular_text = _extract_pdf_text(file_bytes).strip()

    if not circular_text:
        if extension == "pdf":
            raise HTTPException(
                status_code=400,
                detail="No readable text found in this PDF. Paste the text manually for this prototype.",
            )
        raise HTTPException(status_code=400, detail="Uploaded TXT file is empty.")

    stored = _store_reference_circular(
        title=title,
        domain=domain,
        category=category,
        circular_text=circular_text,
        file_name=file_name,
    )
    return {
        **stored,
        "extracted_characters": len(circular_text),
        "file_name": file_name,
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
    try:
        memory_items = [_circular_item_from_memory(item) for item in list_memory_circulars()]
    except Exception:
        memory_items = []

    if memory_items:
        return {
            "items": memory_items,
            "circulars": memory_items,
            "count": len(memory_items),
            "total": len(memory_items),
            "offline_mode": True,
        }

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
