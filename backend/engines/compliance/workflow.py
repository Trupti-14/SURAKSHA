import re
from datetime import datetime

from .actions import extract_action_points
from .delta import compare_policy
from .priority import calculate_priority
from .scout import get_circular_by_id, parse_circular_text, scan_circulars

try:
    from .chroma_store import search_similar, store_circular
except Exception:
    search_similar = None
    store_circular = None


WORKFLOW_STAGES = [
    "Scout Parser",
    "Semantic Delta Agent",
    "MAP Generator",
    "Priority Calculator",
    "Evidence Verifier",
    "Compliance Report",
]

OBLIGATION_KEYWORDS = (
    "must",
    "shall",
    "required",
    "ensure",
    "submit",
    "maintain",
    "report",
    "implement",
    "deadline",
    "within",
)

DOMAIN_GAPS = (
    (
        ("two-factor", "2fa", "otp", "authentication", "mfa", "biometric"),
        "Existing customer authentication controls must be checked against the new authentication requirement.",
        "High",
    ),
    (
        ("kyc", "dormant", "re-verification", "reverification"),
        "Existing KYC procedures must be updated for the circular's re-verification and dormant-account controls.",
        "High",
    ),
    (
        ("fraud", "mule", "cyber", "payment", "suspicious"),
        "Fraud monitoring controls must be mapped to the circular's surveillance, escalation, and reporting expectations.",
        "Critical",
    ),
    (
        ("audit", "evidence", "log", "record", "retain", "trail"),
        "Evidence retention and audit trail controls must be aligned with the circular.",
        "Medium",
    ),
    (
        ("rbi", "regulator", "report", "submission", "penalty"),
        "Regulatory reporting ownership and submission evidence must be confirmed.",
        "High",
    ),
    (
        ("deadline", "within", "days", "implementation"),
        "Implementation tracking must be created for the circular deadline.",
        "Medium",
    ),
)


def _stage_status(completed_stage_names):
    return [
        {
            "stage": stage,
            "status": "pending" if stage == "Evidence Verifier" else (
                "completed" if stage in completed_stage_names else "completed_with_fallback"
            ),
        }
        for stage in WORKFLOW_STAGES
    ]


def _clean_text(value):
    if value is None:
        return ""
    return str(value).strip()


def _clean_line(line):
    return re.sub(r"^\s*[-*0-9.)]+\s*", "", line).strip()


def _deadline_days(content):
    matches = re.findall(r"within\s+(\d{1,3})\s+days|(\d{1,3})\s+days", content, flags=re.I)
    days = []
    for first, second in matches:
        value = first or second
        try:
            days.append(int(value))
        except ValueError:
            continue
    return min(days) if days else 30


def _department_for_action(action_text):
    lower_text = action_text.lower()
    if any(word in lower_text for word in ["kyc", "aml", "dormant"]):
        return "KYC Compliance Desk"
    if any(word in lower_text for word in ["fraud", "mule", "cyber", "payment"]):
        return "Fraud Risk Operations"
    if any(word in lower_text for word in ["authentication", "otp", "mfa", "biometric", "session"]):
        return "Digital Banking Security"
    if any(word in lower_text for word in ["report", "rbi", "regulator"]):
        return "Regulatory Reporting"
    if any(word in lower_text for word in ["audit", "evidence", "log", "record"]):
        return "Compliance Assurance"
    return "Compliance Operations"


def _evidence_required(action_text):
    lower_text = action_text.lower()
    if any(word in lower_text for word in ["kyc", "dormant", "re-verification", "reverification"]):
        return "KYC re-verification tracker, customer notification proof, and exception approval sample"
    if any(word in lower_text for word in ["fraud", "mule", "cyber", "payment"]):
        return "Fraud monitoring rule screenshot, alert export, and escalation register"
    if any(word in lower_text for word in ["authentication", "otp", "mfa", "biometric", "session"]):
        return "Authentication policy configuration screenshot and test transaction evidence"
    if any(word in lower_text for word in ["report", "rbi", "regulator", "submission"]):
        return "Regulatory report sample, submission timestamp, and maker-checker approval proof"
    if any(word in lower_text for word in ["audit", "evidence", "log", "record", "retain"]):
        return "Audit trail export and evidence retention confirmation"
    return "Owner sign-off note and implementation evidence pack"


def _parse_obligations(content):
    obligations = []
    for line in content.splitlines():
        cleaned = _clean_line(line)
        if len(cleaned) < 8:
            continue
        lower_line = cleaned.lower()
        if any(keyword in lower_line for keyword in OBLIGATION_KEYWORDS):
            obligations.append(cleaned)

    if obligations:
        return obligations[:8]

    sentences = re.split(r"(?<=[.!?])\s+", content)
    for sentence in sentences:
        cleaned = _clean_line(sentence)
        if len(cleaned) >= 25:
            obligations.append(cleaned)
        if len(obligations) >= 3:
            break

    return obligations


def _normalize_action_points(action_result, obligations, content):
    raw_points = []
    if isinstance(action_result, dict):
        raw_points = action_result.get("action_points") or []
    elif isinstance(action_result, list):
        raw_points = action_result

    if not raw_points and obligations:
        raw_points = [
            {
                "id": f"MAP-{index + 1:03d}",
                "action": obligation,
                "department": _department_for_action(obligation),
                "deadline_days": _deadline_days(content),
            }
            for index, obligation in enumerate(obligations[:5])
        ]

    normalized = []
    for index, point in enumerate(raw_points[:8]):
        if isinstance(point, dict):
            action_text = _clean_text(
                point.get("action")
                or point.get("action_point")
                or point.get("description")
                or point.get("title")
            )
            department = _clean_text(
                point.get("department")
                or point.get("owner")
                or point.get("assigned_to")
                or _department_for_action(action_text)
            )
            try:
                deadline_days = int(point.get("deadline_days", _deadline_days(action_text or content)))
            except (TypeError, ValueError):
                deadline_days = _deadline_days(action_text or content)
            action_id = _clean_text(point.get("id") or point.get("map_id") or f"MAP-{index + 1:03d}")
        else:
            action_text = _clean_text(point)
            department = _department_for_action(action_text)
            deadline_days = _deadline_days(action_text or content)
            action_id = f"MAP-{index + 1:03d}"

        if not action_text:
            continue

        normalized.append(
            {
                "id": action_id,
                "action": action_text,
                "owner": point.get("owner") if isinstance(point, dict) else f"{department} Lead",
                "department": department or _department_for_action(action_text),
                "deadline": point.get("deadline") if isinstance(point, dict) else None,
                "deadline_days": deadline_days,
                "evidence_required": (
                    point.get("evidence_required")
                    if isinstance(point, dict) and point.get("evidence_required")
                    else _evidence_required(action_text)
                ),
                "status": point.get("status", "Pending Review") if isinstance(point, dict) else "Pending Review",
                "reason": point.get("reason") if isinstance(point, dict) else "Generated from compliance workflow.",
                "linked_gap_id": point.get("linked_gap_id") if isinstance(point, dict) else None,
                "source_obligation": point.get("source_obligation") if isinstance(point, dict) else action_text,
                "acceptance_criteria": (
                    point.get("acceptance_criteria")
                    if isinstance(point, dict) and point.get("acceptance_criteria")
                    else ["Compliance Office review and evidence verification completed."]
                ),
                "business_vertical": point.get("business_vertical") if isinstance(point, dict) else None,
                "sub_vertical": point.get("sub_vertical") if isinstance(point, dict) else None,
                "primary_regulator": point.get("primary_regulator") if isinstance(point, dict) else None,
                "regulatory_reference": point.get("regulatory_reference") if isinstance(point, dict) else None,
                "official_link": point.get("official_link") if isinstance(point, dict) else None,
                "assignment_basis": point.get("assignment_basis") if isinstance(point, dict) else None,
            }
        )

    return normalized


def _normalize_key_changes(key_changes):
    normalized = []
    if not isinstance(key_changes, list):
        return normalized

    for change in key_changes:
        if isinstance(change, str):
            cleaned = _clean_text(change)
        elif isinstance(change, dict):
            cleaned = _clean_text(
                change.get("change")
                or change.get("summary")
                or change.get("description")
                or change.get("requirement")
            )
        else:
            cleaned = ""
        if cleaned:
            normalized.append(cleaned)
    return normalized[:5]


def _build_policy_gaps(content, delta_result, obligations):
    if isinstance(delta_result.get("policy_gaps"), list) and delta_result.get("policy_gaps"):
        return delta_result["policy_gaps"][:8]

    lower_content = content.lower()
    gaps = []

    for change in _normalize_key_changes(delta_result.get("key_changes")):
        gaps.append(
            {
                "gap": change,
                "severity": "Medium",
                "source": "Semantic Delta Agent",
            }
        )

    existing_gap_text = {gap["gap"] for gap in gaps}
    for keywords, message, severity in DOMAIN_GAPS:
        if any(keyword in lower_content for keyword in keywords) and message not in existing_gap_text:
            gaps.append(
                {
                    "gap": message,
                    "severity": severity,
                    "source": "Offline policy mapping",
                }
            )
        if len(gaps) >= 5:
            break

    if not gaps and obligations:
        gaps.append(
            {
                "gap": "Manual policy gap review is required for the extracted circular obligations.",
                "severity": "Medium",
                "source": "Offline fallback",
            }
        )

    return gaps[:5]


def _summary(file_name, action_points, policy_gaps, priority):
    source_name = file_name or "uploaded circular"
    return (
        f"Offline compliance workflow completed for {source_name}: "
        f"{len(action_points)} measurable action point(s), "
        f"{len(policy_gaps)} policy gap(s), highest priority "
        f"{priority['priority_label']} ({priority['priority_score']}/10)."
    )


def _overall_priority(prioritized_actions):
    if not prioritized_actions:
        return {
            "priority_score": 0,
            "priority_label": "Low",
            "priority_reason": "No measurable action points were generated from the provided circular text.",
        }

    top_action = prioritized_actions[0]
    return {
        "priority_score": int(top_action.get("priority_score", 0)),
        "priority_label": top_action.get("priority_label", "Low"),
        "priority_reason": top_action.get(
            "priority_reason",
            f"Based on highest-scoring action point: {top_action.get('action', 'review required')}.",
        ),
    }


def _empty_report(engine_notes):
    priority = {
        "priority_score": 0,
        "priority_label": "Low",
        "priority_reason": "No circular text was provided for analysis.",
    }
    return {
        "offline_mode": True,
        "summary": "No circular text was provided. Offline workflow returned a safe empty compliance report.",
        "obligations": [],
        "similar_circulars": [],
        "policy_gaps": [],
        "measurable_action_points": [],
        "priority": priority,
        "workflow": _stage_status(set(WORKFLOW_STAGES) - {"Evidence Verifier"}),
        "engine_notes": engine_notes
        + [
            "Scout Parser completed with empty input.",
            "Evidence Verifier is pending and must be run through /api/compliance/evidence/verify.",
        ],
    }


def _safe_chroma(content, file_name, mode, engine_notes):
    similar_circulars = []
    if not content:
        return similar_circulars

    if search_similar is None or store_circular is None:
        engine_notes.append("ChromaDB functions are unavailable; similar-circular lookup skipped.")
        return similar_circulars

    try:
        similar = search_similar(content, n_results=3) or []
        similar_circulars = [
            {
                "id": item.get("id", ""),
                "summary": (item.get("content", "") or "")[:180],
            }
            for item in similar
            if isinstance(item, dict)
        ]
    except Exception as exc:
        engine_notes.append(f"ChromaDB similar-circular lookup failed safely: {exc}.")

    try:
        store_result = store_circular(
            file_name or "uploaded_circular",
            content,
            {"file_name": file_name or "unknown", "mode": mode or "offline"},
        )
        if isinstance(store_result, dict) and store_result.get("status") in {"skipped", "error"}:
            engine_notes.append(
                f"ChromaDB storage skipped safely: {store_result.get('reason', 'unavailable')}."
            )
    except Exception as exc:
        engine_notes.append(f"ChromaDB storage failed safely: {exc}.")

    return similar_circulars


def run_compliance_workflow(
    circular_text=None,
    file_name=None,
    mode="offline",
    circular_id=None,
    new_content=None,
    content=None,
):
    """
    Run the Member D compliance agent chain and return the frontend schema.

    The signature accepts the current API shape plus the older circular_id /
    new_content shape so existing local callers keep working.
    """
    engine_notes = ["Offline/local workflow active. No cloud API is required."]
    completed_stages = set()

    input_text = _clean_text(circular_text if circular_text is not None else new_content)
    if content is not None and not input_text:
        input_text = _clean_text(content)

    try:
        local_circulars = scan_circulars()
        engine_notes.append(f"Scout Parser saw {len(local_circulars)} local circular record(s).")
    except Exception as exc:
        local_circulars = []
        engine_notes.append(f"Scout Parser local circular scan failed safely: {exc}.")

    if circular_id and not input_text:
        try:
            circular = get_circular_by_id(circular_id)
            if circular:
                input_text = _clean_text(circular.get("content"))
                file_name = file_name or f"{circular_id}.txt"
                engine_notes.append(f"Scout Parser loaded circular_id {circular_id}.")
            else:
                engine_notes.append(f"Scout Parser could not find circular_id {circular_id}; using empty input.")
        except Exception as exc:
            engine_notes.append(f"Scout Parser failed to load circular_id {circular_id}: {exc}.")

    completed_stages.add("Scout Parser")

    if not input_text:
        return _empty_report(engine_notes)

    try:
        scout_result = parse_circular_text(input_text, file_name=file_name)
        engine_notes.extend(scout_result.get("engine_notes", []))
    except Exception as exc:
        scout_result = {
            "obligations": _parse_obligations(input_text),
            "risk_keywords": [],
            "affected_departments": ["Compliance Office"],
            "evidence_required": ["Manual compliance review record"],
            "normalized_summary": "Scout fallback used after parser failure.",
        }
        engine_notes.append(f"Scout Parser failed safely: {exc}.")

    obligations = scout_result.get("obligations") or []
    if obligations:
        engine_notes.append(f"Scout Parser extracted {len(obligations)} obligation candidate(s).")
    else:
        engine_notes.append("Scout Parser found no explicit obligations; MAP fallback may be limited.")

    prior_documents = []
    for local_circular in local_circulars:
        local_id = local_circular.get("id")
        if not local_id or local_id == circular_id:
            continue
        try:
            circular = get_circular_by_id(local_id)
            if circular and circular.get("content"):
                prior_documents.append(
                    {
                        "id": local_id,
                        "content": circular["content"],
                        "source": "local_regulatory_memory",
                    }
                )
        except Exception as exc:
            engine_notes.append(f"Prior circular {local_id} could not be loaded for Delta: {exc}.")

    try:
        delta_result = compare_policy(
            old_policy=None,
            new_policy=input_text,
            scout_result=scout_result,
            prior_documents=prior_documents,
        ) or {}
        engine_notes.extend(delta_result.get("engine_notes", []))
        engine_notes.append("Semantic Delta Agent returned deterministic structured policy gaps.")
    except Exception as exc:
        delta_result = {
            "gap_found": bool(obligations),
            "summary": "Delta comparison fallback used after agent failure.",
            "risk_level": "MEDIUM",
            "key_changes": [],
            "policy_gaps": [],
            "analysis_by": "fallback",
        }
        engine_notes.append(f"Semantic Delta Agent failed safely: {exc}.")
    completed_stages.add("Semantic Delta Agent")

    policy_gaps = _build_policy_gaps(input_text, delta_result, obligations)

    try:
        action_result = extract_action_points(
            input_text,
            scout_result=scout_result,
            delta_result={**delta_result, "policy_gaps": policy_gaps},
        ) or {}
        engine_notes.extend(action_result.get("engine_notes", []))
        if not action_result.get("action_points"):
            engine_notes.append("MAP Generator returned no structured actions; obligation fallback used if available.")
    except Exception as exc:
        action_result = {"action_points": []}
        engine_notes.append(f"MAP Generator failed safely: {exc}.")
    completed_stages.add("MAP Generator")

    action_points = _normalize_action_points(action_result, obligations, input_text)

    try:
        prioritized_actions = calculate_priority(action_points)
    except Exception as exc:
        prioritized_actions = [
            {
                **point,
                "priority_score": 5,
                "priority_label": "Medium",
                "priority_reason": "Priority fallback applied after calculator failure.",
                "calculated_at": datetime.utcnow().isoformat(),
            }
            for point in action_points
        ]
        engine_notes.append(f"Priority Calculator failed safely: {exc}.")
    completed_stages.add("Priority Calculator")

    for index, action in enumerate(prioritized_actions, start=1):
        action["id"] = f"MAP-{index:03d}"

    priority = _overall_priority(prioritized_actions)
    similar_circulars = _safe_chroma(input_text, file_name, mode, engine_notes)

    completed_stages.add("Compliance Report")
    engine_notes.append("Evidence Verifier is pending; upload evidence through /api/compliance/evidence/verify.")

    return {
        "offline_mode": True,
        "summary": _summary(file_name, prioritized_actions, policy_gaps, priority),
        "obligations": obligations,
        "similar_circulars": similar_circulars,
        "policy_gaps": policy_gaps,
        "measurable_action_points": prioritized_actions,
        "priority": priority,
        "workflow": _stage_status(completed_stages),
        "engine_notes": engine_notes,
    }
