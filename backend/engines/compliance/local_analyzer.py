"""Local circular analyzer for the Member D compliance backend.

The analyzer connects the offline compliance support modules into one
structured pipeline. It is designed for future FastAPI integration and does not
require internet, cloud services, or a local LLM to run.
"""

from __future__ import annotations

from datetime import date, timedelta
import json
from pathlib import Path
import re
import sys
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from backend.engines.compliance import actions, chroma_store, local_llm, priority
except ModuleNotFoundError:
    try:
        from engines.compliance import actions, chroma_store, local_llm, priority
    except ModuleNotFoundError:
        actions = None
        chroma_store = None
        local_llm = None
        priority = None


WORKFLOW_STAGES = (
    "Circular Received",
    "Local Summary",
    "Obligation Extraction",
    "Regulatory Memory Search",
    "Policy Gap Detection",
    "MAP Generation",
    "Priority Scoring",
)

OBLIGATION_TERMS = (
    "must",
    "shall",
    "required",
    "mandatory",
    "report",
    "retain",
    "review",
    "complete",
    "submit",
)


def _sentences(text: str) -> list[str]:
    candidates = re.split(r"(?<=[.!?])\s+", text.strip())
    return [sentence.strip() for sentence in candidates if sentence.strip()]


def _fallback_summary(text: str) -> str:
    sentences = _sentences(text)
    if not sentences:
        return "No circular content was available for summary."
    return " ".join(sentences[:2])


def _fallback_obligations(text: str) -> list[str]:
    obligations = []
    for sentence in _sentences(text):
        lowered = sentence.lower()
        if any(term in lowered for term in OBLIGATION_TERMS):
            obligations.append(sentence)
    return obligations or [_fallback_summary(text)]


def _fallback_priority(circular: dict[str, Any]) -> dict[str, Any]:
    text = " ".join(str(circular.get(field, "")) for field in ("title", "summary", "text"))
    lowered = text.lower()
    score = 3
    reasons = ["base compliance review"]

    if any(term in lowered for term in ("fraud", "mule", "cyber", "payment")):
        score += 3
        reasons.append("risk-sensitive circular language")
    if any(term in lowered for term in ("mandatory", "penalty", "report", "customer")):
        score += 2
        reasons.append("reporting or customer impact obligation")

    score = max(1, min(10, score))
    if score >= 8:
        label = "Critical"
    elif score >= 6:
        label = "High"
    elif score >= 4:
        label = "Medium"
    else:
        label = "Low"

    return {
        "priority_score": score,
        "priority_label": label,
        "priority_reason": "; ".join(reasons),
    }


def _fallback_actions(circular: dict[str, Any], obligations: list[str]) -> list[dict[str, Any]]:
    deadline = circular.get("deadline") or str(date.today() + timedelta(days=30))
    circular_id = str(circular.get("circular_id") or "LOCAL-UPLOAD")
    selected_obligations = obligations[:3] or ["Review circular and record compliance action."]

    generated_actions = []
    for index, obligation in enumerate(selected_obligations, start=1):
        generated_actions.append(
            {
                "id": f"MAP-{circular_id}-{index:02d}",
                "circular_id": circular_id,
                "action": obligation,
                "owner": "Compliance Office",
                "deadline": deadline,
                "priority_score": circular.get("priority_score"),
                "priority_label": circular.get("priority_label"),
                "evidence_required": "Compliance review note and supporting evidence pack",
                "status": "Pending Review",
                "reason": "Generated from circular obligation identified during local analysis.",
            }
        )

    return generated_actions


def _detect_policy_gaps(
    circular_text: str,
    obligations: list[str],
    similar_circulars: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []

    for circular in similar_circulars[:2]:
        detected_gap = circular.get("detected_gap")
        if detected_gap:
            gaps.append(
                {
                    "source": circular.get("circular_id", "local-memory"),
                    "policy_gap": detected_gap,
                    "basis": "Similar circular in local regulatory memory contains a recorded policy gap.",
                }
            )

    lower_text = circular_text.lower()
    gap_patterns = [
        ("reporting", "Reporting cadence or evidence submission may need review."),
        ("customer impact", "Customer-impact handling may require documented controls."),
        ("deadline", "Implementation timeline may need ownership and tracking."),
        ("mandatory", "Mandatory obligation may require formal control mapping."),
        ("retain", "Evidence retention expectations may require audit-ready proof."),
    ]
    for keyword, message in gap_patterns:
        if keyword in lower_text and not any(keyword in gap["policy_gap"].lower() for gap in gaps):
            gaps.append(
                {
                    "source": "uploaded-circular",
                    "policy_gap": message,
                    "basis": f"Keyword '{keyword}' was identified in the uploaded circular.",
                }
            )

    if not gaps and obligations:
        gaps.append(
            {
                "source": "uploaded-circular",
                "policy_gap": "New obligations should be mapped against existing policy controls.",
                "basis": "Obligations were identified, but no matching policy gap was already recorded.",
            }
        )

    return gaps


def _workflow(status: str = "completed") -> list[dict[str, str]]:
    return [{"stage": stage, "status": status} for stage in WORKFLOW_STAGES]


def _build_circular_context(circular_text: str, file_name: str | None) -> dict[str, Any]:
    display_name = Path(file_name).stem if file_name else "uploaded-circular"
    return {
        "circular_id": f"LOCAL-{display_name.upper().replace(' ', '-')}",
        "title": display_name.replace("_", " ").replace("-", " ").title(),
        "category": "Regulatory Compliance",
        "summary": _fallback_summary(circular_text),
        "text": circular_text,
        "deadline": str(date.today() + timedelta(days=30)),
    }


def analyze_uploaded_circular(
    circular_text: str,
    file_name: str | None = None,
) -> dict[str, Any]:
    """Analyze one uploaded circular using local offline compliance modules."""

    text = str(circular_text or "").strip()
    if not text:
        return {
            "offline_mode": True,
            "file_name": file_name,
            "summary": "",
            "obligations": [],
            "similar_circulars": [],
            "policy_gaps": [],
            "measurable_action_points": [],
            "priority": {
                "priority_score": 0,
                "priority_label": "Invalid",
                "priority_reason": "Circular text is required for compliance analysis.",
            },
            "workflow": _workflow("not_started"),
            "engine_notes": [
                "Circular text was empty. No compliance analysis was performed.",
                "No external AI, internet, scraping, or cloud API was used.",
            ],
        }

    engine_notes = [
        "Local offline analyzer executed without internet, scraping, or cloud APIs.",
        "Local LLM support is optional; deterministic compliance fallback remains available.",
    ]
    circular_context = _build_circular_context(text, file_name)

    try:
        summary = (
            local_llm.summarize_policy_text(text)
            if local_llm is not None
            else _fallback_summary(text)
        )
    except Exception:
        summary = _fallback_summary(text)
        engine_notes.append("Summary fallback was used due to a local analyzer exception.")

    try:
        obligations = (
            local_llm.extract_obligations_with_fallback(text)
            if local_llm is not None
            else _fallback_obligations(text)
        )
    except Exception:
        obligations = _fallback_obligations(text)
        engine_notes.append("Obligation fallback was used due to a local analyzer exception.")

    try:
        similar_circulars = (
            chroma_store.search_similar(text, top_k=3)
            if chroma_store is not None
            else []
        )
    except Exception:
        similar_circulars = []
        engine_notes.append("Regulatory memory search was unavailable during analysis.")

    policy_gaps = _detect_policy_gaps(text, obligations, similar_circulars)

    try:
        priority_result = (
            priority.calculate_priority(circular_context)
            if priority is not None
            else _fallback_priority(circular_context)
        )
    except Exception:
        priority_result = _fallback_priority(circular_context)
        engine_notes.append("Priority fallback was used due to a local analyzer exception.")

    circular_context.update(priority_result)

    try:
        measurable_action_points = (
            actions.generate_action_points([circular_context])
            if actions is not None
            else _fallback_actions(circular_context, obligations)
        )
    except Exception:
        measurable_action_points = _fallback_actions(circular_context, obligations)
        engine_notes.append("MAP fallback was used due to a local analyzer exception.")

    return {
        "offline_mode": True,
        "file_name": file_name,
        "summary": summary,
        "obligations": obligations,
        "similar_circulars": similar_circulars,
        "policy_gaps": policy_gaps,
        "measurable_action_points": measurable_action_points,
        "priority": priority_result,
        "workflow": _workflow(),
        "engine_notes": engine_notes,
    }


if __name__ == "__main__":
    sample_text = (
        "Banks must review digital fraud reporting controls and retain evidence "
        "for compliance audit. Customer impact notes and implementation deadline "
        "tracking are required for branch and central compliance teams."
    )
    result = analyze_uploaded_circular(sample_text, file_name="sample_circular.txt")
    print(json.dumps(result, indent=2, ensure_ascii=False))
