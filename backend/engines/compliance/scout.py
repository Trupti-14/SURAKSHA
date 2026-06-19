import hashlib
import re
from datetime import datetime
from pathlib import Path


CIRCULARS_DIR = Path(__file__).resolve().parents[2] / "data" / "circulars"

OBLIGATION_PHRASES = (
    "must",
    "shall",
    "required to",
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
    ("Digital Fraud Reporting", ("digital fraud", "payment fraud", "fraud reporting")),
    ("Mule Account Monitoring", ("mule account", "mule", "suspicious account")),
    ("KYC / AML Compliance", ("kyc", "aml", "suspicious transaction", "dormant")),
    ("Cyber Incident Compliance", ("cyber incident", "cybersecurity", "security log")),
    ("Customer Protection", ("customer protection", "customer notification", "grievance")),
    ("Evidence Retention and Audit", ("audit", "evidence", "retain", "preserve")),
    ("Data Privacy / DPDP", ("dpdp", "data privacy", "personal data")),
    ("Regulatory Reporting", ("report", "submit", "rbi", "submission")),
)

DEPARTMENT_RULES = (
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
    ("Fraud incident register with detection timestamp, reporting timestamp, customer impact, and evidence reference", ("fraud", "digital fraud", "payment fraud")),
    ("Customer notification proof, notification timestamp, and exception log", ("notify", "customer notification", "affected customer", "grievance")),
    ("Evidence archive inventory, retention configuration, and audit trail export", ("retain", "preserve", "evidence", "audit trail", "archive")),
    ("Monthly monitoring report, maker-checker approval, and submission proof", ("monthly", "report", "submit")),
    ("Branch escalation register with owner sign-off and closure timestamp", ("branch", "escalate", "branch-level")),
    ("KYC verification tracker, exception approvals, and customer communication proof", ("kyc", "aml", "verification", "suspicious transaction")),
    ("Security log export, incident ticket, and digital evidence hash", ("cyber", "security log", "incident", "digital evidence")),
    ("Regulatory submission acknowledgement and Compliance Office sign-off", ("rbi", "regulatory", "compliance office")),
)


def _normalize_space(value):
    return re.sub(r"\s+", " ", value or "").strip()


def _clean_line(line):
    return re.sub(r"^\s*[-*0-9.)]+\s*", "", line or "").strip()


def _dedupe(items):
    deduped = []
    seen = set()
    for item in items:
        normalized = _normalize_space(str(item))
        key = normalized.lower()
        if normalized and key not in seen:
            deduped.append(normalized)
            seen.add(key)
    return deduped


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
        if lower.startswith("subject:"):
            return _normalize_space(cleaned.split(":", 1)[1])
        if "circular" not in lower and len(cleaned) >= 12:
            return cleaned[:140]
    return Path(file_name or "uploaded circular").stem.replace("_", " ").title()


def _extract_circular_id(text, file_name):
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
    effective_match = re.search(r"effective\s+(?:from|date)?\s*[:\-]?\s*([A-Za-z0-9 ,/-]+)", text, flags=re.I)
    if effective_match:
        return _normalize_space(effective_match.group(1))
    if any("immediate effect" in deadline.lower() for deadline in deadlines):
        return "with immediate effect"
    return None


def _split_obligation_clauses(sentence):
    prepared = re.sub(
        r"\s+and\s+(?=(?:notify|retain|submit|maintain|monitor|escalate|reconcile|verify|preserve|disclose|review|update|implement)\b)",
        ", ",
        sentence,
        flags=re.I,
    )
    split_pattern = (
        r",\s+(?=(?:and\s+)?(?:notify|retain|submit|maintain|monitor|escalate|"
        r"reconcile|verify|preserve|disclose|review|update|implement|report)\b)"
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


def extract_obligations(text):
    obligations = []
    candidates = []
    for line in text.splitlines():
        cleaned = _clean_line(line)
        if cleaned:
            candidates.extend(re.split(r"(?<=[.!?])\s+", cleaned))

    if not candidates:
        candidates = re.split(r"(?<=[.!?])\s+", text)

    for sentence in candidates:
        for clause in _split_obligation_clauses(sentence):
            if len(clause) < 8:
                continue
            if _has_obligation_phrase(clause):
                obligations.append(_normalize_obligation(clause))

    return _dedupe(obligations)[:12]


def _detect_risk_keywords(text):
    lower = text.lower()
    found = []
    for label, terms in RISK_RULES:
        if any(term in lower for term in terms):
            found.append(label)
    return _dedupe(found)


def _detect_category(text, risk_keywords):
    lower = text.lower()
    for category, terms in CATEGORY_RULES:
        if any(term in lower for term in terms):
            return category
    if risk_keywords:
        return risk_keywords[0].title()
    return "General Regulatory Compliance"


def _detect_departments(text, obligations):
    lower = f"{text} {' '.join(obligations)}".lower()
    departments = []
    for department, terms in DEPARTMENT_RULES:
        if any(term in lower for term in terms):
            departments.append(department)
    if not departments:
        departments.append("Compliance Office")
    return _dedupe(departments)


def _detect_evidence(text, obligations):
    lower = f"{text} {' '.join(obligations)}".lower()
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
    text = circular_text or ""
    cleaned_text = _normalize_space(text)
    engine_notes = ["Scout Parser used deterministic offline extraction."]

    if not cleaned_text or len(cleaned_text) < 20:
        engine_notes.append("Input circular text was empty or too short; safe fallback metadata returned.")
        fallback_title = Path(file_name or "uploaded circular").stem.replace("_", " ").title()
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
            "normalized_summary": "Circular text was empty or too short for reliable extraction.",
            "raw_text_excerpt": cleaned_text[:500],
            "engine_notes": engine_notes,
        }

    deadlines = _extract_deadlines(cleaned_text)
    obligations = extract_obligations(cleaned_text)
    risk_keywords = _detect_risk_keywords(cleaned_text)
    category = _detect_category(cleaned_text, risk_keywords)
    departments = _detect_departments(cleaned_text, obligations)
    evidence = _detect_evidence(cleaned_text, obligations)
    title = _extract_title(text, file_name)
    primary_deadline = deadlines[0] if deadlines else None

    if not obligations:
        engine_notes.append("No explicit obligation phrase was found; downstream agents should use manual-review fallback.")

    return {
        "title": title,
        "circular_id": _extract_circular_id(cleaned_text, file_name),
        "category": category,
        "issue_date": _extract_issue_date(text),
        "effective_date": _extract_effective_date(cleaned_text, deadlines),
        "deadline": primary_deadline,
        "deadlines": deadlines,
        "obligations": obligations,
        "risk_keywords": risk_keywords,
        "evidence_required": evidence,
        "affected_departments": departments,
        "normalized_summary": _build_summary(title, category, obligations, departments, primary_deadline),
        "raw_text_excerpt": cleaned_text[:500],
        "engine_notes": engine_notes,
    }
