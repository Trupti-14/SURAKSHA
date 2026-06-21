import re

from .advisory_mapping import match_department_advisory
from .scout import parse_circular_text


NO_PRIOR_POLICY = "No matching prior policy found."

METADATA_KEYS = {
    "circular_id",
    "title",
    "category",
    "issue_date",
    "regulator",
    "effective_from",
    "effective_date",
    "status",
    "source_type",
}

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

DOMAIN_TERMS = {
    "it_inventory": ("central inventory", "outsourced it services", "service provider name", "technology owner", "criticality rating", "exit dependency"),
    "it_policy": ("board-approved", "it outsourcing policy", "senior management", "it function", "compliance department"),
    "vendor_due_diligence": ("service provider", "due diligence", "third-party", "subcontractor", "concentration risk", "vendor"),
    "outsourcing_contract": ("outsourcing agreement", "legally binding", "contract", "audit rights", "rbi inspection", "termination rights", "exit strategy"),
    "cloud": ("cloud", "cloud service provider", "data portability", "secure deletion", "cloud governance", "encryption"),
    "soc": ("security operations centre", "security operations center", "outsourced soc", "alert rules", "logs", "metadata", "incident response integration"),
    "bcp_drp": ("business continuity", "disaster recovery", "bcp", "drp", "resilience testing", "recovery objectives"),
    "it_audit": ("audit reports", "audit rights", "sla monitoring", "risk reviews", "closure of observations", "evidence retention"),
    "fraud": ("fraud", "digital fraud", "payment fraud", "mule", "suspicious"),
    "customer": ("customer", "notify", "notification", "grievance", "complaint"),
    "evidence": ("evidence", "retain", "preserve", "archive", "audit trail", "audit"),
    "reporting": ("report", "submit", "submission", "rbi", "monthly", "quarterly"),
    "branch": ("branch", "escalate", "escalation", "branch-level"),
    "kyc": ("kyc", "aml", "verification", "dormant", "suspicious transaction"),
    "cyber": ("cyber", "security", "incident", "log", "digital evidence"),
    "privacy": ("dpdp", "privacy", "personal data", "data protection"),
    "authentication": ("authentication", "otp", "mfa", "2fa", "biometric"),
}

DEPARTMENT_BY_DOMAIN = {
    "it_inventory": "IT Vertical",
    "it_policy": "Compliance Department + Risk Management + IT Vertical",
    "vendor_due_diligence": "Procurement & Vendor Management",
    "outsourcing_contract": "Legal Department + Procurement & Vendor Management",
    "cloud": "IT Vertical + Procurement & Vendor Management",
    "soc": "Cybersecurity Wing",
    "bcp_drp": "IT Vertical + Risk Management",
    "it_audit": "Internal Audit",
    "fraud": "Fraud Risk Department",
    "customer": "Customer Support / Grievance Cell",
    "evidence": "Internal Audit",
    "reporting": "Compliance Office",
    "branch": "Branch Operations",
    "kyc": "KYC / AML Compliance",
    "cyber": "Cybersecurity / IT Security",
    "privacy": "Data Privacy / DPDP Office",
    "authentication": "Cybersecurity / IT Security",
}

EVIDENCE_BY_DOMAIN = {
    "it_inventory": "Outsourcing policy, audit report, and management approval",
    "it_policy": "Outsourcing policy and management approval",
    "vendor_due_diligence": "Service provider due diligence checklist and management approval",
    "outsourcing_contract": "Outsourcing agreement clause checklist, exit strategy, and management approval",
    "cloud": "Cloud governance checklist and audit report",
    "soc": "SOC escalation workflow evidence and audit report",
    "bcp_drp": "BCP/DR test report and management approval",
    "it_audit": "Audit report and management approval",
    "fraud": "Fraud reporting SOP, transaction logs, fraud monitoring report, owner sign-off, and closure timestamp",
    "customer": "Customer notification proof, transaction logs, owner sign-off, and closure timestamp",
    "evidence": "Transaction logs, audit trail export, owner sign-off, and closure timestamp",
    "reporting": "Regulatory report sample, submission acknowledgement, and Compliance Office sign-off",
    "branch": "Branch escalation register, owner sign-off, and closure timestamp",
    "kyc": "KYC/AML verification tracker, exception approval sample, and suspicious account review note",
    "cyber": "Security log export, incident ticket, digital evidence hash, and containment note",
    "privacy": "DPDP assessment note, customer data handling log, and privacy approval evidence",
    "authentication": "Authentication control configuration screenshot and test evidence",
}

RISK_KEYWORDS_BY_DOMAIN = {
    "it_inventory": ["IT outsourcing", "third-party risk"],
    "it_policy": ["IT outsourcing", "third-party risk"],
    "vendor_due_diligence": ["third-party risk", "IT outsourcing"],
    "outsourcing_contract": ["IT outsourcing", "third-party risk"],
    "cloud": ["cloud outsourcing", "IT outsourcing"],
    "soc": ["SOC outsourcing", "cyber incident"],
    "bcp_drp": ["business continuity", "operational risk"],
    "it_audit": ["audit", "IT outsourcing"],
    "fraud": ["digital fraud", "fraud"],
    "customer": ["customer protection"],
    "evidence": ["evidence retention", "audit"],
    "reporting": ["reporting"],
    "branch": ["branch compliance"],
    "kyc": ["KYC", "AML"],
    "cyber": ["cyber incident"],
    "privacy": ["DPDP/data privacy"],
    "authentication": ["cyber incident"],
}


def _normalize_space(value):
    return re.sub(r"\s+", " ", value or "").strip()


def _is_metadata_line(line):
    if ":" not in (line or ""):
        return False
    key = line.split(":", 1)[0].strip().lower()
    return key in METADATA_KEYS


def _strip_metadata_lines(text):
    return "\n".join(line for line in (text or "").splitlines() if not _is_metadata_line(line.strip()))


def _dedupe(items):
    deduped = []
    seen = set()
    for item in items:
        key = str(item).lower()
        if key not in seen:
            deduped.append(item)
            seen.add(key)
    return deduped


def _sentences(text):
    chunks = []
    for line in (text or "").splitlines():
        if _is_metadata_line(line.strip()):
            continue
        chunks.extend(re.split(r"(?<=[.!?])\s+", line))
    return [_normalize_space(chunk) for chunk in chunks if len(_normalize_space(chunk)) >= 10]


def _domains_for_text(text):
    lower = (text or "").lower()
    domains = []
    for domain, terms in DOMAIN_TERMS.items():
        if any(term in lower for term in terms):
            domains.append(domain)
    return domains


def _domain_for_obligation(obligation):
    lower = (obligation or "").lower()
    if any(term in lower for term in ("central inventory", "inventory of all outsourced", "outsourced it services", "inventory shall include")):
        return "it_inventory"
    if any(term in lower for term in ("board-approved it outsourcing policy", "outsourcing policy", "board", "senior management", "it function")):
        return "it_policy"
    if any(term in lower for term in ("outsourcing agreement", "agreement must include", "contract", "audit rights", "rbi inspection", "termination rights", "exit strategy")):
        return "outsourcing_contract"
    if any(term in lower for term in ("cloud", "data portability", "secure deletion", "cloud governance")):
        return "cloud"
    if any(term in lower for term in ("security operations centre", "security operations center", "outsourced soc", "soc", "alert rules", "incident response integration", "cyber incidents")):
        return "soc"
    if any(term in lower for term in ("audit reports", "periodic audits", "audit review", "sla monitoring", "contract reviews", "closure of observations")):
        return "it_audit"
    if any(term in lower for term in ("due diligence", "service provider", "third-party", "subcontractor", "concentration risk")):
        return "vendor_due_diligence"
    if any(term in lower for term in ("business continuity", "disaster recovery", "bcp", "drp", "resilience")):
        return "bcp_drp"
    if any(term in lower for term in ("retain", "preserve", "evidence", "audit trail", "audit", "archive")):
        return "evidence"
    if any(term in lower for term in ("notify", "customer notification", "affected customer", "grievance")):
        return "customer"
    if any(term in lower for term in ("kyc", "aml", "verification", "suspicious transaction")):
        return "kyc"
    if any(term in lower for term in ("cert-in", "cyber", "security log", "digital evidence", "incident")):
        return "cyber"
    if any(term in lower for term in ("branch", "branch-level", "escalation", "escalate")):
        return "branch"
    if any(term in lower for term in ("submit", "monthly", "quarterly", "rbi", "regulatory report")):
        return "reporting"
    if any(term in lower for term in ("fraud", "mule", "payment fraud", "digital fraud")):
        return "fraud"
    if any(term in lower for term in ("report", "submission")):
        return "reporting"
    domains = _domains_for_text(obligation)
    return domains[0] if domains else "reporting"


def _duration_minutes(phrase):
    if not phrase:
        return None

    lower = phrase.lower()
    number_match = re.search(r"(\d{1,4})", lower)
    number = int(number_match.group(1)) if number_match else 1

    if "hour" in lower:
        return number * 60
    if "day" in lower:
        return number * 24 * 60
    if "month" in lower or "monthly" in lower:
        return 30 * 24 * 60
    if "quarter" in lower or "quarterly" in lower:
        return 90 * 24 * 60
    if "annual" in lower or "annually" in lower:
        return 365 * 24 * 60
    if "immediate" in lower:
        return 0
    return None


def _deadline_phrases(text):
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
    found = []
    for pattern in patterns:
        found.extend(match.group(0) for match in re.finditer(pattern, text or "", flags=re.I))
    return _dedupe([_normalize_space(item) for item in found])


def _primary_deadline(text, scout_result=None):
    deadlines = _deadline_phrases(text)
    if deadlines:
        return deadlines[0]
    if scout_result and scout_result.get("deadline"):
        return scout_result["deadline"]
    return None


def _severity(domain, change_type, new_deadline=None, old_deadline=None):
    new_minutes = _duration_minutes(new_deadline)
    old_minutes = _duration_minutes(old_deadline)

    if change_type == "deadline_changed" and new_minutes is not None:
        if new_minutes <= 4 * 60:
            return "Critical"
        if old_minutes is not None and new_minutes < old_minutes:
            return "High"
    if domain in {"fraud", "cyber", "soc", "cloud", "vendor_due_diligence", "outsourcing_contract"}:
        return "Critical" if change_type in {"missing_policy", "deadline_changed"} else "High"
    if domain in {"it_inventory", "it_policy", "bcp_drp", "it_audit"}:
        return "High" if change_type in {"missing_policy", "new_obligation"} else "Medium"
    if domain in {"customer", "kyc", "privacy"}:
        return "High"
    if domain in {"evidence", "reporting", "branch"}:
        return "Medium"
    return "Low"


def _confidence(change_type, relevant_doc):
    if change_type == "missing_policy":
        return 0.74
    if relevant_doc:
        return 0.86
    return 0.68


def _document_content(document):
    if isinstance(document, dict):
        text = document.get("content") or document.get("text") or document.get("summary") or ""
        return _normalize_space(_strip_metadata_lines(text))
    return _normalize_space(_strip_metadata_lines(str(document or "")))


def _document_id(document, index):
    if isinstance(document, dict):
        return document.get("id") or document.get("file") or document.get("source") or f"prior_policy_{index + 1}"
    return f"prior_policy_{index + 1}"


def _prepare_prior_documents(old_policy=None, prior_documents=None):
    documents = []
    for index, document in enumerate(prior_documents or []):
        content = _document_content(document)
        if content:
            documents.append(
                {
                    "id": _document_id(document, index),
                    "content": content,
                    "source": "regulatory_memory",
                }
            )

    cleaned_old_policy = _normalize_space(_strip_metadata_lines(old_policy)) if old_policy else ""
    if cleaned_old_policy and old_policy != NO_PRIOR_POLICY:
        documents.append(
            {
                "id": "provided_old_policy",
                "content": cleaned_old_policy,
                "source": "provided_policy",
            }
        )

    return documents


def _score_document(document_text, scout_result, obligation_domains):
    text = document_text.lower()
    score = 0

    for keyword in scout_result.get("risk_keywords", []):
        if keyword.lower() in text:
            score += 3

    category = scout_result.get("category")
    if category and category.lower() in text:
        score += 2

    for domain in obligation_domains:
        for term in DOMAIN_TERMS.get(domain, ()):
            if term in text:
                score += 1

    return score


def _select_relevant_documents(documents, scout_result, obligations):
    obligation_domains = _dedupe([_domain_for_obligation(obligation) for obligation in obligations])
    scored = []
    for document in documents:
        score = _score_document(document["content"], scout_result, obligation_domains)
        if score > 0:
            scored.append((score, document))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [document for _, document in scored[:3]]


def _find_relevant_old_requirement(domain, documents):
    terms = DOMAIN_TERMS.get(domain, ())
    best_sentence = ""
    best_document = None
    best_score = 0

    for document in documents:
        for sentence in _sentences(document["content"]):
            lower = sentence.lower()
            score = sum(1 for term in terms if term in lower)
            if score > best_score:
                best_sentence = sentence
                best_document = document
                best_score = score

    if best_score == 0:
        return NO_PRIOR_POLICY, None
    return best_sentence, best_document


def _evidence_terms_present(text):
    lower = (text or "").lower()
    return any(term in lower for term in ("evidence", "audit", "retain", "preserve", "archive", "log", "trail"))


def _customer_impact_present(text):
    lower = (text or "").lower()
    return any(term in lower for term in ("customer", "notify", "notification", "impact", "grievance"))


def _reporting_frequency(text):
    lower = (text or "").lower()
    for frequency in ("monthly", "quarterly", "annually", "annual"):
        if frequency in lower:
            return frequency
    return None


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
    return ", ".join(_dedupe(items))


def _digital_fraud_evidence_for_obligation(obligation):
    lower = (obligation or "").lower()
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


def _it_outsourcing_evidence_for_obligation(obligation):
    lower = (obligation or "").lower()
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


def _change_type(old_requirement, new_requirement, domain):
    if old_requirement == NO_PRIOR_POLICY:
        return "missing_policy"

    old_deadline = _primary_deadline(old_requirement)
    new_deadline = _primary_deadline(new_requirement)
    if old_deadline and new_deadline and old_deadline.lower() != new_deadline.lower():
        return "deadline_changed"
    if not old_deadline and new_deadline:
        return "new_obligation"

    old_frequency = _reporting_frequency(old_requirement)
    new_frequency = _reporting_frequency(new_requirement)
    if old_frequency != new_frequency and new_frequency:
        return "reporting_frequency_changed"

    if _evidence_terms_present(new_requirement) and not _evidence_terms_present(old_requirement):
        return "evidence_required"

    if _customer_impact_present(new_requirement) and not _customer_impact_present(old_requirement):
        return "new_obligation"

    if domain == "branch" and "branch" not in old_requirement.lower():
        return "department_owner_missing"

    if "audit" in new_requirement.lower() and "audit" not in old_requirement.lower():
        return "audit_trail_missing"

    return "new_obligation"


def _gap_dimensions(new_requirement):
    lower = (new_requirement or "").lower()
    dimensions = []
    deadline = _primary_deadline(new_requirement)

    if deadline:
        dimensions.append(f"timeline ({deadline})")
    if any(term in lower for term in ("report", "submit", "monthly", "quarterly", "rbi")):
        dimensions.append("reporting workflow")
    if any(term in lower for term in ("evidence", "proof", "log", "record", "retain", "preserve")):
        dimensions.append("evidence capture")
    if any(term in lower for term in ("retain", "preserve", "archive", "for ")) and any(term in lower for term in ("year", "month", "day")):
        dimensions.append("retention period")
    if any(term in lower for term in ("owner", "sign-off", "approval", "responsibility", "accountable")):
        dimensions.append("owner sign-off")
    if any(term in lower for term in ("escalat", "branch", "cert-in", "incident response")):
        dimensions.append("escalation workflow")
    if any(term in lower for term in ("audit trail", "audit log", "audit report", "audit rights", "periodic audits")):
        dimensions.append("audit trail")
    if any(term in lower for term in ("notify", "customer notification", "affected customer")):
        dimensions.append("customer notification proof")
    if any(term in lower for term in ("agreement", "contract", "clause", "termination rights", "exit strategy")):
        dimensions.append("agreement clause review")
    if any(term in lower for term in ("due diligence", "service provider", "third-party")):
        dimensions.append("service provider due diligence")

    return _dedupe(dimensions) or ["specific workflow, evidence, owner, and audit trail"]


def _gap_message(change_type, old_requirement, new_requirement, domain):
    dimensions = ", ".join(_gap_dimensions(new_requirement))
    old_deadline = _primary_deadline(old_requirement) if old_requirement != NO_PRIOR_POLICY else None
    new_deadline = _primary_deadline(new_requirement)

    if change_type == "deadline_changed":
        return f"Existing {domain} process uses timeline {old_deadline or 'not captured'} but new circular requires {new_deadline}; timeline update is missing."
    if change_type == "missing_policy":
        return f"No matching internal {domain} policy found; missing {dimensions} required by: {new_requirement}"
    if change_type == "reporting_frequency_changed":
        return f"Existing {domain} reporting workflow does not capture the required frequency in: {new_requirement}"
    if change_type == "evidence_required":
        return f"Existing {domain} policy lacks {dimensions} required by: {new_requirement}"
    if change_type == "department_owner_missing":
        return f"Existing process does not define owner sign-off or escalation workflow required by: {new_requirement}"
    if change_type == "audit_trail_missing":
        return f"Existing process does not include the required audit trail for: {new_requirement}"
    return f"Existing {domain} process lacks {dimensions} required by: {new_requirement}"


def _department_for_gap(domain, obligation):
    lower = (obligation or "").lower()
    if domain == "reporting" and any(term in lower for term in ("fraud", "mule", "digital fraud")):
        return "Fraud Risk Department + Compliance Office"
    if domain == "evidence" and any(term in lower for term in ("cyber", "digital evidence", "security log")):
        return "Cybersecurity / IT Security + Internal Audit"
    if domain == "it_inventory" and any(term in lower for term in ("compliance report", "closure report", "reporting")):
        return "Compliance Department + IT Vertical"
    return DEPARTMENT_BY_DOMAIN.get(domain, "Compliance Office")


def _evidence_for_gap(domain, obligation, scout=None):
    lower = (obligation or "").lower()
    if _is_digital_fraud_context(obligation, scout):
        return _digital_fraud_evidence_for_obligation(obligation)
    if _is_it_outsourcing_context(obligation, scout):
        return _it_outsourcing_evidence_for_obligation(obligation)
    if "customer notification" in lower or "affected customer" in lower or "notify" in lower:
        return "Customer notification proof, timestamp, delivery status, and exception approval"
    if domain == "reporting" and any(term in lower for term in ("monthly", "report", "submit")):
        return "Monthly monitoring report, maker-checker approval, and Compliance Office submission proof"
    return EVIDENCE_BY_DOMAIN.get(domain, "Compliance evidence pack and owner sign-off")


def _fixed_it_advisory(domain):
    fixed_rows = {
        "it_inventory": {
            "business_vertical": "IT Vertical",
            "sub_vertical": "Infrastructure Management",
            "scope": "Central inventory of outsourced IT services",
        },
        "it_policy": {
            "business_vertical": "Compliance Department",
            "sub_vertical": "Regulatory Compliance",
            "scope": "Board-approved IT outsourcing policy and governance reporting",
        },
        "vendor_due_diligence": {
            "business_vertical": "Procurement & Vendor Management",
            "sub_vertical": "Third-Party Risk Management",
            "scope": "Service provider due diligence and outsourcing risk review",
        },
        "outsourcing_contract": {
            "business_vertical": "Legal Department",
            "sub_vertical": "Contract Management",
            "scope": "Outsourcing agreement clauses, audit rights, termination, and exit",
        },
        "cloud": {
            "business_vertical": "IT Vertical",
            "sub_vertical": "Cloud Operations",
            "scope": "Cloud governance, resilience, logging, portability, and secure deletion",
        },
        "soc": {
            "business_vertical": "Cybersecurity Wing",
            "sub_vertical": "Security Operations Center (SOC)",
            "scope": "Outsourced SOC oversight, alert rules, logs, and escalation",
        },
        "bcp_drp": {
            "business_vertical": "Risk Management",
            "sub_vertical": "Operational Risk",
            "scope": "BCP/DR testing for material outsourced IT services",
        },
        "it_audit": {
            "business_vertical": "Internal Audit",
            "sub_vertical": "Information Systems Audit",
            "scope": "Service provider audit reports, SLA monitoring, and closure review",
        },
    }
    row = fixed_rows.get(domain)
    if not row:
        return None
    return {
        **row,
        "primary_regulator": "RBI",
        "regulatory_reference": "Master Direction on Outsourcing of Information Technology Services",
        "official_link": "",
        "match_score": 100,
        "assignment_basis": f"Deterministic IT outsourcing domain mapping: {domain}.",
    }


def _fallback_advisory(department, obligation):
    lower = (obligation or "").lower()
    if "customer" in lower or "notify" in lower:
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
        "scope": "Mapped through deterministic department fallback",
        "primary_regulator": "RBI",
        "regulatory_reference": reference,
        "official_link": "",
        "match_score": 0,
        "assignment_basis": "No strong bank advisory row matched; deterministic fallback used from obligation/domain mapping.",
    }


def _advisory_for_gap(obligation, domain, scout, department):
    if domain == "customer":
        return _fallback_advisory(department, obligation)

    fixed_advisory = _fixed_it_advisory(domain)
    if fixed_advisory:
        return fixed_advisory

    matches = match_department_advisory(
        obligation,
        obligations=[obligation],
        risk_keywords=RISK_KEYWORDS_BY_DOMAIN.get(domain, []),
        category=scout.get("category"),
        limit=1,
    )
    if matches and matches[0].get("match_score", 0) >= 20:
        return matches[0]

    return _fallback_advisory(department, obligation)


def _basis(change_type, old_requirement, new_requirement):
    if old_requirement == NO_PRIOR_POLICY:
        return "No relevant old RBI circular or internal policy was found in available regulatory memory."
    return f"Compared old requirement [{old_requirement}] with new requirement [{new_requirement}]."


def compare_policy(old_policy=None, new_policy=None, scout_result=None, prior_documents=None):
    """
    Compare new circular requirements against relevant old policy memory.

    This function intentionally avoids word-difference/token-difference output.
    It returns structured policy gaps suitable for MAP generation.
    """
    content = _normalize_space(new_policy)
    scout = scout_result or parse_circular_text(content)
    obligations = scout.get("obligations") or []
    engine_notes = ["Semantic Delta Agent used deterministic offline comparison."]

    if not content or not obligations:
        return {
            "gap_found": False,
            "summary": "No strong obligations were available for delta comparison.",
            "risk_level": "Low",
            "key_changes": [],
            "policy_gaps": [],
            "analysis_by": "deterministic_delta",
            "engine_notes": engine_notes + ["Delta returned safe low-risk fallback for empty or weak input."],
        }

    documents = _prepare_prior_documents(old_policy=old_policy, prior_documents=prior_documents)
    relevant_documents = _select_relevant_documents(documents, scout, obligations)
    if not relevant_documents:
        engine_notes.append("No matching prior policy found in available regulatory memory.")

    gaps = []
    seen = set()
    for obligation in obligations:
        domain = _domain_for_obligation(obligation)
        old_requirement, source_document = _find_relevant_old_requirement(domain, relevant_documents)
        change_type = _change_type(old_requirement, obligation, domain)
        deadline = _primary_deadline(obligation)
        old_deadline = _primary_deadline(old_requirement) if old_requirement != NO_PRIOR_POLICY else None
        gap_text = _gap_message(change_type, old_requirement, obligation, domain)
        department = _department_for_gap(domain, obligation)
        advisory = _advisory_for_gap(obligation, domain, scout, department)
        key = (gap_text.lower(), obligation.lower())
        if key in seen:
            continue
        seen.add(key)

        gaps.append(
            {
                "id": f"GAP-{len(gaps) + 1:03d}",
                "gap": gap_text,
                "policy_gap": gap_text,
                "basis": _basis(change_type, old_requirement, obligation),
                "severity": _severity(domain, change_type, deadline, old_deadline),
                "old_requirement": old_requirement,
                "new_requirement": obligation,
                "affected_department": department,
                "deadline": deadline,
                "evidence_required": _evidence_for_gap(domain, obligation, scout),
                "confidence": _confidence(change_type, source_document),
                "source": source_document["id"] if source_document else "No matching prior policy found",
                "change_type": change_type,
                "business_vertical": advisory["business_vertical"],
                "sub_vertical": advisory["sub_vertical"],
                "primary_regulator": advisory["primary_regulator"],
                "regulatory_reference": advisory["regulatory_reference"],
                "official_link": advisory["official_link"],
                "match_score": advisory.get("match_score", 0),
                "assignment_basis": advisory["assignment_basis"],
            }
        )

        if len(gaps) >= 12:
            break

    if not gaps:
        fallback_obligation = obligations[0] if obligations else content[:180]
        fallback_advisory = _advisory_for_gap(
            fallback_obligation,
            _domain_for_obligation(fallback_obligation),
            scout,
            "Compliance Office",
        )
        gaps.append(
            {
                "id": "GAP-001",
                "gap": "No material policy gap detected; manual compliance confirmation is recommended.",
                "policy_gap": "No material policy gap detected; manual compliance confirmation is recommended.",
                "basis": "Scout obligations were compared with available regulatory memory and no strong delta was detected.",
                "severity": "Low",
                "old_requirement": "Relevant prior policy appears broadly aligned.",
                "new_requirement": fallback_obligation,
                "affected_department": "Compliance Office",
                "deadline": scout.get("deadline"),
                "evidence_required": "Compliance review note and owner sign-off",
                "confidence": 0.62,
                "source": "deterministic_delta",
                "change_type": "manual_review",
                "business_vertical": fallback_advisory["business_vertical"],
                "sub_vertical": fallback_advisory["sub_vertical"],
                "primary_regulator": fallback_advisory["primary_regulator"],
                "regulatory_reference": fallback_advisory["regulatory_reference"],
                "official_link": fallback_advisory["official_link"],
                "match_score": fallback_advisory.get("match_score", 0),
                "assignment_basis": fallback_advisory["assignment_basis"],
            }
        )

    severity_order = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}
    highest = max(gaps, key=lambda gap: severity_order.get(gap["severity"], 1))["severity"]

    return {
        "gap_found": True,
        "summary": f"Delta comparison produced {len(gaps)} meaningful policy gap(s).",
        "risk_level": highest,
        "key_changes": [gap["policy_gap"] for gap in gaps[:5]],
        "policy_gaps": gaps,
        "analysis_by": "deterministic_delta",
        "engine_notes": engine_notes,
    }
