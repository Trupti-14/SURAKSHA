import re

from .advisory_mapping import match_department_advisory
from .scout import parse_circular_text


DIGITAL_FRAUD_EVIDENCE = (
    "Fraud reporting SOP",
    "Branch escalation register",
    "Customer notification proof",
    "Transaction logs",
    "Fraud monitoring report",
    "Audit trail export",
    "CERT-In escalation record",
    "Owner sign-off",
    "Closure timestamp",
)

IT_OUTSOURCING_EVIDENCE = (
    "Outsourcing policy",
    "Service provider due diligence checklist",
    "Outsourcing agreement clause checklist",
    "Cloud governance checklist",
    "SOC escalation workflow evidence",
    "BCP/DR test report",
    "Audit report",
    "Exit strategy",
    "Management approval",
)

PSO_EVIDENCE = (
    "RBI prior approval application",
    "DPSS acknowledgement",
    "Board approval",
    "Proposed director details",
    "Shareholder details",
    "Public notice proof",
    "Stakeholder communication proof",
    "Form A submission",
    "Certificate of Authorisation",
    "CoA surrender proof",
    "Legal review note",
    "Compliance sign-off",
    "Closure record",
)

ACCOUNT_AGGREGATOR_EVIDENCE = (
    "Updated Account Aggregator policy",
    "CCIL FIP inclusion record",
    "Application/configuration update proof",
    "Compliance sign-off",
    "Stakeholder communication proof",
    "Implementation closure record",
)

PSO_CONTEXT_TERMS = (
    "non-bank pso",
    "payment system operator",
    "pso",
    "prior approval",
    "dpss",
    "takeover",
    "acquisition of control",
    "sale/transfer of payment activity",
    "payment activity transfer",
    "form a",
    "certificate of authorisation",
    "certificate of authorization",
    "payment and settlement systems act",
    "payment aggregator",
    "payment gateway",
    "ppi",
)

ACCOUNT_AGGREGATOR_CONTEXT_TERMS = (
    "account aggregator",
    "financial information provider",
    "fip",
    "clearing corporation of india limited",
    "ccil",
    "retail direct gilt",
    "government securities",
    "g-sec",
)

DEPARTMENT_RULES = (
    ("Regulatory Compliance Department", ("account aggregator", "financial information provider", "fip", "ccil")),
    ("Digital Banking / Account Aggregator Operations", ("account aggregator", "data sharing", "consent artefact", "consent artifact", "fip")),
    ("Treasury / Government Securities Operations", ("government securities", "retail direct gilt", "g-sec", "gilt accounts", "ccil")),
    ("IT/Application Owner for Account Aggregator integration", ("application", "configuration", "integration", "systems", "data sharing")),
    ("Payments Vertical / Payment Systems Compliance", ("non-bank pso", "payment system operator", "payment activity", "payment aggregator", "payment gateway", "ppi", "dpss", "form a")),
    ("Regulatory Compliance Department", ("prior approval of rbi", "rbi approval", "inform rbi", "dpss", "payment and settlement systems act")),
    ("Legal & Secretarial", ("takeover", "acquisition of control", "sale/transfer", "transferor", "transferee", "legal", "public notice")),
    ("Board Governance / Company Secretary", ("change in management", "directors", "director", "board approval", "shareholder")),
    ("Risk & Compliance", ("regulatory/supervisory action", "supervisory action", "risk", "compliance sign-off")),
    ("Operations / Merchant Acquiring", ("merchants", "agents", "bankers", "customers", "stakeholders", "merchant acquiring")),
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
    ("Updated Account Aggregator policy, CCIL FIP inclusion record, Application/configuration update proof, Compliance sign-off, Stakeholder communication proof, and Implementation closure record", ("account aggregator", "financial information provider", "fip", "ccil", "retail direct gilt", "government securities")),
    ("RBI prior approval application, DPSS acknowledgement, Board approval, Legal review note, and Compliance sign-off", ("prior approval of rbi", "rbi approval", "takeover", "acquisition of control")),
    ("Sale/transfer approval checklist, Board approval, Legal review note, Compliance sign-off, and Closure record", ("sale/transfer of payment activity", "payment activity transfer", "transferor", "transferee")),
    ("DPSS application pack, proposed director details, shareholder details, and Closure record", ("dpss", "director", "shareholder")),
    ("Public notice proof and stakeholder communication proof", ("public notice", "stakeholders", "agents", "bankers", "customers", "merchants")),
    ("Form A submission, Certificate of Authorisation, CoA surrender proof, and DPSS acknowledgement", ("form a", "certificate of authorisation", "certificate of authorization", "surrender")),
    ("Outsourcing policy and management approval", ("board-approved it outsourcing policy", "outsourcing policy", "senior management")),
    ("BCP/DR test report and management approval", ("business continuity", "disaster recovery", "bcp", "drp", "resilience")),
    ("Outsourcing policy, audit report, and management approval", ("central inventory", "inventory shall include", "inventory of outsourced it", "outsourced it services")),
    ("Outsourcing agreement clause checklist, exit strategy, and management approval", ("outsourcing agreement", "legally binding", "audit rights", "rbi inspection", "termination rights", "exit strategy")),
    ("Cloud governance checklist and audit report", ("cloud", "data portability", "secure deletion", "cloud governance")),
    ("SOC escalation workflow evidence and audit report", ("security operations centre", "security operations center", "soc", "alert rules", "metadata", "incident response integration")),
    ("SLA monitoring report, service review minutes, and closure evidence", ("service standards", "sla monitoring", "sla", "service level")),
    ("Exit strategy and transition plan with management approval/sign-off", ("exit strategy", "termination rights", "transition plan")),
    ("Audit report, risk review, contract review, closure evidence, and management sign-off", ("audit report", "periodic audits", "audit review", "contract reviews", "closure of observations", "management approvals")),
    ("Service provider due diligence checklist, risk assessment approval, concentration risk note, and subcontractor review", ("due diligence", "service provider", "third-party", "subcontractor")),
    ("Fraud reporting SOP, transaction logs, fraud monitoring report, owner sign-off, and closure timestamp", ("fraud", "digital fraud", "payment fraud", "mule")),
    ("Customer notification proof, delivery timestamp, and exception approval log", ("notify", "customer notification", "affected customer", "grievance", "complaint")),
    ("Transaction logs, audit trail export, owner sign-off, and closure timestamp", ("retain", "preserve", "evidence", "audit trail", "archive")),
    ("Monthly report sample, maker-checker approval, and Compliance Office submission proof", ("monthly", "report", "submit")),
    ("Branch escalation register, owner sign-off, and closure timestamp", ("branch", "escalate", "branch-level")),
    ("Security log export, incident ticket, digital evidence hash, and containment note", ("cyber", "security", "digital evidence", "incident")),
    ("KYC/AML review tracker, suspicious account review note, and exception approval sample", ("kyc", "aml", "verification", "suspicious account")),
    ("DPDP/privacy assessment note and customer data handling approval", ("dpdp", "privacy", "personal data")),
)


def _normalize_space(value):
    return re.sub(r"\s+", " ", value or "").strip()


def _scout_context(scout_result):
    if not scout_result:
        return ""
    parts = [
        scout_result.get("category") or "",
        " ".join(scout_result.get("risk_keywords") or []),
        " ".join(scout_result.get("obligations") or []),
    ]
    return " ".join(parts).lower()


def _is_digital_fraud_context(text, scout_result=None):
    context = f"{text or ''} {_scout_context(scout_result)}".lower()
    return any(
        term in context
        for term in (
            "digital fraud",
            "payment fraud",
            "cyber-enabled fraud",
            "fraud reporting",
            "fraud monitoring",
            "mule account",
        )
    )


def _is_pso_payment_context(text, scout_result=None):
    context = f"{text or ''} {_scout_context(scout_result)}".lower()
    return any(term in context for term in PSO_CONTEXT_TERMS)


def _is_account_aggregator_context(text, scout_result=None):
    context = f"{text or ''} {_scout_context(scout_result)}".lower()
    return any(term in context for term in ACCOUNT_AGGREGATOR_CONTEXT_TERMS)


def _is_it_outsourcing_context(text, scout_result=None):
    context = f"{text or ''} {_scout_context(scout_result)}".lower()
    return any(
        term in context
        for term in (
            "it outsourcing",
            "outsourced it",
            "outsourcing arrangement",
            "outsourcing agreement",
            "service provider due diligence",
            "cloud governance",
            "outsourced soc",
            "security operations centre",
            "security operations center",
            "bcp/dr",
            "disaster recovery",
            "business continuity",
            "third-party risk",
            "central inventory",
            "inventory of outsourced",
            "board-approved it outsourcing policy",
            "outsourcing policy",
        )
    )


def _join_evidence(items):
    return ", ".join(dict.fromkeys(item for item in items if item))


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
        "Payments Vertical",
        "Payments Vertical / Payment Systems Compliance",
        "Regulatory Compliance Department",
        "Digital Banking / Account Aggregator Operations",
        "Treasury / Government Securities Operations",
        "IT/Application Owner for Account Aggregator integration",
        "Legal & Secretarial",
        "Board Governance / Company Secretary",
        "Operations / Merchant Acquiring",
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
    if _is_account_aggregator_context(lower):
        matched = ["Regulatory Compliance Department", "Digital Banking / Account Aggregator Operations"]
        if any(term in lower for term in ("government securities", "retail direct gilt", "g-sec", "ccil")):
            matched.append("Treasury / Government Securities Operations")
        if any(term in lower for term in ("policy", "framework", "reference", "included", "inclusion")):
            matched.append("Legal & Secretarial")
        if any(term in lower for term in ("systems", "application", "configuration", "integration", "data sharing")):
            matched.append("IT/Application Owner for Account Aggregator integration")
        return " + ".join(dict.fromkeys(matched).keys())

    if _is_pso_payment_context(lower):
        matched = ["Payments Vertical / Payment Systems Compliance"]
        if any(term in lower for term in ("prior approval", "rbi", "dpss", "form a", "certificate of authorisation", "certificate of authorization")):
            matched.append("Regulatory Compliance Department")
        if any(term in lower for term in ("takeover", "acquisition of control", "sale/transfer", "transferor", "transferee", "public notice")):
            matched.append("Legal & Secretarial")
        if any(term in lower for term in ("management", "director", "shareholder", "board")):
            matched.append("Board Governance / Company Secretary")
        if any(term in lower for term in ("stakeholders", "agents", "bankers", "customers", "merchants")):
            matched.append("Operations / Merchant Acquiring")
        if any(term in lower for term in ("regulatory/supervisory action", "supervisory action", "risk")):
            matched.append("Risk & Compliance")
        if any(term in lower for term in ("audit", "evidence review")):
            matched.append("Internal Audit")
        return " + ".join(dict.fromkeys(matched).keys())

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


def _fixed_payment_advisory_for_text(text):
    lower = (text or "").lower()
    if not _is_pso_payment_context(lower):
        return None

    if any(term in lower for term in ("management", "director", "shareholder", "board")):
        row = {
            "business_vertical": "Board Governance / Company Secretary",
            "sub_vertical": "Corporate Governance",
            "scope": "Management/director/shareholder change intimation",
        }
    elif any(term in lower for term in ("public notice", "stakeholders", "agents", "bankers", "customers", "merchants")):
        row = {
            "business_vertical": "Operations / Merchant Acquiring",
            "sub_vertical": "Stakeholder Communications",
            "scope": "Public notice and stakeholder intimation",
        }
    elif any(term in lower for term in ("takeover", "acquisition of control", "sale/transfer", "transferor", "transferee")):
        row = {
            "business_vertical": "Legal & Secretarial",
            "sub_vertical": "Regulatory Transactions",
            "scope": "PSO control or payment activity transfer approval",
        }
    elif any(term in lower for term in ("form a", "certificate of authorisation", "certificate of authorization", "dpss", "rbi")):
        row = {
            "business_vertical": "Regulatory Compliance Department",
            "sub_vertical": "Payment Systems Compliance",
            "scope": "DPSS application and authorisation documentation",
        }
    else:
        row = {
            "business_vertical": "Payments Vertical",
            "sub_vertical": "Payment Systems Compliance",
            "scope": "Digital payment regulatory approval workflow",
        }

    return {
        **row,
        "primary_regulator": "RBI",
        "regulatory_reference": "Payment System Operator prior approval and payment activity transfer requirements",
        "official_link": "",
        "match_score": 100,
        "assignment_basis": "Deterministic digital_payment / PSO domain mapping.",
    }


def _fixed_account_aggregator_advisory_for_text(text):
    lower = (text or "").lower()
    if not _is_account_aggregator_context(lower):
        return None

    if any(term in lower for term in ("retail direct gilt", "government securities", "g-sec")):
        row = {
            "business_vertical": "Treasury / Government Securities Operations",
            "sub_vertical": "Retail Direct Gilt Operations",
            "scope": "Government Securities data sharing under Account Aggregator",
        }
    elif any(term in lower for term in ("systems", "application", "configuration", "integration", "data sharing")):
        row = {
            "business_vertical": "IT/Application Owner for Account Aggregator integration",
            "sub_vertical": "Account Aggregator Platform Integration",
            "scope": "FIP configuration and data sharing workflow update",
        }
    elif any(term in lower for term in ("policy", "framework", "reference", "included", "inclusion")):
        row = {
            "business_vertical": "Regulatory Compliance Department",
            "sub_vertical": "Account Aggregator Compliance",
            "scope": "Policy/reference register update for CCIL FIP inclusion",
        }
    else:
        row = {
            "business_vertical": "Digital Banking / Account Aggregator Operations",
            "sub_vertical": "Account Aggregator Operations",
            "scope": "Operational readiness for CCIL as Financial Information Provider",
        }

    return {
        **row,
        "primary_regulator": "RBI",
        "regulatory_reference": "Account Aggregator Framework - Financial Information Provider inclusion",
        "official_link": "",
        "match_score": 100,
        "assignment_basis": "Deterministic account_aggregator / FIP / CCIL domain mapping.",
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

    fixed_advisory = (
        _fixed_account_aggregator_advisory_for_text(text)
        or _fixed_payment_advisory_for_text(text)
        or _fixed_it_advisory_for_text(text)
    )
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


def _digital_fraud_evidence_for_text(text):
    lower = (text or "").lower()
    evidence = []

    if any(term in lower for term in ("cert-in", "cyber", "security incident")):
        evidence.extend(("CERT-In escalation record", "Audit trail export", "Closure timestamp"))
    if any(term in lower for term in ("branch", "branch-level")):
        evidence.extend(("Branch escalation register", "Owner sign-off", "Closure timestamp"))
    if "escalat" in lower and not evidence:
        evidence.extend(("Branch escalation register", "Owner sign-off", "Closure timestamp"))
    if any(term in lower for term in ("notify", "customer", "grievance")):
        evidence.extend(("Customer notification proof", "Transaction logs", "Closure timestamp"))
    if any(term in lower for term in ("retain", "preserve", "evidence", "audit trail", "log")):
        evidence.extend(("Transaction logs", "Audit trail export", "Owner sign-off"))
    if any(term in lower for term in ("monitor", "monthly", "submit")) or re.search(r"\breport(?:ing|s|ed)?\b", lower):
        evidence.extend(("Fraud reporting SOP", "Fraud monitoring report", "Owner sign-off"))
    if any(term in lower for term in ("fraud", "mule", "payment fraud", "digital fraud")):
        evidence.extend(("Fraud reporting SOP", "Transaction logs", "Fraud monitoring report"))

    return _join_evidence(evidence or DIGITAL_FRAUD_EVIDENCE)


def _it_outsourcing_evidence_for_text(text):
    lower = (text or "").lower()
    evidence = []

    if any(term in lower for term in ("outsourcing policy", "board-approved", "senior management", "central inventory", "inventory")):
        evidence.extend(("Outsourcing policy", "Management approval"))
    if any(term in lower for term in ("due diligence", "service provider", "third-party", "subcontractor", "concentration risk")):
        evidence.extend(("Service provider due diligence checklist", "Management approval"))
    if any(term in lower for term in ("outsourcing agreement", "contract", "audit rights", "rbi inspection", "termination rights")):
        evidence.extend(("Outsourcing agreement clause checklist", "Management approval"))
    if any(term in lower for term in ("cloud", "data portability", "secure deletion", "cloud governance")):
        evidence.extend(("Cloud governance checklist", "Audit report"))
    if any(term in lower for term in ("soc", "security operations centre", "security operations center", "alert rules", "incident response integration")):
        evidence.extend(("SOC escalation workflow evidence", "Audit report"))
    if any(term in lower for term in ("business continuity", "disaster recovery", "bcp", "drp", "resilience")):
        evidence.extend(("BCP/DR test report", "Management approval"))
    if any(term in lower for term in ("audit reports", "periodic audits", "audit review", "sla monitoring", "closure of observations")):
        evidence.extend(("Audit report", "Management approval"))
    if any(term in lower for term in ("exit strategy", "transition plan")):
        evidence.extend(("Exit strategy", "Outsourcing agreement clause checklist", "Management approval"))

    return _join_evidence(evidence or IT_OUTSOURCING_EVIDENCE)


def _pso_evidence_for_text(text):
    lower = (text or "").lower()
    evidence = []
    if any(term in lower for term in ("prior approval", "rbi approval", "takeover", "acquisition of control")):
        evidence.extend(("RBI prior approval application", "DPSS acknowledgement", "Board approval", "Legal review note", "Compliance sign-off"))
    if any(term in lower for term in ("sale/transfer", "payment activity transfer", "transferor", "transferee")):
        evidence.extend(("Board approval", "Legal review note", "Compliance sign-off", "Closure record"))
    if any(term in lower for term in ("management", "director", "shareholder")):
        evidence.extend(("Proposed director details", "Shareholder details", "DPSS acknowledgement"))
    if any(term in lower for term in ("public notice", "stakeholder", "agents", "bankers", "customers", "merchants")):
        evidence.extend(("Public notice proof", "Stakeholder communication proof", "Closure record"))
    if any(term in lower for term in ("form a", "certificate of authorisation", "certificate of authorization", "surrender")):
        evidence.extend(("Form A submission", "Certificate of Authorisation", "CoA surrender proof", "DPSS acknowledgement"))
    if any(term in lower for term in ("regulatory/supervisory action", "supervisory action")):
        evidence.extend(("Legal review note", "Compliance sign-off", "Closure record"))
    return _join_evidence(evidence or PSO_EVIDENCE)


def _account_aggregator_evidence_for_text(text):
    lower = (text or "").lower()
    evidence = ["Updated Account Aggregator policy", "Compliance sign-off", "Implementation closure record"]
    if any(term in lower for term in ("ccil", "clearing corporation of india limited", "financial information provider", "fip")):
        evidence.append("CCIL FIP inclusion record")
    if any(term in lower for term in ("systems", "application", "configuration", "integration", "data sharing")):
        evidence.append("Application/configuration update proof")
    if any(term in lower for term in ("operations", "stakeholder", "notify", "owner")):
        evidence.append("Stakeholder communication proof")
    if any(term in lower for term in ("retail direct gilt", "government securities", "g-sec")):
        evidence.append("Retail Direct Gilt / Government Securities workflow update proof")
    return _join_evidence(evidence or ACCOUNT_AGGREGATOR_EVIDENCE)


def _strict_evidence_for_context(text, scout_result=None):
    if _is_account_aggregator_context(text, scout_result):
        return _account_aggregator_evidence_for_text(text)
    if _is_pso_payment_context(text, scout_result):
        return _pso_evidence_for_text(text)
    if _is_digital_fraud_context(text, scout_result):
        return _digital_fraud_evidence_for_text(text)
    if _is_it_outsourcing_context(text, scout_result):
        return _it_outsourcing_evidence_for_text(text)
    return None


def _evidence_for_text(text, fallback=None, scout_result=None):
    strict_evidence = _strict_evidence_for_context(text, scout_result)
    if strict_evidence:
        return strict_evidence

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

    if _is_pso_payment_context(lower):
        if any(term in lower for term in ("prior approval", "rbi approval", "dpss", "takeover", "acquisition of control", "form a", "certificate of authorisation", "certificate of authorization")):
            score = max(score, 7)
        elif any(term in lower for term in ("public notice", "stakeholder", "agents", "bankers", "customers", "merchants")):
            score = max(score, 6)
        else:
            score = max(score, 5)
        score = min(score, 8)
    elif _is_account_aggregator_context(lower):
        score = max(score, 6)
        if any(term in lower for term in ("application", "configuration", "systems", "data sharing", "retail direct gilt", "government securities")):
            score = max(score, 7)
    elif any(term in lower for term in ("fraud", "cyber", "mule", "customer", "kyc", "aml", "outsourcing", "cloud", "service provider", "soc")):
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


def _action_template(text, change_type=None, scout_result=None):
    lower = (text or "").lower()
    if _is_account_aggregator_context(text, scout_result):
        if any(term in lower for term in ("compliance sign-off", "implementation evidence", "closure record", "maintained")):
            return "Maintain compliance sign-off and implementation evidence for CCIL FIP inclusion."
        if any(term in lower for term in ("notify", "notified", "operations", "application owners", "owner")):
            return "Notify Account Aggregator operations and application owners about CCIL FIP inclusion."
        if any(term in lower for term in ("retail direct gilt", "government securities", "g-sec")):
            return "Update Retail Direct Gilt / Government Securities data sharing workflow for CCIL as FIP."
        if any(term in lower for term in ("systems", "application", "configuration", "integration", "data sharing")):
            return "Update Account Aggregator application/configuration to reflect CCIL's FIP role."
        if any(term in lower for term in ("policy", "framework", "reference", "included", "inclusion", "ccil", "financial information provider")):
            return "Update Account Aggregator policy/reference register to include CCIL as FIP."
        return "Maintain compliance sign-off and implementation evidence for CCIL FIP inclusion."

    if _is_pso_payment_context(text, scout_result):
        if "within 15 calendar days" in lower and "inform rbi" in lower:
            return "Track 15-calendar-day RBI intimation for management/director or authorised payment activity transfer changes."
        if any(term in lower for term in ("takeover", "acquisition of control")):
            return "Create RBI prior approval workflow for takeover/acquisition of control."
        if "sale/transfer" in lower or "payment activity transfer" in lower:
            return "Create sale/transfer approval checklist for payment activity transfer."
        if any(term in lower for term in ("management", "director", "shareholder", "dpss")):
            return "Maintain DPSS application pack with proposed director and shareholder details."
        if "public notice" in lower:
            return "Publish 15-calendar-day public notice after RBI approval."
        if any(term in lower for term in ("stakeholders", "agents", "bankers", "customers", "merchants")):
            return "Notify stakeholders before payment activity transfer."
        if any(term in lower for term in ("form a", "certificate of authorisation", "certificate of authorization", "surrender")):
            return "Maintain Form A, Certificate of Authorisation, and surrender documentation where applicable."
        if "regulatory/supervisory action" in lower or "supervisory action" in lower:
            return "Maintain board approval, legal review, compliance sign-off, and closure evidence for supervisory liability."
        return "Create RBI approval and DPSS compliance workflow for PSO control or payment activity changes."

    if _is_digital_fraud_context(text, scout_result):
        if any(term in lower for term in ("cert-in", "cyber", "security incident")):
            return "Configure CERT-In escalation path with audit trail export and closure timestamp."
        if any(term in lower for term in ("branch", "branch-level")):
            return "Maintain branch escalation register with owner sign-off and closure timestamp."
        if "escalat" in lower:
            return "Configure escalation path with owner sign-off and closure timestamp."
        if any(term in lower for term in ("notify", "customer", "grievance")):
            return "Create customer notification workflow with proof capture and closure timestamp."
        if any(term in lower for term in ("retain", "preserve", "evidence", "audit trail", "log")):
            return "Maintain transaction logs and audit trail export for digital fraud evidence."
        if any(term in lower for term in ("monitor", "monthly", "report", "submit")):
            return "Submit fraud monitoring report with owner sign-off."
        return "Update fraud reporting SOP with transaction log evidence and owner sign-off."

    if _is_it_outsourcing_context(text, scout_result):
        if any(term in lower for term in ("soc", "security operations centre", "security operations center", "alert rules", "incident response integration")):
            return "Configure SOC escalation workflow evidence and audit report review."
        if any(term in lower for term in ("cloud", "data portability", "secure deletion", "cloud governance")):
            return "Update cloud governance checklist with audit report review."
        if any(term in lower for term in ("business continuity", "disaster recovery", "bcp", "drp", "resilience")):
            return "Submit BCP/DR test report with management approval."
        if any(term in lower for term in ("outsourcing agreement", "contract", "audit rights", "rbi inspection", "termination rights")):
            return "Review outsourcing agreement clauses for audit rights, inspection access, termination, and exit."
        if any(term in lower for term in ("due diligence", "service provider", "third-party", "subcontractor", "concentration risk")):
            return "Update service provider due diligence checklist with management approval."
        if any(term in lower for term in ("audit reports", "periodic audits", "audit review", "sla monitoring", "closure of observations")):
            return "Submit outsourcing audit report with management approval."
        if any(term in lower for term in ("exit strategy", "transition plan")):
            return "Create exit strategy and review related outsourcing agreement clauses."
        return "Update outsourcing policy with owner sign-off and management approval."

    if "central inventory" in lower or "inventory shall include" in lower or "inventory of outsourced" in lower:
        return "Create and maintain the central outsourced IT services inventory with owner, provider, criticality, data, contract, and exit fields."
    if "board-approved it outsourcing policy" in lower or "outsourcing policy" in lower:
        return "Update the Board-approved IT outsourcing policy and responsibility matrix for all accountable functions."
    if "outsourcing agreement" in lower or "audit rights" in lower or "rbi inspection" in lower:
        return "Update the outsourcing agreement clause checklist for audit rights, RBI inspection access, incident reporting, termination rights, and exit strategy."
    if "cloud" in lower or "data portability" in lower or "secure deletion" in lower:
        return "Update the cloud governance checklist for access control, logging, monitoring, DR, data portability, and secure deletion."
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
        return "Maintain evidence retention register with archive inventory and audit trail export."
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
    if any(term in lower for term in ("report", "submit", "monitor")):
        return f"Submit monitoring report for: {_normalize_space(text)[:160]}"
    if any(term in lower for term in ("workflow", "process", "notify")):
        return f"Create workflow for: {_normalize_space(text)[:160]}"
    if any(term in lower for term in ("escalat", "incident")):
        return f"Configure escalation path for: {_normalize_space(text)[:160]}"
    if any(term in lower for term in ("owner", "sign-off", "approval")):
        return f"Define owner sign-off for: {_normalize_space(text)[:160]}"
    if any(term in lower for term in ("agreement", "contract", "clause")):
        return f"Review agreement clauses for: {_normalize_space(text)[:160]}"
    return f"Update SOP for: {_normalize_space(text)[:160]}"


def _acceptance_criteria(action, evidence_required, deadline):
    return [
        f"Approved SOP or workflow update exists for: {action}",
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
    strict_evidence = _strict_evidence_for_context(new_requirement, scout_result)
    evidence_required = strict_evidence or gap.get("evidence_required") or _evidence_for_text(new_requirement, scout_result=scout_result)
    action = _action_template(new_requirement, gap.get("change_type"), scout_result)
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
    evidence_required = _evidence_for_text(obligation, scout_result=scout_result)
    action = _action_template(obligation, scout_result=scout_result)
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


def _account_aggregator_supplemental_obligations(scout_result):
    if not _is_account_aggregator_context("", scout_result):
        return []
    return [
        "Account Aggregator operations and application owners should be notified about CCIL's inclusion as a Financial Information Provider.",
        "Compliance sign-off and implementation evidence should be maintained for CCIL FIP inclusion under the Account Aggregator framework.",
    ]


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

    mapped_obligations = list(obligations)
    for supplemental_obligation in _account_aggregator_supplemental_obligations(scout):
        if supplemental_obligation not in mapped_obligations:
            mapped_obligations.append(supplemental_obligation)

    for obligation in mapped_obligations:
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
