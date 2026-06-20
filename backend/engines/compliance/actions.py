import re

from .advisory_mapping import match_department_advisory
from .scout import parse_circular_text


DEPARTMENT_RULES = (
    ("IT Vertical", ("central inventory", "inventory shall include", "outsourced it services", "it outsourcing", "application maintenance", "data centre", "network services", "technology owner", "cloud governance")),
    ("Procurement & Vendor Management", ("service provider", "vendor", "third-party", "due diligence", "subcontractor", "cloud provider", "concentration risk")),
    ("Legal Department", ("outsourcing agreement", "legally binding", "contract", "audit rights", "rbi inspection", "termination rights", "exit strategy")),
    ("Risk Management", ("risk assessment", "risk management", "technology risk", "operational risk", "business continuity", "disaster recovery", "resilience")),
    ("Cybersecurity Wing", ("security operations centre", "security operations center", "outsourced soc", "soc", "alert rules", "metadata", "incident response integration")),
    ("Compliance Department", ("board-approved it outsourcing policy", "outsourcing policy", "regulatory reporting", "closure report", "senior management")),
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
    ("Board-approved outsourcing policy and management approval/sign-off", ("board-approved it outsourcing policy", "outsourcing policy", "senior management")),
    ("BCP/DR test report with gaps, corrective actions, recovery objectives, and management approval", ("business continuity", "disaster recovery", "bcp", "drp", "resilience")),
    ("Outsourcing inventory export with provider, owner, criticality, data, contract expiry, and exit dependency fields", ("central inventory", "inventory shall include", "inventory of outsourced it", "outsourced it services")),
    ("Signed outsourcing agreement clause checklist with audit rights, RBI inspection access, termination rights, and exit strategy evidence", ("outsourcing agreement", "legally binding", "audit rights", "rbi inspection", "termination rights", "exit strategy")),
    ("Cloud governance checklist covering access control, logging, monitoring, DR, data portability, and secure deletion", ("cloud", "data portability", "secure deletion", "cloud governance")),
    ("SOC escalation workflow evidence, alert rule review, logs, metadata, and incident response integration proof", ("security operations centre", "security operations center", "soc", "alert rules", "metadata", "incident response integration")),
    ("SLA monitoring report, service review minutes, and closure evidence", ("service standards", "sla monitoring", "sla", "service level")),
    ("Exit strategy and transition plan with management approval/sign-off", ("exit strategy", "termination rights", "transition plan")),
    ("Audit report, risk review, contract review, closure evidence, and management sign-off", ("audit report", "periodic audits", "audit review", "contract reviews", "closure of observations", "management approvals")),
    ("Service provider due diligence checklist, risk assessment approval, concentration risk note, and subcontractor review", ("due diligence", "service provider", "third-party", "subcontractor")),
    ("Fraud incident register, reporting timestamp, customer impact note, and evidence reference", ("fraud", "digital fraud", "payment fraud", "mule")),
    ("Customer notification proof, delivery timestamp, and exception approval log", ("notify", "customer notification", "affected customer", "grievance", "complaint")),
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


def _prioritize_action_points(action_points):
    required_verticals = (
        "IT Vertical",
        "Procurement & Vendor Management",
        "Legal Department",
        "Risk Management",
        "Cybersecurity Wing",
        "Internal Audit",
        "Compliance Department",
    )
    selected = []
    selected_ids = set()

    for vertical in required_verticals:
        for action_point in action_points:
            if id(action_point) in selected_ids:
                continue
            if action_point.get("business_vertical") == vertical:
                selected.append(action_point)
                selected_ids.add(id(action_point))
                break

    for action_point in action_points:
        if id(action_point) not in selected_ids:
            selected.append(action_point)
            selected_ids.add(id(action_point))

    return selected


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


def _fallback_advisory(department, text):
    lower = (text or "").lower()
    if "customer notification" in lower or "affected customer" in lower or "notify" in lower:
        business_vertical = "Customer Support / Grievance Cell"
        sub_vertical = "Customer Notification"
        reference = "Internal customer protection and grievance workflow"
    elif "branch" in lower:
        business_vertical = "Branch Operations"
        sub_vertical = "Branch Compliance"
        reference = "Internal branch escalation and compliance workflow"
    else:
        business_vertical = department or "Compliance Department"
        sub_vertical = "Regulatory Compliance"
        reference = "Internal compliance assignment fallback"

    return {
        "business_vertical": business_vertical,
        "sub_vertical": sub_vertical,
        "primary_regulator": "RBI",
        "regulatory_reference": reference,
        "official_link": "",
        "match_score": 0,
        "assignment_basis": "No strong bank advisory row matched; deterministic fallback used from department rules.",
    }


def _fixed_it_advisory_for_text(text):
    lower = (text or "").lower()
    row = None

    if any(term in lower for term in ("business continuity", "disaster recovery", "bcp", "drp", "resilience")) and "due diligence" not in lower:
        row = {
            "business_vertical": "Risk Management",
            "sub_vertical": "Operational Risk",
            "scope": "BCP/DR testing and resilience oversight",
        }
    elif any(term in lower for term in ("audit reports", "periodic audits", "audit review", "sla monitoring", "closure of observations")):
        row = {
            "business_vertical": "Internal Audit",
            "sub_vertical": "Information Systems Audit",
            "scope": "Audit reports, SLA monitoring, and closure review",
        }
    elif any(term in lower for term in ("security operations centre", "security operations center", "outsourced soc", "soc", "alert rules", "incident response integration", "cyber incidents")):
        row = {
            "business_vertical": "Cybersecurity Wing",
            "sub_vertical": "Security Operations Center (SOC)",
            "scope": "SOC oversight and third-party cyber incident escalation",
        }
    elif any(term in lower for term in ("due diligence", "service provider", "third-party", "subcontractor")):
        row = {
            "business_vertical": "Procurement & Vendor Management",
            "sub_vertical": "Third-Party Risk Management",
            "scope": "Service provider due diligence and third-party risk review",
        }
    elif any(term in lower for term in ("outsourcing agreement", "audit rights", "rbi inspection", "termination rights", "exit strategy")):
        row = {
            "business_vertical": "Legal Department",
            "sub_vertical": "Contract Management",
            "scope": "Outsourcing agreement clauses and exit controls",
        }
    elif any(term in lower for term in ("cloud", "data portability", "secure deletion", "cloud governance")):
        row = {
            "business_vertical": "IT Vertical",
            "sub_vertical": "Cloud Operations",
            "scope": "Cloud governance and secure exit controls",
        }
    elif any(term in lower for term in ("central inventory", "inventory shall include", "outsourced it services")):
        row = {
            "business_vertical": "IT Vertical",
            "sub_vertical": "Infrastructure Management",
            "scope": "Central inventory of outsourced IT services",
        }
    elif any(term in lower for term in ("outsourcing policy", "board-approved", "senior management")):
        row = {
            "business_vertical": "Compliance Department",
            "sub_vertical": "Regulatory Compliance",
            "scope": "IT outsourcing governance and policy ownership",
        }

    if not row:
        return None

    return {
        **row,
        "primary_regulator": "RBI",
        "regulatory_reference": "Master Direction on Outsourcing of Information Technology Services",
        "official_link": "",
        "match_score": 100,
        "assignment_basis": "Deterministic IT outsourcing obligation mapping.",
    }


def _advisory_from_gap_or_match(gap, text, scout_result, department):
    if gap and gap.get("business_vertical") and gap.get("sub_vertical"):
        return {
            "business_vertical": gap.get("business_vertical"),
            "sub_vertical": gap.get("sub_vertical"),
            "primary_regulator": gap.get("primary_regulator", "RBI"),
            "regulatory_reference": gap.get("regulatory_reference", "Mapped regulatory advisory"),
            "official_link": gap.get("official_link", ""),
            "match_score": gap.get("match_score", 0),
            "assignment_basis": gap.get("assignment_basis", "Mapped from Delta policy gap advisory assignment."),
        }

    fixed_advisory = _fixed_it_advisory_for_text(text)
    if fixed_advisory:
        return fixed_advisory

    matches = match_department_advisory(
        text,
        obligations=[text],
        risk_keywords=scout_result.get("risk_keywords", []) if scout_result else [],
        category=scout_result.get("category") if scout_result else None,
        limit=1,
    )
    if matches and matches[0].get("match_score", 0) > 1:
        return matches[0]

    return _fallback_advisory(department, text)


def _department_from_advisory(advisory, fallback_department):
    if advisory and advisory.get("match_score", 0) > 1:
        return f"{advisory['business_vertical']} / {advisory['sub_vertical']}"
    return fallback_department or "Compliance Office"


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

    if any(term in lower for term in ("fraud", "cyber", "mule", "customer", "kyc", "aml", "outsourcing", "cloud", "service provider", "soc")):
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
    if "central inventory" in lower or "inventory shall include" in lower or "inventory of outsourced" in lower:
        return "Create and maintain the central outsourced IT services inventory with owner, provider, criticality, data, contract, and exit fields."
    if "board-approved it outsourcing policy" in lower or "outsourcing policy" in lower:
        return "Update the Board-approved IT outsourcing policy and responsibility matrix for all accountable functions."
    if "outsourcing agreement" in lower or "audit rights" in lower or "rbi inspection" in lower:
        return "Update the outsourcing agreement clause checklist for audit rights, RBI inspection access, incident reporting, termination rights, and exit strategy."
    if "cloud" in lower or "data portability" in lower or "secure deletion" in lower:
        return "Implement the cloud governance checklist for access control, logging, monitoring, DR, data portability, and secure deletion."
    if "security operations centre" in lower or "security operations center" in lower or "soc" in lower or "alert rules" in lower:
        return "Document outsourced SOC oversight with alert rule review, log coverage, escalation workflow, and incident response integration."
    if "cyber incidents" in lower and ("third-party" in lower or "service provider" in lower or "escalat" in lower):
        return "Define third-party cyber incident escalation workflow and integrate it with incident response reporting timelines."
    if "due diligence" in lower or "service provider" in lower or "third-party" in lower:
        return "Complete service provider due diligence and technology risk approval before entering or renewing the outsourcing arrangement."
    if "business continuity" in lower or "disaster recovery" in lower or "bcp" in lower or "drp" in lower:
        return "Run and document BCP/DR testing for material outsourced IT services with corrective action tracking."
    if "exit strategy" in lower or "transition plan" in lower:
        return "Prepare the exit strategy and transition plan for material outsourced IT services."
    if "periodic audits" in lower or "audit reports" in lower or "audit review" in lower or "sla monitoring" in lower:
        return "Collect service provider audit reports, SLA monitoring results, risk reviews, and closure evidence."
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


def _map_from_gap(gap, index, scout_result=None):
    new_requirement = _normalize_space(gap.get("new_requirement") or gap.get("policy_gap") or gap.get("gap"))
    deadline = gap.get("deadline") or _deadline_text(new_requirement)
    deadline_days = _deadline_days(deadline)
    fallback_department = gap.get("affected_department") or _department_for_text(new_requirement)
    advisory = _advisory_from_gap_or_match(gap, new_requirement, scout_result, fallback_department)
    department = _department_from_advisory(advisory, fallback_department)
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
        "business_vertical": advisory["business_vertical"],
        "sub_vertical": advisory["sub_vertical"],
        "primary_regulator": advisory["primary_regulator"],
        "regulatory_reference": advisory["regulatory_reference"],
        "official_link": advisory["official_link"],
        "assignment_basis": advisory["assignment_basis"],
    }


def _map_from_obligation(obligation, index, scout_result):
    deadline = _deadline_text(obligation, scout_result.get("deadline"))
    deadline_days = _deadline_days(deadline)
    fallback_department = _department_for_text(obligation)
    advisory = _advisory_from_gap_or_match(None, obligation, scout_result, fallback_department)
    department = _department_from_advisory(advisory, fallback_department)
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
        "business_vertical": advisory["business_vertical"],
        "sub_vertical": advisory["sub_vertical"],
        "primary_regulator": advisory["primary_regulator"],
        "regulatory_reference": advisory["regulatory_reference"],
        "official_link": advisory["official_link"],
        "assignment_basis": advisory["assignment_basis"],
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
        if len(action_points) >= 24:
            break
        if isinstance(gap, dict):
            action_points.append(_map_from_gap(gap, len(action_points) + 1, scout))

    for obligation in obligations:
        if len(action_points) >= 24:
            break
        action_points.append(_map_from_obligation(obligation, len(action_points) + 1, scout))

    action_points = _prioritize_action_points(_dedupe_action_points(action_points))

    if len(action_points) > 24:
        action_points = action_points[:24]

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
