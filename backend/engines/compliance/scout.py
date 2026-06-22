import hashlib
import re
from datetime import datetime
from pathlib import Path

from .advisory_mapping import match_department_advisory

try:
    from .local_llm import extract_circular_fields, get_llm_mode, get_ollama_model, is_llm_enabled
except Exception:
    extract_circular_fields = None

    def get_llm_mode():
        return "rules"

    def get_ollama_model():
        return "unavailable"

    def is_llm_enabled():
        return False


CIRCULARS_DIR = Path(__file__).resolve().parents[2] / "data" / "circulars"

OBLIGATION_PHRASES = (
    "must",
    "shall",
    "required to",
    "require prior approval",
    "should ensure",
    "directed to",
    "report",
    "submit",
    "retain",
    "notify",
    "monitor",
    "escalate",
    "reconcile",
    "verify",
    "maintain",
    "implement",
    "preserve",
    "disclose",
    "review",
    "update",
    "inform",
    "apply",
    "surrender",
    "liable",
    "public notice",
)

OBLIGATION_VERBS = (
    "report",
    "submit",
    "retain",
    "notify",
    "monitor",
    "escalate",
    "reconcile",
    "verify",
    "maintain",
    "implement",
    "preserve",
    "disclose",
    "review",
    "update",
    "configure",
    "assign",
    "complete",
    "ensure",
    "inform",
    "apply",
    "surrender",
    "conduct",
    "perform",
    "test",
)

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

LLM_STOPWORDS = {
    "bank",
    "banks",
    "shall",
    "must",
    "should",
    "with",
    "within",
    "from",
    "that",
    "this",
    "they",
    "their",
    "there",
    "where",
    "which",
    "circular",
    "requirement",
    "requirements",
    "compliance",
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

PSO_CONTEXT_TERMS = (
    "non-bank pso",
    "non-bank payment system operator",
    "payment system operator",
    "takeover/acquisition of control",
    "acquisition of control",
    "sale/transfer of payment activity",
    "payment activity transfer",
    "dpss",
    "certificate of authorisation",
    "certificate of authorization",
    "payment and settlement systems act",
    "form a",
    "payment aggregator",
    "payment gateway",
    "prepaid payment instrument",
    "ppi",
)

DEADLINE_PATTERNS = (
    r"within\s+\d{1,3}\s+(?:hours?|days?|months?|years?)",
    r"by\s+\d{1,2}[/-]\d{1,2}[/-]\d{2,4}",
    r"no later than\s+[A-Za-z0-9 ,/-]+",
    r"before end of month",
    r"immediate effect",
    r"with immediate effect",
    r"monthly",
    r"quarterly",
    r"annually",
    r"annual",
)

DATE_PATTERNS = (
    r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
    r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b",
    r"\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b",
    r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b",
)

RISK_RULES = (
    ("payment system approval", ("non-bank pso", "payment system operator", "takeover/acquisition of control", "acquisition of control", "sale/transfer of payment activity", "dpss", "certificate of authorisation", "certificate of authorization", "form a")),
    ("digital payment", ("payment aggregator", "payment gateway", "prepaid payment instrument", "ppi", "payment and settlement systems act")),
    ("IT outsourcing", ("it outsourcing", "outsourced it", "central inventory", "outsourcing policy", "outsourcing arrangement", "outsourcing agreement")),
    ("third-party risk", ("third-party", "service provider", "vendor", "due diligence", "subcontractor")),
    ("cloud outsourcing", ("cloud", "cloud service provider", "data portability", "secure deletion")),
    ("SOC outsourcing", ("security operations centre", "security operations center", "outsourced soc", "soc effectiveness")),
    ("business continuity", ("business continuity", "disaster recovery", "bcp", "drp", "resilience")),
    ("digital fraud", ("digital fraud", "payment fraud", "cyber-enabled fraud")),
    ("fraud", ("fraud", "fraudulent")),
    ("mule account", ("mule account", "mule")),
    ("KYC", ("kyc", "re-verification", "reverification", "identity verification")),
    ("AML", ("aml", "anti-money laundering", "suspicious transaction")),
    ("cyber incident", ("cyber incident", "cybersecurity", "security log", "security incident")),
    ("customer protection", ("customer protection", "affected customer", "customer notification")),
    ("reporting", ("report", "submit", "submission", "rbi")),
    ("audit", ("audit", "audit trail", "audit log")),
    ("evidence retention", ("evidence", "retain", "preserve", "archive")),
    ("operational risk", ("operational risk", "operations")),
    ("branch compliance", ("branch", "branch-level")),
    ("DPDP/data privacy", ("dpdp", "data privacy", "personal data", "privacy")),
    ("transaction monitoring", ("transaction monitoring", "monitoring", "surveillance")),
    ("grievance", ("grievance", "complaint")),
    ("suspicious transaction", ("suspicious transaction", "suspicious account")),
)

CATEGORY_RULES = (
    ("Payment System Operator / RBI Approval", ("non-bank pso", "payment system operator", "takeover/acquisition of control", "acquisition of control", "sale/transfer of payment activity", "dpss", "certificate of authorisation", "certificate of authorization", "form a")),
    ("Digital Fraud Reporting", ("digital fraud", "payment fraud", "fraud reporting")),
    ("IT Outsourcing / Third-Party Risk", ("it outsourcing", "outsourced it", "central inventory", "outsourcing policy", "service provider", "third-party", "outsourcing agreement", "cloud service provider", "security operations centre", "security operations center")),
    ("Mule Account Monitoring", ("mule account", "mule", "suspicious account")),
    ("KYC / AML Compliance", ("kyc", "aml", "suspicious transaction", "dormant")),
    ("Cyber Incident Compliance", ("cyber incident", "cybersecurity", "security log")),
    ("Customer Protection", ("customer protection", "customer notification", "grievance")),
    ("Evidence Retention and Audit", ("audit", "evidence", "retain", "preserve")),
    ("Data Privacy / DPDP", ("dpdp", "data privacy", "personal data")),
    ("Regulatory Reporting", ("report", "submit", "rbi", "submission")),
)

DEPARTMENT_RULES = (
    ("Payments Vertical / Payment Systems Compliance", ("non-bank pso", "payment system operator", "payment activity", "payment aggregator", "payment gateway", "ppi", "dpss", "form a")),
    ("Regulatory Compliance Department", ("prior approval of rbi", "rbi approval", "inform rbi", "dpss", "payment and settlement systems act")),
    ("Legal & Secretarial", ("takeover", "acquisition of control", "sale/transfer", "transferor", "transferee", "legal", "public notice")),
    ("Board Governance / Company Secretary", ("change in management", "directors", "board approval", "shareholder")),
    ("Risk & Compliance", ("regulatory/supervisory action", "supervisory action", "risk", "compliance sign-off")),
    ("Operations / Merchant Acquiring", ("merchants", "agents", "bankers", "customers", "stakeholders", "merchant acquiring")),
    ("IT Vertical", ("outsourced it services", "it outsourcing", "application maintenance", "data centre", "network services", "technology owner", "central inventory", "cloud governance")),
    ("Procurement & Vendor Management", ("service provider", "vendor", "third-party", "due diligence", "subcontractor", "cloud provider")),
    ("Legal Department", ("outsourcing agreement", "legally binding", "contract", "audit rights", "termination rights", "exit strategy", "rbi inspection access")),
    ("Risk Management", ("risk assessment", "concentration risk", "operational risk", "technology risk", "risk management", "resilience")),
    ("Cybersecurity Wing", ("outsourced security operations", "security operations centre", "security operations center", "soc", "alert rules", "incident response integration")),
    ("Compliance Department", ("board-approved it outsourcing policy", "outsourcing policy", "regulatory reporting", "closure report", "compliance department")),
    ("Fraud Risk Department", ("fraud", "mule account", "mule", "digital fraud", "payment fraud", "reporting")),
    ("Cybersecurity / IT Security", ("cyber", "security log", "digital evidence", "incident", "authentication")),
    ("Compliance Office", ("rbi", "compliance", "regulatory", "submit", "report")),
    ("Branch Operations", ("branch", "branch-level", "escalation")),
    ("Customer Support / Grievance Cell", ("customer notification", "affected customer", "grievance", "complaint")),
    ("Internal Audit", ("audit", "audit trail", "evidence retention", "retain", "preserve")),
    ("Legal Department", ("legal", "disclose", "regulatory interpretation")),
    ("Data Privacy / DPDP Office", ("dpdp", "data privacy", "personal data", "privacy")),
    ("Risk Management", ("operational risk", "enterprise risk", "risk management")),
    ("Operations Department", ("operations", "reconcile", "process")),
    ("KYC / AML Compliance", ("kyc", "aml", "verification", "suspicious transaction", "dormant")),
)

EVIDENCE_RULES = (
    ("RBI prior approval application, DPSS acknowledgement, Board approval, Legal review note, and Compliance sign-off", ("prior approval of rbi", "rbi approval", "takeover", "acquisition of control")),
    ("Payment activity transfer checklist, Legal review note, Board approval, and Compliance sign-off", ("sale/transfer of payment activity", "payment activity transfer", "transferor", "transferee")),
    ("DPSS application pack, proposed director details, shareholder details, and closure record", ("dpss", "director", "shareholder")),
    ("Public notice proof and stakeholder communication proof", ("public notice", "stakeholders", "agents", "bankers", "customers", "merchants")),
    ("Form A submission, Certificate of Authorisation, CoA surrender proof, and DPSS acknowledgement", ("form a", "certificate of authorisation", "certificate of authorization", "surrender")),
    ("Outsourcing policy and management approval", ("board-approved it outsourcing policy", "outsourcing policy", "senior management")),
    ("Outsourcing policy, audit report, and management approval", ("central inventory", "inventory of outsourced it", "outsourced it services")),
    ("Service provider due diligence checklist and management approval", ("due diligence", "service provider", "third-party", "subcontractor")),
    ("Outsourcing agreement clause checklist, exit strategy, and management approval", ("outsourcing agreement", "legally binding", "audit rights", "rbi inspection", "termination rights", "exit strategy")),
    ("Cloud governance checklist and audit report", ("cloud", "data portability", "secure deletion", "cloud governance")),
    ("SOC escalation workflow evidence and audit report", ("security operations centre", "security operations center", "soc", "alert rules", "metadata", "incident response integration")),
    ("BCP/DR test report and management approval", ("business continuity", "disaster recovery", "bcp", "drp", "resilience")),
    ("Audit report and management approval", ("audit report", "sla monitoring", "risk review", "closure of observations")),
    ("Fraud reporting SOP, transaction logs, fraud monitoring report, owner sign-off, and closure timestamp", ("fraud", "digital fraud", "payment fraud")),
    ("Customer notification proof, transaction logs, owner sign-off, and closure timestamp", ("notify", "customer notification", "affected customer", "grievance")),
    ("Transaction logs, audit trail export, owner sign-off, and closure timestamp", ("retain", "preserve", "evidence", "audit trail", "archive")),
    ("Monthly monitoring report, maker-checker approval, and submission proof", ("monthly", "report", "submit")),
    ("Branch escalation register with owner sign-off and closure timestamp", ("branch", "escalate", "branch-level")),
    ("KYC verification tracker, exception approvals, and customer communication proof", ("kyc", "aml", "verification", "suspicious transaction")),
    ("Security log export, incident ticket, and digital evidence hash", ("cyber", "security log", "incident", "digital evidence")),
    ("Regulatory submission acknowledgement and Compliance Office sign-off", ("rbi", "regulatory", "compliance office")),
)


def _normalize_space(value):
    return re.sub(r"\s+", " ", value or "").strip()


def _normalize_pdf_text(text):
    if not text:
        return ""

    normalized = (
        str(text)
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\u00a0", " ")
        .replace("–", "-")
        .replace("—", "-")
    )
    replacements = (
        (r"\bReview\s+ed\b", "Reviewed"),
        (r"\bT\s+he\b", "The"),
        (r"\bt\s+he\b", "the"),
        (r"\bbuy\s+er\b", "buyer"),
        (r"\bBuy\s+er\b", "Buyer"),
        (r"\bsell\s+er\b", "seller"),
        (r"\btrans\s+feror\b", "transferor"),
        (r"\btrans\s+feree\b", "transferee"),
        (r"\bBi\s*-\s*monthly\b", "Bi-monthly"),
        (r"\bnon\s*-\s*bank\b", "non-bank"),
        (r"\bsale\s*/\s*transfer\b", "sale/transfer"),
        (r"\btakeover\s*/\s*acquisition\b", "takeover/acquisition"),
        (r"\bCertificate\s+of\s+Authori[sz]\s+ation\b", "Certificate of Authorisation"),
        (r"\bPayment\s+System\s+Operator\s+s\b", "Payment System Operators"),
        (r"\bP\s*S\s*O\b", "PSO"),
    )
    for pattern, replacement in replacements:
        normalized = re.sub(pattern, replacement, normalized, flags=re.I)

    raw_lines = [re.sub(r"[ \t\f\v]+", " ", line).strip() for line in normalized.splitlines()]
    merged_lines = []
    for line in raw_lines:
        if not line:
            if merged_lines and merged_lines[-1] != "":
                merged_lines.append("")
            continue

        if not merged_lines or merged_lines[-1] == "":
            merged_lines.append(line)
            continue

        previous = merged_lines[-1]
        previous_lower = previous.lower().rstrip(" :-")
        current_starts_continuation = bool(
            re.match(
                r"^(?:and|or|of|for|to|in|with|by|whether|where|which|who|whose|"
                r"including|before|after|when|wherever|not|whether|the|a|an|\([ivxlcdm0-9]+\)|[a-z])\b",
                line,
                flags=re.I,
            )
        )
        previous_incomplete = (
            not re.search(r"[.!?;:]$", previous)
            or previous_lower.endswith((" of", " and", " or", " for", " to", " for obtaining", " in the following cases"))
        )
        if previous_incomplete or current_starts_continuation:
            merged_lines[-1] = f"{previous} {line}"
        else:
            merged_lines.append(line)

    normalized = "\n".join(merged_lines)
    normalized = re.sub(r"\s*/\s*", "/", normalized)
    normalized = re.sub(r"\s+([,.;:])", r"\1", normalized)
    normalized = re.sub(r"\(\s+", "(", normalized)
    normalized = re.sub(r"\s+\)", ")", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def _clean_line(line):
    return re.sub(r"^\s*[-*0-9.)]+\s*", "", line or "").strip()


def _is_metadata_line(line):
    if ":" not in (line or ""):
        return False
    key = line.split(":", 1)[0].strip().lower()
    return key in METADATA_KEYS


def _dedupe(items):
    deduped = []
    seen = set()
    for item in items:
        normalized = _normalize_space(str(item))
        key = re.sub(r"[^a-z0-9]+", " ", normalized.lower()).strip()
        key = re.sub(r"^(?:the|a|an)\s+", "", key)
        if normalized and key not in seen:
            deduped.append(normalized)
            seen.add(key)
    return deduped


def _is_digital_fraud_context(text, risk_keywords=None, category=None):
    context = " ".join(
        [
            str(text or ""),
            str(category or ""),
            " ".join(str(item) for item in (risk_keywords or [])),
        ]
    ).lower()
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


def _is_pso_payment_context(text, risk_keywords=None, category=None):
    context = " ".join(
        [
            str(text or ""),
            str(category or ""),
            " ".join(str(item) for item in (risk_keywords or [])),
        ]
    ).lower()
    return any(term in context for term in PSO_CONTEXT_TERMS)


def _is_it_outsourcing_context(text, risk_keywords=None, category=None):
    context = " ".join(
        [
            str(text or ""),
            str(category or ""),
            " ".join(str(item) for item in (risk_keywords or [])),
        ]
    ).lower()
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


def _find_first(patterns, text):
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.I)
        if match:
            return _normalize_space(match.group(0))
    return None


def _extract_title(text, file_name):
    for line in text.splitlines():
        cleaned = _clean_line(line)
        if not cleaned:
            continue
        lower = cleaned.lower()
        if lower.startswith("title:"):
            return _normalize_space(cleaned.split(":", 1)[1])
        if lower.startswith("subject:"):
            return _normalize_space(cleaned.split(":", 1)[1])
        if _is_metadata_line(cleaned):
            continue
        if "circular" not in lower and len(cleaned) >= 12:
            return cleaned[:140]
    return Path(file_name or "uploaded circular").stem.replace("_", " ").title()


def _extract_circular_id(text, file_name):
    metadata_match = re.search(r"^\s*circular_id\s*:\s*([^\n\r]+)", text or "", flags=re.I | re.M)
    if metadata_match:
        return _normalize_space(metadata_match.group(1))

    patterns = (
        r"\bRBI[/A-Z0-9.-]*[/ -]\d{4}[/A-Z0-9.-]*\b",
        r"\bRBI\s+Circular\s+No\.?\s*[:\-]?\s*[A-Z0-9/.-]+\b",
        r"\bCircular\s+No\.?\s*[:\-]?\s*[A-Z0-9/.-]+\b",
    )
    found = _find_first(patterns, text)
    if found:
        return found.replace("Circular No.", "").replace("RBI Circular No.", "").strip(" :-")

    seed = f"{file_name or 'circular'}:{text[:120]}".encode("utf-8", errors="ignore")
    digest = hashlib.sha1(seed).hexdigest()[:8].upper()
    return f"RBI-GEN-{datetime.utcnow().year}-{digest}"


def _extract_issue_date(text):
    issue_date = re.search(r"^\s*issue_date\s*:\s*([^\n\r]+)", text or "", flags=re.I | re.M)
    if issue_date:
        return _normalize_space(issue_date.group(1))
    date_line = re.search(r"\bDate\s*:\s*([^\n\r]+)", text, flags=re.I)
    if date_line:
        return _normalize_space(date_line.group(1))
    return _find_first(DATE_PATTERNS, text)


def _extract_deadlines(text):
    deadlines = []
    for pattern in DEADLINE_PATTERNS:
        deadlines.extend(match.group(0) for match in re.finditer(pattern, text, flags=re.I))
    return _dedupe(deadlines)


def _extract_effective_date(text, deadlines):
    effective_from = re.search(r"^\s*effective_from\s*:\s*([^\n\r]+)", text or "", flags=re.I | re.M)
    if effective_from:
        return _normalize_space(effective_from.group(1))
    effective_match = re.search(r"effective\s+(?:from|date)?\s*[:\-]?\s*([A-Za-z0-9 ,/-]+)", text, flags=re.I)
    if effective_match:
        return _normalize_space(effective_match.group(1))
    if any("immediate effect" in deadline.lower() for deadline in deadlines):
        return "with immediate effect"
    return None


def _split_obligation_clauses(sentence):
    prepared = re.sub(
        r"\s+and\s+(?=(?:notify|retain|submit|maintain|monitor|escalate|reconcile|verify|preserve|disclose|review|update|implement|conduct|perform|test|inform|apply|surrender)\b)",
        ", ",
        sentence,
        flags=re.I,
    )
    split_pattern = (
        r",\s+(?=(?:and\s+)?(?:notify|retain|submit|maintain|monitor|escalate|"
        r"reconcile|verify|preserve|disclose|review|update|implement|conduct|"
        r"perform|test|report|inform|apply|surrender)\b)"
    )
    return [_clean_line(part) for part in re.split(split_pattern, prepared) if _clean_line(part)]


def _has_obligation_phrase(text):
    lower = text.lower()
    return any(phrase in lower for phrase in OBLIGATION_PHRASES) or lower.startswith(OBLIGATION_VERBS)


def _normalize_obligation(clause):
    cleaned = _normalize_space(clause).strip(" ,;")
    cleaned = re.sub(r"^(?:and\s+)", "", cleaned, flags=re.I)
    if not cleaned:
        return ""
    return cleaned[0].upper() + cleaned[1:]


def _is_incomplete_obligation(clause):
    lower = _normalize_space(clause).lower().strip(" .;:-")
    if len(lower) < 24:
        return True
    if "in the following cases" in lower:
        return True
    if lower.startswith(("reviewed and they shall", "reviewed they shall")):
        return True
    return lower.endswith(
        (
            " of",
            " and",
            " or",
            " to",
            " for",
            " for obtaining",
            " in the following cases",
            " in the following cases -",
            " in the following cases –",
        )
    )


def _extract_pso_obligations(text):
    normalized = _normalize_space(text)
    lower = normalized.lower()
    if not _is_pso_payment_context(lower):
        return []

    obligations = []
    if "takeover" in lower or "acquisition of control" in lower:
        obligations.append(
            "Non-bank PSOs shall require prior approval of RBI for takeover/acquisition of control, whether or not it results in change of management."
        )
    if "sale/transfer of payment activity" in lower or "payment activity transfer" in lower:
        if "not authorised" in lower or "not authorized" in lower or "not authorised to undertake similar" in lower or "not authorized to undertake similar" in lower:
            obligations.append(
                "Non-bank PSOs shall require prior approval of RBI for sale/transfer of payment activity to an entity not authorised to undertake similar activity."
            )
        if "authorised" in lower or "authorized" in lower:
            obligations.append(
                "Non-bank PSOs shall inform RBI within 15 calendar days for sale/transfer of payment activity to an entity authorised for similar activity."
            )
    if "change in management" in lower or "directors" in lower or "director" in lower:
        obligations.append(
            "Non-bank PSOs shall inform RBI within 15 calendar days for change in management/directors."
        )
    if "public notice" in lower:
        obligations.append(
            "After obtaining RBI approval, a public notice of at least 15 calendar days shall be given before effecting changes."
        )
    if any(term in lower for term in ("stakeholders", "agents", "bankers", "customers", "merchants")):
        obligations.append(
            "The seller/transferor non-bank PSO shall inform stakeholders including agents, bankers, customers, and merchants at least 15 calendar days before changes."
        )
    if "form a" in lower or "apply for authorisation" in lower or "apply for authorization" in lower:
        obligations.append(
            "Buyer/transferee must apply for authorisation in Form A when required."
        )
    if "surrender" in lower and ("certificate of authorisation" in lower or "certificate of authorization" in lower or "coa" in lower):
        obligations.append(
            "Seller/transferor PSO shall surrender its Certificate of Authorisation where applicable."
        )
    if "regulatory/supervisory action" in lower or "supervisory action" in lower:
        obligations.append(
            "Buyer/transferee shall be liable for regulatory/supervisory action for periods prior to sale/transfer."
        )

    return obligations


def extract_obligations(text):
    obligations = []
    normalized_text = _normalize_pdf_text(text)
    pso_obligations = _extract_pso_obligations(normalized_text)
    obligations.extend(pso_obligations)
    candidates = []
    for line in normalized_text.splitlines():
        cleaned = _clean_line(line)
        if cleaned and not _is_metadata_line(cleaned):
            candidates.extend(re.split(r"(?<=[.!?])\s+", cleaned))

    if not candidates:
        candidates = re.split(r"(?<=[.!?])\s+", normalized_text)

    for sentence in candidates:
        for clause in _split_obligation_clauses(sentence):
            if len(clause) < 8:
                continue
            if _is_incomplete_obligation(clause):
                continue
            if _has_obligation_phrase(clause):
                obligations.append(_normalize_obligation(clause))

    return _dedupe(obligations)[:16]


def _detect_risk_keywords(text):
    lower = text.lower()
    found = []
    for label, terms in RISK_RULES:
        if any(term in lower for term in terms):
            found.append(label)
    return _dedupe(found)


def _detect_category(text, risk_keywords):
    lower = text.lower()
    if _is_pso_payment_context(lower, risk_keywords):
        return "Payment System Operator / RBI Approval"
    for category, terms in CATEGORY_RULES:
        if any(term in lower for term in terms):
            return category
    if risk_keywords:
        return risk_keywords[0].title()
    return "General Regulatory Compliance"


def _detect_departments(text, obligations):
    lower = f"{text} {' '.join(obligations)}".lower()
    if _is_pso_payment_context(lower):
        departments = ["Payments Vertical / Payment Systems Compliance", "Regulatory Compliance Department"]
        if any(term in lower for term in ("takeover", "acquisition of control", "sale/transfer", "transferor", "transferee", "public notice")):
            departments.append("Legal & Secretarial")
        if any(term in lower for term in ("directors", "director", "management", "shareholder", "board")):
            departments.append("Board Governance / Company Secretary")
        if any(term in lower for term in ("stakeholders", "agents", "bankers", "customers", "merchants")):
            departments.append("Operations / Merchant Acquiring")
        if any(term in lower for term in ("regulatory/supervisory action", "supervisory action", "risk")):
            departments.append("Risk & Compliance")
        if any(term in lower for term in ("audit", "evidence review")):
            departments.append("Internal Audit")
        return _dedupe(departments)

    departments = []
    for department, terms in DEPARTMENT_RULES:
        if any(term in lower for term in terms):
            departments.append(department)
    if not departments:
        departments.append("Compliance Office")
    return _dedupe(departments)


def _detect_evidence(text, obligations, risk_keywords=None, category=None):
    lower = f"{text} {' '.join(obligations)}".lower()
    if _is_pso_payment_context(lower, risk_keywords, category):
        return list(PSO_EVIDENCE)
    if _is_digital_fraud_context(lower, risk_keywords, category):
        return list(DIGITAL_FRAUD_EVIDENCE)
    if _is_it_outsourcing_context(lower, risk_keywords, category):
        return list(IT_OUTSOURCING_EVIDENCE)

    evidence = []
    for evidence_item, terms in EVIDENCE_RULES:
        if any(term in lower for term in terms):
            evidence.append(evidence_item)
    if not evidence:
        evidence.append("Owner sign-off note, implementation evidence, and compliance review record")
    return _dedupe(evidence)


def _build_summary(title, category, obligations, departments, deadline):
    obligation_count = len(obligations)
    department_text = ", ".join(departments[:3]) if departments else "Compliance Office"
    deadline_text = deadline or "deadline not explicitly stated"
    return (
        f"{title} is classified as {category}. Scout extracted "
        f"{obligation_count} obligation(s), mapped ownership to {department_text}, "
        f"and detected {deadline_text}."
    )


def _source_overlap_count(value, source_text):
    source_lower = (source_text or "").lower()
    tokens = {
        token
        for token in re.findall(r"[a-z0-9-]{4,}", (value or "").lower())
        if token not in LLM_STOPWORDS
    }
    return sum(1 for token in tokens if token in source_lower)


def _coerce_llm_text(value):
    if isinstance(value, dict):
        for key in ("obligation", "requirement", "text", "summary", "description"):
            if value.get(key):
                return str(value.get(key))
        return ""
    return str(value or "")


def _sanitize_llm_obligations(raw_obligations, source_text):
    if not isinstance(raw_obligations, list):
        return []

    obligations = []
    for raw_item in raw_obligations[:20]:
        cleaned = _normalize_obligation(_coerce_llm_text(raw_item))
        if not cleaned or _is_metadata_line(cleaned):
            continue
        if _is_incomplete_obligation(cleaned):
            continue
        if not _has_obligation_phrase(cleaned):
            continue
        if _source_overlap_count(cleaned, source_text) < 2:
            continue
        obligations.append(cleaned)
    return _dedupe(obligations)[:12]


def _sanitize_llm_list(raw_items, source_text=None, max_items=8):
    if isinstance(raw_items, str):
        items = re.split(r"[,;\n]+", raw_items)
    elif isinstance(raw_items, list):
        items = raw_items
    else:
        return []

    sanitized = []
    for raw_item in items[:20]:
        text = _normalize_space(_coerce_llm_text(raw_item)).strip(" .;:-")
        if not text or len(text) > 100 or any(char in text for char in "{}[]"):
            continue
        if source_text and _source_overlap_count(text, source_text) == 0:
            continue
        sanitized.append(text)
    return _dedupe(sanitized)[:max_items]


def _sanitize_llm_summary(summary, source_text):
    text = _normalize_space(summary)
    if len(text) < 40 or len(text) > 700:
        return ""
    if _source_overlap_count(text, source_text) < 3:
        return ""
    return text


def _try_local_llm_extract(cleaned_text, engine_notes):
    mode = get_llm_mode()
    if mode == "rules":
        engine_notes.append("Local LLM extraction skipped because COMPLIANCE_LLM_MODE=rules.")
        return {}
    if not is_llm_enabled() or extract_circular_fields is None:
        engine_notes.append("Local LLM extraction adapter unavailable; deterministic Scout fallback used.")
        return {}

    payload = extract_circular_fields(cleaned_text)
    if not isinstance(payload, dict):
        engine_notes.append(
            f"Local LLM extraction unavailable in {mode} mode for model {get_ollama_model()}; deterministic Scout fallback used."
        )
        return {}

    obligations = _sanitize_llm_obligations(payload.get("key_obligations"), cleaned_text)
    if not obligations:
        engine_notes.append("Local LLM extraction returned weak or malformed obligations; deterministic Scout fallback used.")
        return {}

    deadlines = _sanitize_llm_list(payload.get("deadlines"), source_text=cleaned_text, max_items=8)
    departments = _sanitize_llm_list(payload.get("impacted_departments"), max_items=8)
    domain = _normalize_space(payload.get("domain"))
    summary = _sanitize_llm_summary(payload.get("summary"), cleaned_text)

    engine_notes.append(
        f"Local LLM extraction accepted from Ollama model {get_ollama_model()} with deterministic validation."
    )
    return {
        "summary": summary,
        "obligations": obligations,
        "deadlines": deadlines,
        "domain": domain[:140],
        "departments": departments,
    }


def scan_circulars():
    circulars = []

    if not CIRCULARS_DIR.exists():
        return circulars

    for file in CIRCULARS_DIR.glob("*.txt"):
        circulars.append(
            {
                "id": file.stem,
                "path": str(file),
                "ingested_at": file.stat().st_mtime,
            }
        )

    return circulars


def get_circular_by_id(circular_id):
    file_path = CIRCULARS_DIR / f"{circular_id}.txt"

    if not file_path.exists():
        return None

    return {
        "id": circular_id,
        "content": file_path.read_text(encoding="utf-8"),
    }


def parse_circular_text(circular_text=None, file_name=None):
    text = _normalize_pdf_text(circular_text or "")
    cleaned_text = _normalize_space(text)
    engine_notes = ["Scout Parser used local extraction with deterministic offline fallback."]

    if not cleaned_text or len(cleaned_text) < 20:
        engine_notes.append("Input circular text was empty or too short; safe fallback metadata returned.")
        fallback_title = Path(file_name or "uploaded circular").stem.replace("_", " ").title()
        fallback_advisories = match_department_advisory(
            cleaned_text,
            obligations=[],
            risk_keywords=[],
            category="General Regulatory Compliance",
            limit=1,
        )
        return {
            "title": fallback_title,
            "circular_id": _extract_circular_id(cleaned_text, file_name),
            "category": "General Regulatory Compliance",
            "issue_date": None,
            "effective_date": None,
            "deadline": None,
            "deadlines": [],
            "obligations": [],
            "risk_keywords": [],
            "evidence_required": ["Manual compliance review record"],
            "affected_departments": ["Compliance Office"],
            "mapped_advisories": fallback_advisories,
            "normalized_summary": "Circular text was empty or too short for reliable extraction.",
            "raw_text_excerpt": cleaned_text[:500],
            "engine_notes": engine_notes,
        }

    llm_extract = _try_local_llm_extract(cleaned_text, engine_notes)
    deterministic_obligations = extract_obligations(text)
    obligations = deterministic_obligations
    if llm_extract.get("obligations"):
        obligations = _dedupe(llm_extract["obligations"] + deterministic_obligations)[:16]

    deadlines = _dedupe((llm_extract.get("deadlines") or []) + _extract_deadlines(cleaned_text))
    risk_keywords = _detect_risk_keywords(cleaned_text)
    category = _detect_category(cleaned_text, risk_keywords)
    if (
        category == "General Regulatory Compliance"
        and llm_extract.get("domain")
        and not _is_pso_payment_context(cleaned_text, risk_keywords)
    ):
        category = llm_extract["domain"]
    departments = _detect_departments(cleaned_text, obligations)
    if llm_extract.get("departments") and not _is_pso_payment_context(cleaned_text, risk_keywords, category):
        departments = _dedupe(llm_extract["departments"] + departments)[:8]
    evidence = _detect_evidence(cleaned_text, obligations, risk_keywords, category)
    title = _extract_title(text, file_name)
    primary_deadline = deadlines[0] if deadlines else None
    mapped_advisories = match_department_advisory(
        cleaned_text,
        obligations=obligations,
        risk_keywords=risk_keywords,
        category=category,
        limit=5,
    )
    mapped_departments = [
        f"{advisory['business_vertical']} / {advisory['sub_vertical']}"
        for advisory in mapped_advisories
        if advisory.get("match_score", 0) > 1
    ]
    affected_departments = departments if _is_pso_payment_context(cleaned_text, risk_keywords, category) else (mapped_departments or departments)

    if not obligations:
        engine_notes.append("No explicit obligation phrase was found; downstream agents should use manual-review fallback.")

    return {
        "title": title,
        "circular_id": _extract_circular_id(text, file_name),
        "category": category,
        "issue_date": _extract_issue_date(text),
        "effective_date": _extract_effective_date(text, deadlines),
        "deadline": primary_deadline,
        "deadlines": deadlines,
        "obligations": obligations,
        "risk_keywords": risk_keywords,
        "evidence_required": evidence,
        "affected_departments": affected_departments,
        "mapped_advisories": mapped_advisories,
        "normalized_summary": llm_extract.get("summary")
        or _build_summary(title, category, obligations, affected_departments, primary_deadline),
        "raw_text_excerpt": cleaned_text[:500],
        "engine_notes": engine_notes,
    }
