import re

from .scout import parse_circular_text


DEPARTMENT_RULES = (
    ("Fraud Risk Department", ("fraud", "mule account", "mule", "digital fraud", "payment fraud", "reporting")),
    ("Cybersecurity / IT Security", ("cyber", "security log", "digital evidence", "incident", "authentication")),
    ("KYC / AML Compliance", ("kyc", "aml", "verification", "suspicious account", "dormant")),
    ("Customer Support / Grievance Cell", ("customer", "notify", "notification", "grievance", "complaint")),
    ("Branch Operations", ("branch", "branch-level", "escalation")),
    ("Internal Audit", ("audit", "audit trail", "evidence retention", "retain", "preserve", "archive")),
    ("Legal Department", ("legal", "disclose", "regulatory interpretation")),
    ("Data Privacy / DPDP Office", ("dpdp", "privacy", "personal data", "customer data")),
    ("Operations Department", ("operations", "reconcile", "process")),
    ("Risk Management", ("operational risk", "enterprise risk", "risk")),
    ("Compliance Office", ("rbi", "compliance", "regulatory", "submit", "report")),
)

EVIDENCE_RULES = (
    ("Fraud incident register, reporting timestamp, customer impact note, and evidence reference", ("fraud", "digital fraud", "payment fraud", "mule")),
    ("Customer notification proof, delivery timestamp, and exception approval log", ("customer", "notify", "notification", "grievance")),
    ("Evidence archive inventory, retention proof, and audit trail export", ("retain", "preserve", "evidence", "audit trail", "archive")),
    ("Monthly report sample, maker-checker approval, and Compliance Office submission proof", ("monthly", "report", "submit")),
    ("Branch escalation register, owner sign-off, and closure timestamp", ("branch", "escalate", "branch-level")),
    ("Security log export, incident ticket, digital evidence hash, and containment note", ("cyber", "security", "digital evidence", "incident")),
    ("KYC/AML review tracker, suspicious account review note, and exception approval sample", ("kyc", "aml", "verification", "suspicious account")),
    ("DPDP/privacy assessment note and customer data handling approval", ("dpdp", "privacy", "personal data")),
)


def _normalize_space(value):
    return re.sub(r"\s+", " ", value or "").strip()


def _dedupe_action_points(action_points):
    deduped = []
    seen = set()
    for action_point in action_points:
        key = re.sub(r"[^a-z0-9]+", " ", action_point["action"].lower()).strip()
        if key and key not in seen:
            deduped.append(action_point)
            seen.add(key)
    return deduped


def _deadline_text(text, fallback=None):
    patterns = (
        r"within\s+\d{1,3}\s+(?:hours?|days?|months?|years?)",
        r"for\s+\d{1,3}\s+years?",
        r"by\s+\d{1,2}[/-]\d{1,2}[/-]\d{2,4}",
        r"no later than\s+[A-Za-z0-9 ,/-]+",
        r"before end of month",
        r"with immediate effect",
        r"immediate effect",
        r"monthly",
        r"quarterly",
        r"annually",
        r"annual",
    )
    for pattern in patterns:
        match = re.search(pattern, text or "", flags=re.I)
        if match:
            return _normalize_space(match.group(0))
    return fallback or "To be assigned by Compliance Office"


def _deadline_days(deadline):
    lower = (deadline or "").lower()
    number_match = re.search(r"(\d{1,4})", lower)
    number = int(number_match.group(1)) if number_match else None

    if "hour" in lower:
        return 1
    if "day" in lower and number is not None:
        return number
    if "month" in lower or "monthly" in lower:
        return 30
    if "quarter" in lower or "quarterly" in lower:
        return 90
    if "annual" in lower or "year" in lower:
        return 365 if "within" in lower else 30
    if "immediate" in lower:
        return 1
    return 30


def _department_for_text(text, fallback=None):
    lower = (text or "").lower()
    matched = []
    for department, terms in DEPARTMENT_RULES:
        if any(term in lower for term in terms):
            matched.append(department)

    if matched:
        if "Fraud Risk Department" in matched and "Compliance Office" not in matched and "report" in lower:
            matched.append("Compliance Office")
        return " + ".join(matched[:2])
    return fallback or "Compliance Office"


def _owner_for_department(department):
    if "+" in department:
        return f"{department.split('+')[0].strip()} Lead with Compliance Office coordination"
    return f"{department} Lead"


def _evidence_for_text(text, fallback=None):
    lower = (text or "").lower()
    evidence = []
    for evidence_item, terms in EVIDENCE_RULES:
        if any(term in lower for term in terms):
            evidence.append(evidence_item)
    if evidence:
        return evidence[0]
    return fallback or "Implementation evidence pack, owner sign-off, and compliance review note"


def _priority(deadline_days, text, severity=None):
    score = 4
    lower = (text or "").lower()

    if deadline_days <= 1:
        score = 10
    elif deadline_days <= 7:
        score = 9
    elif deadline_days <= 15:
        score = 8
    elif deadline_days <= 30:
        score = 6

    if any(term in lower for term in ("fraud", "cyber", "mule", "customer", "kyc", "aml")):
        score = min(10, score + 1)
    if severity == "Critical":
        score = max(score, 9)
    elif severity == "High":
        score = max(score, 7)

    if score >= 9:
        label = "Critical"
    elif score >= 7:
        label = "High"
    elif score >= 5:
        label = "Medium"
    else:
        label = "Low"
    return score, label


def _action_template(text, change_type=None):
    lower = (text or "").lower()
    if "monthly" in lower and ("report" in lower or "submit" in lower):
        return "Submit monthly monitoring report with maker-checker approval and Compliance Office sign-off."
    if "fraud" in lower and ("4 hours" in lower or "report" in lower):
        return "Update fraud reporting SOP to enforce RBI-mandated reporting timelines and evidence capture."
    if "notify" in lower or "customer notification" in lower:
        return "Create customer notification workflow with timestamped proof and exception approval tracking."
    if "retain" in lower or "preserve" in lower or "evidence" in lower:
        return "Implement evidence retention control with archive inventory and audit trail export."
    if "branch" in lower or "escalat" in lower:
        return "Define branch-level escalation path with owner assignment, SLA, and closure evidence."
    if "audit trail" in lower or "audit" in lower:
        return "Configure audit trail review process and retain evidence for compliance testing."
    if "kyc" in lower or "aml" in lower:
        return "Update KYC/AML operating procedure and exception tracker for the new circular requirement."
    if "cyber" in lower or "security" in lower:
        return "Configure cybersecurity evidence capture and incident review workflow for the circular requirement."
    if change_type == "department_owner_missing":
        return "Assign department owner and escalation path for the new compliance requirement."
    return f"Implement compliance control for: {_normalize_space(text)[:180]}"


def _acceptance_criteria(action, evidence_required, deadline):
    return [
        f"Approved SOP/control update exists for: {action}",
        f"Evidence available: {evidence_required}",
        f"Deadline/SLA captured as {deadline}",
        "Compliance Office has reviewed and marked the MAP ready for evidence verification.",
    ]


def _map_from_gap(gap, index):
    new_requirement = _normalize_space(gap.get("new_requirement") or gap.get("policy_gap") or gap.get("gap"))
    deadline = gap.get("deadline") or _deadline_text(new_requirement)
    deadline_days = _deadline_days(deadline)
    department = gap.get("affected_department") or _department_for_text(new_requirement)
    evidence_required = gap.get("evidence_required") or _evidence_for_text(new_requirement)
    action = _action_template(new_requirement, gap.get("change_type"))
    priority_score, priority_label = _priority(deadline_days, new_requirement, gap.get("severity"))

    return {
        "id": f"MAP-{index:03d}",
        "action": action,
        "owner": _owner_for_department(department),
        "department": department,
        "deadline": deadline,
        "deadline_days": deadline_days,
        "priority_score": priority_score,
        "priority_label": priority_label,
        "evidence_required": evidence_required,
        "status": "Pending Review",
        "reason": gap.get("basis") or f"Generated from gap {gap.get('id', 'unlinked')}.",
        "linked_gap_id": gap.get("id"),
        "source_obligation": new_requirement,
        "acceptance_criteria": _acceptance_criteria(action, evidence_required, deadline),
    }


def _map_from_obligation(obligation, index, scout_result):
    deadline = _deadline_text(obligation, scout_result.get("deadline"))
    deadline_days = _deadline_days(deadline)
    department = _department_for_text(obligation)
    evidence_required = _evidence_for_text(obligation)
    action = _action_template(obligation)
    priority_score, priority_label = _priority(deadline_days, obligation)

    return {
        "id": f"MAP-{index:03d}",
        "action": action,
        "owner": _owner_for_department(department),
        "department": department,
        "deadline": deadline,
        "deadline_days": deadline_days,
        "priority_score": priority_score,
        "priority_label": priority_label,
        "evidence_required": evidence_required,
        "status": "Pending Review",
        "reason": "Generated from Scout obligation extraction.",
        "linked_gap_id": None,
        "source_obligation": obligation,
        "acceptance_criteria": _acceptance_criteria(action, evidence_required, deadline),
    }


def extract_action_points(content=None, scout_result=None, delta_result=None):
    """
    Generate bank-realistic Measurable Action Points from Scout and Delta output.
    Keeps the original function name for workflow compatibility.
    """
    text = _normalize_space(content)
    scout = scout_result or parse_circular_text(text)
    delta = delta_result or {}
    obligations = scout.get("obligations") or []
    gaps = delta.get("policy_gaps") or []
    engine_notes = ["MAP Generator used deterministic offline department/evidence mapping."]

    action_points = []
    for gap in gaps:
        if len(action_points) >= 7:
            break
        if isinstance(gap, dict):
            action_points.append(_map_from_gap(gap, len(action_points) + 1))

    for obligation in obligations:
        if len(action_points) >= 7:
            break
        action_points.append(_map_from_obligation(obligation, len(action_points) + 1, scout))

    action_points = _dedupe_action_points(action_points)

    if len(action_points) > 7:
        action_points = action_points[:7]

    if not action_points and text:
        fallback_gap = {
            "id": "GAP-001",
            "new_requirement": text[:180],
            "basis": "Fallback MAP generated because no structured obligation was extracted.",
            "affected_department": "Compliance Office",
            "evidence_required": "Manual compliance review note and owner sign-off",
            "severity": "Medium",
        }
        action_points = [_map_from_gap(fallback_gap, 1)]
        engine_notes.append("Fallback MAP generated for weak circular text.")

    if not action_points:
        engine_notes.append("No MAP generated because circular text was empty.")

    for index, action_point in enumerate(action_points, start=1):
        action_point["id"] = f"MAP-{index:03d}"

    return {
        "action_points": action_points,
        "engine_notes": engine_notes,
    }
