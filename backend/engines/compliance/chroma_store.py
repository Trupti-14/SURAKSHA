import json
import math
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from .embeddings import embed_text

try:
    import chromadb
except Exception:
    chromadb = None


BACKEND_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BACKEND_DIR / "data"
CHROMA_DIR = DATA_DIR / "chroma_db"
CIRCULARS_DIR = DATA_DIR / "circulars"
COMPLIANCE_DIR = DATA_DIR / "compliance"
FALLBACK_MEMORY_PATH = COMPLIANCE_DIR / "regulatory_memory.json"
COLLECTION_NAME = "rbi_regulatory_memory"
EMBEDDING_DIMENSIONS = 128

_client = None
_collection = None
_client_mode = None
_last_chroma_error = None

CONTROL_VERBS = (
    "shall",
    "must",
    "should",
    "ensure",
    "maintain",
    "submit",
    "report",
    "notify",
    "retain",
    "monitor",
    "review",
    "audit",
    "escalate",
    "test",
    "approve",
    "control",
    "policy",
    "framework",
    "risk",
    "incident",
    "access",
    "logs",
    "bcp",
    "dr",
    "ciso",
    "soc",
)

ACTION_VERBS = (
    "shall",
    "must",
    "should",
    "ensure",
    "maintain",
    "submit",
    "report",
    "notify",
    "retain",
    "monitor",
    "review",
    "audit",
    "escalate",
    "test",
    "approve",
)

NOISY_SECTION_HEADINGS = (
    "acronyms",
    "abbreviations",
    "table of contents",
    "contents",
    "list of circulars",
    "repealed circular",
    "repealed circulars",
    "superseded circular",
    "superseded circulars",
    "withdrawn circular",
    "circular reference",
)

NOISY_LINE_PHRASES = (
    "circular reference date subject remarks",
    "reference date subject remarks",
    "date subject remarks",
    "table of contents",
    "master circulars repealed",
    "list of repealed circulars",
    "hindi is easy",
    "hindi is very easy",
)

HEADER_FOOTER_PHRASES = (
    "reserve bank of india",
    "central office",
    "department of regulation",
    "department of supervision",
    "shahid bhagat singh",
    "mumbai",
    "rbi.org.in",
    "@rbi.org.in",
    "email",
    "e-mail",
    "telephone",
    "phone",
    "fax",
)

TITLE_SUBJECT_PATTERNS = (
    r"\bmaster direction\b[^\n]*",
    r"\bmaster circular\b[^\n]*",
    r"\bdraft master direction\b.*",
    r"\bsubject\s*[:\-]\s*(.+)",
    r"\btitle\s*[:\-]\s*(.+)",
)

TITLE_KEYWORDS = (
    "master direction",
    "master circular",
    "directions",
    "framework",
    "requirement for",
    "requirements for",
    "inclusion of",
    "information technology governance",
    "risk, controls",
    "financial information provider",
    "account aggregator",
    "payment activity",
    "cyber security",
    "outsourcing",
)

GENERIC_TITLE_VALUES = {
    "reference",
    "policy reference",
    "approved policy reference",
    "circular",
    "rbi circular",
    "rbi reference",
    "reference circular",
    "uploaded reference",
    "uploaded circular",
    "document",
    "pdf",
    "untitled",
}

METADATA_LINE_KEYS = {
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

VALID_REFERENCE_DOMAINS = {
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

DOMAIN_KEYWORDS = (
    (
        "audit_governance",
        (
            "it governance",
            "information technology governance",
            "ciso",
            "soc",
            "audit trail",
            "audit trails",
            "va/pt",
            "vapt",
            "cyber security policy",
            "information security policy",
            "bcp",
            "business continuity",
            "dr",
            "disaster recovery",
            "is audit",
            "controls and assurance",
            "risk controls and assurance",
            "assurance practices",
        ),
    ),
    (
        "cyber_incident",
        (
            "cert-in",
            "cyber incident",
            "incident response",
            "security logs",
            "containment",
            "root cause",
            "soc escalation",
            "incident reporting",
        ),
    ),
    (
        "digital_fraud",
        (
            "digital fraud",
            "customer notification",
            "mule account",
            "fraud monitoring report",
            "payment fraud",
            "fraud reporting",
            "transaction logs",
        ),
    ),
    (
        "kyc_aml",
        (
            "kyc",
            "aml",
            "beneficial owner",
            "suspicious account",
            "suspicious transaction",
            "mule account",
        ),
    ),
    (
        "it_outsourcing",
        (
            "outsourcing",
            "vendor",
            "third party",
            "third-party",
            "cloud",
            "service provider",
            "subcontractor",
        ),
    ),
    (
        "digital_payment",
        (
            "payment system",
            "pso",
            "upi",
            "ppi",
            "payment aggregator",
            "payment gateway",
            "settlement",
            "clearing corporation",
            "ccil",
            "financial information provider",
            "account aggregator",
        ),
    ),
    (
        "mobile_banking",
        (
            "mobile banking",
            "mobile app",
            "device binding",
        ),
    ),
    (
        "digital_lending",
        (
            "digital lending",
            "lending service provider",
            "loan app",
            "lsp",
        ),
    ),
    (
        "bcp_drp",
        (
            "business continuity",
            "disaster recovery",
            "rto",
            "rpo",
            "dr drill",
            "bcp",
            "drp",
        ),
    ),
)

DOMAIN_CATEGORIES = {
    "audit_governance": "IT Governance / Risk / Controls / Assurance",
    "cyber_incident": "Cyber Incident Response / CERT-In / SOC Escalation",
    "digital_fraud": "Digital Fraud / Customer Notification / Monitoring",
    "kyc_aml": "KYC / AML / Suspicious Account Monitoring",
    "it_outsourcing": "IT Outsourcing / Vendor Risk / Third-Party Controls",
    "digital_payment": "Payment System Operator / RBI Approval / Payment Activity Transfer",
    "mobile_banking": "Mobile Banking / App Security / Device Controls",
    "digital_lending": "Digital Lending / LSP / Loan App Controls",
    "bcp_drp": "Business Continuity / Disaster Recovery / Resilience Testing",
    "general_compliance": "Regulatory Compliance",
}


def _utc_now():
    return datetime.utcnow().isoformat()


def _ensure_dirs():
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    COMPLIANCE_DIR.mkdir(parents=True, exist_ok=True)


def _safe_metadata(metadata: dict[str, Any] | None) -> dict[str, str | int | float | bool]:
    safe = {}
    for key, value in (metadata or {}).items():
        if value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            safe[key] = value
        else:
            safe[key] = json.dumps(value, ensure_ascii=True, sort_keys=True)
    return safe


def _content_excerpt(content: str, limit: int = 220) -> str:
    text = " ".join((content or "").split())
    return text[:limit]


def _is_user_reference_id(circular_id: str | None) -> bool:
    return bool(circular_id and str(circular_id).startswith("USER-REF-"))


def _has_withdrawn_marker(text: str) -> bool:
    return bool(re.search(r"\b(withdrawn|repealed|superseded|archived)\b", text or "", flags=re.I))


def source_status_for_text(text: str) -> str:
    return "Withdrawn / archived" if _has_withdrawn_marker(text) else ""


def _looks_like_metadata_line(line: str) -> bool:
    if ":" not in (line or ""):
        return False
    key = line.split(":", 1)[0].strip().lower()
    return key in METADATA_LINE_KEYS


def _looks_like_subject_line(line: str) -> bool:
    return bool(re.match(r"^\s*(?:subject|title)\s*[:\-]", line or "", flags=re.I))


def _looks_like_salutation_line(line: str) -> bool:
    return bool(re.match(r"^\s*(?:madam|dear sir|sir|madam\s*/\s*dear sir)\s*,?\s*$", line or "", flags=re.I))


def _has_control_verb(line: str) -> bool:
    lower = (line or "").lower()
    return any(re.search(rf"\b{re.escape(verb)}\b", lower) for verb in CONTROL_VERBS)


def _has_action_verb(line: str) -> bool:
    lower = (line or "").lower()
    return any(re.search(rf"\b{re.escape(verb)}\b", lower) for verb in ACTION_VERBS)


def _looks_like_page_number(line: str) -> bool:
    text = (line or "").strip()
    return bool(
        re.match(r"^(?:page\s*)?\d{1,4}(?:\s*(?:of|/)\s*\d{1,4})?$", text, flags=re.I)
        or re.match(r"^[-–—]\s*\d{1,4}\s*[-–—]$", text)
    )


def _mostly_abbreviations(line: str) -> bool:
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9&/-]*", line or "")
    if len(tokens) < 3:
        return False
    abbreviation_count = sum(
        1
        for token in tokens
        if (
            token.upper() == token
            and len(re.sub(r"[^A-Z]", "", token)) >= 2
            and not token.isdigit()
        )
    )
    natural_word_count = sum(1 for token in tokens if token.lower() == token and len(token) >= 4)
    return abbreviation_count / max(1, len(tokens)) >= 0.65 and natural_word_count < 3


def _looks_like_toc_line(line: str) -> bool:
    text = (line or "").strip()
    return bool(re.search(r"\.{3,}\s*\d{1,4}$", text) or re.match(r"^\d+(?:\.\d+)*\s+\S+.*\s+\d{1,4}$", text))


def _looks_like_broken_header(line: str) -> bool:
    text = line or ""
    lower = text.lower()
    if "�" in text or "â" in text:
        return not _has_control_verb(text)
    non_ascii_count = sum(1 for char in text if ord(char) > 127)
    return non_ascii_count >= max(6, len(text) // 3) and not _has_control_verb(text)


def _looks_like_rbi_header_footer(line: str) -> bool:
    lower = (line or "").lower()
    if not any(phrase in lower for phrase in HEADER_FOOTER_PHRASES):
        return False
    return len(line or "") <= 180 and not _has_control_verb(line)


def _looks_like_reference_table_row(line: str) -> bool:
    lower = (line or "").lower()
    if _has_control_verb(line):
        return False
    date_count = len(re.findall(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}\b", line or ""))
    reference_markers = sum(
        marker in lower
        for marker in (
            "circular",
            "notification",
            "master direction",
            "reference",
            "remarks",
            "repealed",
            "superseded",
            "withdrawn",
        )
    )
    column_like_spaces = bool(re.search(r"\S+\s{2,}\S+\s{2,}\S+", line or ""))
    slashed_reference = bool(re.search(r"\b[A-Z]{2,}(?:/[A-Z0-9.-]+){2,}\b", line or ""))
    return (date_count >= 2 and reference_markers >= 1) or (
        reference_markers >= 2 and (column_like_spaces or slashed_reference)
    )


def _is_noisy_reference_line(line: str) -> bool:
    normalized = " ".join((line or "").split())
    lower = normalized.lower()
    if not normalized:
        return False
    if _looks_like_metadata_line(normalized):
        return True
    if _looks_like_salutation_line(normalized):
        return True
    if _looks_like_subject_line(normalized):
        return True
    if any(phrase in lower for phrase in NOISY_LINE_PHRASES):
        return True
    if _looks_like_broken_header(normalized):
        return True
    if _looks_like_rbi_header_footer(normalized):
        return True
    if _looks_like_toc_line(normalized):
        return True
    if _looks_like_page_number(normalized):
        return True
    if _mostly_abbreviations(normalized):
        return True
    if _looks_like_reference_table_row(normalized):
        return True
    if len(normalized) <= 4 and normalized.upper() == normalized and not _has_control_verb(normalized):
        return True
    return False


def _starts_noisy_section(line: str) -> bool:
    lower = (line or "").strip(" :-").lower()
    if lower in NOISY_SECTION_HEADINGS:
        return True
    if re.match(r"^(annex|annexure|appendix)\b", lower):
        return any(term in lower for term in ("circular", "reference", "repeal", "acronym", "abbreviation", "historical"))
    return False


def clean_reference_text(text: str) -> str:
    """
    Remove PDF extraction noise from uploaded reference circulars while keeping
    policy/control paragraphs available for comparison.
    """
    if not text:
        return ""

    normalized_text = (
        str(text)
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\u00a0", " ")
    )
    raw_lines = [re.sub(r"\s+", " ", line).strip() for line in normalized_text.splitlines()]
    line_counts = {}
    for line in raw_lines:
        if line:
            line_counts[line.lower()] = line_counts.get(line.lower(), 0) + 1

    cleaned_lines = []
    skip_noise_section = False

    for line in raw_lines:
        lower = line.lower()

        if not line:
            skip_noise_section = False
            if cleaned_lines and cleaned_lines[-1] != "":
                cleaned_lines.append("")
            continue

        if skip_noise_section:
            if _has_control_verb(line) and len(line) >= 60:
                skip_noise_section = False
            else:
                continue

        if _starts_noisy_section(line):
            skip_noise_section = True
            continue

        if any(phrase in lower for phrase in NOISY_LINE_PHRASES):
            skip_noise_section = True
            continue

        if line_counts.get(lower, 0) >= 3 and len(line) <= 120 and not _has_control_verb(line):
            continue

        if _is_noisy_reference_line(line):
            continue

        cleaned_lines.append(line)

    cleaned = "\n".join(cleaned_lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned


def _is_hash_like_title(title: str | None) -> bool:
    text = (title or "").strip()
    if not text:
        return True
    lower = text.lower()
    if any(keyword in lower for keyword in TITLE_KEYWORDS):
        return False
    if text.startswith("USER-REF-"):
        return True
    compact = re.sub(r"[^A-Za-z0-9]", "", text)
    if len(compact) >= 24:
        tokens = re.findall(r"[A-Za-z][A-Za-z0-9]*", text)
        natural_words = sum(1 for token in tokens if token.isalpha() and token.lower() == token and len(token) >= 4)
        digit_ratio = sum(char.isdigit() for char in compact) / max(1, len(compact))
        upper_ratio = sum(char.isupper() for char in compact) / max(1, len(compact))
        has_long_hash_token = any(
            len(token) >= 20 and any(char.isdigit() for char in token)
            for token in re.findall(r"[A-Za-z0-9]+", text)
        )
        return has_long_hash_token or (
            natural_words < 3 and (digit_ratio >= 0.12 or upper_ratio >= 0.72)
        )
    return False


def _is_generic_title(title: str | None) -> bool:
    text = re.sub(r"\.[A-Za-z0-9]{2,5}$", "", (title or "").strip())
    normalized = re.sub(r"[_\-]+", " ", text)
    normalized = re.sub(r"\s+", " ", normalized).strip(" .:-").lower()
    if not normalized:
        return True
    if normalized in GENERIC_TITLE_VALUES:
        return True
    if normalized.startswith("rbi circular") and len(normalized) <= 35:
        return True
    if normalized.startswith("rbi reference") and len(normalized) <= 35:
        return True
    return False


def _readable_user_title(title: str | None) -> bool:
    text = (title or "").strip()
    if not text or _is_hash_like_title(text) or _is_generic_title(text):
        return False
    return bool(re.search(r"[A-Za-z]", text))


def _title_from_line(line: str) -> str:
    title = re.sub(r"^\s*(?:subject|title)\s*[:\-]\s*", "", line or "", flags=re.I)
    title = re.sub(r"^\s*(?:madam|dear sir|madam\s*/\s*dear sir)\s*,?\s*", "", title, flags=re.I)
    title = re.sub(r"\s+", " ", title).strip(" :-")
    return title[:180]


def _title_candidate_score(candidate: str) -> int:
    cleaned = _title_from_line(candidate)
    lower = cleaned.lower()
    if (
        len(cleaned) < 12
        or _is_hash_like_title(cleaned)
        or _is_generic_title(cleaned)
        or _is_noisy_reference_line(cleaned)
    ):
        return 0

    score = 0
    for index, keyword in enumerate(TITLE_KEYWORDS):
        if keyword in lower:
            score += 40 - min(index, 20)
    if re.search(r"\b(master|framework|directions?|requirement|inclusion)\b", lower):
        score += 15
    if len(cleaned.split()) >= 5:
        score += 8
    if _has_control_verb(cleaned):
        score -= 10
    if len(cleaned) > 220:
        score -= 20
    return score


def _title_candidates_from_lines(content: str) -> list[str]:
    raw_lines = [re.sub(r"\s+", " ", line).strip() for line in (content or "").splitlines()]
    lines = [line for line in raw_lines if line]
    candidates = []

    def continuation(line: str) -> bool:
        lower = (line or "").lower()
        if not line or _has_control_verb(line) or _is_noisy_reference_line(line):
            return False
        if lower.startswith(("the reserve bank", "please refer", "in exercise", "all regulated entities")):
            return False
        return len(line) <= 120 and not line.endswith(".")

    for index, line in enumerate(lines):
        lower = line.lower()
        if "madam" in lower or "dear sir" in lower:
            for candidate_index in range(index + 1, min(index + 8, len(lines))):
                candidate = lines[candidate_index]
                candidates.append(candidate)
                if any(keyword in candidate.lower() for keyword in TITLE_KEYWORDS):
                    joined_lines = [candidate]
                    for follow in lines[candidate_index + 1 : candidate_index + 3]:
                        if continuation(follow):
                            joined_lines.append(follow)
                        else:
                            break
                    candidates.append(" ".join(joined_lines))

    for index, line in enumerate(lines):
        lowered = line.lower()
        if _looks_like_subject_line(line) or any(keyword in lowered for keyword in TITLE_KEYWORDS):
            candidates.append(line)
            if index + 1 < len(lines) and continuation(lines[index + 1]):
                candidates.append(f"{line} {lines[index + 1]}")

    return candidates


def _filename_title(file_name: str | None) -> str:
    if not file_name:
        return ""
    stem = Path(str(file_name)).stem
    title = re.sub(r"[_\-]+", " ", stem)
    title = re.sub(r"\s+", " ", title).strip()
    return title


def derive_reference_title(
    content: str,
    uploaded_file_name: str | None = None,
    user_title: str | None = None,
    fallback: str = "Approved Policy Reference",
) -> str:
    if _readable_user_title(user_title):
        return str(user_title).strip()

    scored_candidates = []

    for pattern in TITLE_SUBJECT_PATTERNS:
        match = re.search(pattern, content or "", flags=re.I)
        if match:
            candidate = match.group(1) if match.lastindex else match.group(0)
            candidate = _title_from_line(candidate)
            score = _title_candidate_score(candidate)
            if score:
                scored_candidates.append((score + 10, candidate))

    for candidate in _title_candidates_from_lines(content or ""):
        cleaned = _title_from_line(candidate)
        score = _title_candidate_score(cleaned)
        if score:
            scored_candidates.append((score, cleaned))

    if scored_candidates:
        scored_candidates.sort(key=lambda item: (item[0], len(item[1])), reverse=True)
        return scored_candidates[0][1]

    for line in (content or "").splitlines():
        cleaned = _title_from_line(line)
        lower = cleaned.lower()
        if (
            len(cleaned) >= 24
            and not _is_noisy_reference_line(cleaned)
            and not _is_hash_like_title(cleaned)
            and not _is_generic_title(cleaned)
            and any(term in lower for term in ("master direction", "master circular", "framework", "governance", "policy", "risk", "controls", "inclusion of"))
        ):
            return cleaned

    file_title = _filename_title(uploaded_file_name)
    if _readable_user_title(file_title):
        return file_title

    return fallback


def _readable_title(title: str | None, content: str, circular_id: str | None = None) -> str:
    if _readable_user_title(title):
        return title.strip()
    fallback = "Approved Policy Reference"
    if circular_id and not _is_hash_like_title(circular_id):
        fallback = str(circular_id)
    return derive_reference_title(content, user_title=title, fallback=fallback)


def infer_reference_domain(clean_text: str, user_domain: str | None = None) -> str:
    selected = (user_domain or "").strip()
    if selected in VALID_REFERENCE_DOMAINS and selected != "general_compliance":
        return selected

    lower = (clean_text or "").lower()
    scored = []
    for order, (domain, keywords) in enumerate(DOMAIN_KEYWORDS):
        score = sum(1 for keyword in keywords if keyword in lower)
        if score:
            scored.append((score, -order, domain))

    if not scored:
        return "general_compliance"

    scored.sort(reverse=True)
    return scored[0][2]


def _readable_category(category: str | None) -> bool:
    text = (category or "").strip()
    if not text:
        return False
    if _is_hash_like_title(text) or _is_generic_title(text):
        return False
    return len(text) >= 4 and bool(re.search(r"[A-Za-z]", text))


def infer_reference_category(clean_text: str, domain: str, user_category: str | None = None) -> str:
    if _readable_category(user_category):
        return str(user_category).strip()

    lower = (clean_text or "").lower()
    if domain == "digital_payment" and any(
        term in lower for term in ("account aggregator", "financial information provider", "clearing corporation", "ccil")
    ):
        return "Account Aggregator / Financial Information Provider / RBI Approval"
    return DOMAIN_CATEGORIES.get(domain, DOMAIN_CATEGORIES["general_compliance"])


def _useful_display_line(line: str) -> bool:
    text = (line or "").strip()
    if len(text) < 25:
        return False
    lower = text.lower()
    if _looks_like_subject_line(text) or _looks_like_salutation_line(text):
        return False
    if any(keyword in lower for keyword in TITLE_KEYWORDS) and not _has_action_verb(text):
        return False
    if _is_noisy_reference_line(text):
        return False
    return _has_control_verb(text) or len(text) >= 80


def _display_block_text(block: str) -> str:
    selected_lines = []
    started_policy_text = False

    for line in block.splitlines():
        line = line.strip()
        lower = line.lower()
        if not line or _looks_like_subject_line(line) or _looks_like_salutation_line(line):
            continue
        if any(keyword in lower for keyword in TITLE_KEYWORDS) and not _has_action_verb(line):
            continue
        if not started_policy_text:
            if _has_action_verb(line) or (len(line) >= 80 and not _is_noisy_reference_line(line)):
                started_policy_text = True
            else:
                continue
        if not _is_noisy_reference_line(line):
            selected_lines.append(line)

    return re.sub(r"\s+", " ", " ".join(selected_lines)).strip()


def display_reference_text(content: str, limit: int = 2200) -> str:
    cleaned = clean_reference_text(content or "")
    if not cleaned:
        return ""

    display_lines = []
    for block in re.split(r"\n\s*\n+", cleaned):
        block = _display_block_text(block)
        if _useful_display_line(block):
            display_lines.append(block)
        if len("\n\n".join(display_lines)) >= limit:
            break

    if not display_lines:
        for line in cleaned.splitlines():
            line = line.strip()
            if _useful_display_line(line):
                display_lines.append(line)
            if len("\n\n".join(display_lines)) >= limit:
                break

    if not display_lines:
        display_lines = [cleaned[:limit].strip()]

    return "\n\n".join(display_lines)[:limit].strip()


def _read_fallback_memory() -> list[dict[str, Any]]:
    _ensure_dirs()
    if not FALLBACK_MEMORY_PATH.exists():
        return []

    try:
        payload = json.loads(FALLBACK_MEMORY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    if isinstance(payload, dict):
        records = payload.get("items") or []
    elif isinstance(payload, list):
        records = payload
    else:
        records = []

    return [record for record in records if isinstance(record, dict)]


def _write_fallback_memory(records: list[dict[str, Any]]) -> None:
    _ensure_dirs()
    payload = {
        "offline_mode": True,
        "updated_at": "local_seed",
        "count": len(records),
        "items": records,
    }
    FALLBACK_MEMORY_PATH.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )


def _upsert_fallback_record(record: dict[str, Any]) -> None:
    records = _read_fallback_memory()
    circular_id = record["circular_id"]
    updated = False

    for index, existing in enumerate(records):
        if existing.get("circular_id") == circular_id:
            records[index] = record
            updated = True
            break

    if not updated:
        records.append(record)

    records.sort(key=lambda item: item.get("circular_id", ""))
    _write_fallback_memory(records)


def _delete_fallback_record(circular_id: str) -> bool:
    records = _read_fallback_memory()
    remaining = [
        record
        for record in records
        if (record.get("circular_id") or (record.get("metadata") or {}).get("circular_id")) != circular_id
    ]
    if len(remaining) == len(records):
        return False
    _write_fallback_memory(remaining)
    return True


def _fallback_record(circular_id: str, content: str, metadata: dict[str, Any] | None) -> dict[str, Any]:
    metadata = metadata or {}
    title = metadata.get("title") or metadata.get("file_name") or circular_id
    category = metadata.get("category") or "Regulatory Compliance"
    display_text = display_reference_text(content)
    withdrawn = bool(metadata.get("withdrawn")) or _has_withdrawn_marker(content)
    source_status = metadata.get("source_status") or source_status_for_text(content)
    return {
        "circular_id": circular_id,
        "title": title,
        "category": category,
        "content": content or "",
        "content_excerpt": _content_excerpt(display_text or content),
        "preview_text": display_text,
        "display_text": display_text,
        "withdrawn": withdrawn,
        "source_status": source_status if withdrawn else metadata.get("source_status", ""),
        "metadata": metadata,
        "embedding": embed_text(content or "", dimensions=EMBEDDING_DIMENSIONS),
        "source": metadata.get("source", "local_seed"),
        "updated_at": metadata.get("stored_at") or metadata.get("issue_date") or "local_seed",
    }


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0

    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def _format_record(record: dict[str, Any], similarity_score: float | None = None, source: str | None = None) -> dict[str, Any]:
    metadata = record.get("metadata") or {}
    circular_id = record.get("circular_id") or record.get("id") or metadata.get("circular_id", "")
    content = record.get("content") or record.get("document") or ""
    display_text = record.get("display_text") or record.get("preview_text") or display_reference_text(content)
    withdrawn = bool(record.get("withdrawn")) or bool(metadata.get("withdrawn")) or _has_withdrawn_marker(content)
    source_status = record.get("source_status") or metadata.get("source_status") or source_status_for_text(content)
    return {
        "circular_id": circular_id,
        "id": circular_id,
        "title": derive_reference_title(
            content,
            uploaded_file_name=metadata.get("file_name"),
            user_title=record.get("title") or metadata.get("title"),
            fallback="Approved Policy Reference",
        ),
        "category": record.get("category") or metadata.get("category") or "Regulatory Compliance",
        "content": content,
        "content_excerpt": _content_excerpt(display_text or content),
        "preview_text": display_text,
        "display_text": display_text,
        "withdrawn": withdrawn,
        "source_status": source_status if withdrawn else metadata.get("source_status", ""),
        "metadata": metadata,
        "similarity_score": round(float(similarity_score or 0.0), 4),
        "source": source or record.get("source") or metadata.get("source", "json_fallback"),
    }


def _chroma_available() -> bool:
    return chromadb is not None


def _get_collection():
    global _client, _collection, _client_mode, _last_chroma_error
    if not _chroma_available():
        _last_chroma_error = "chromadb package is not installed"
        return None

    if _collection is not None:
        return _collection

    _ensure_dirs()
    host = os.getenv("CHROMA_HOST")
    port = os.getenv("CHROMA_PORT", "8000")

    if host:
        try:
            _client = chromadb.HttpClient(host=host, port=int(port))
            _collection = _client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"description": "Offline RBI regulatory memory"},
            )
            _client_mode = "http"
            return _collection
        except Exception as exc:
            _last_chroma_error = f"HTTP Chroma unavailable: {exc}"
            _client = None
            _collection = None

    try:
        _client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "Offline RBI regulatory memory"},
        )
        _client_mode = "persistent"
        return _collection
    except Exception as exc:
        _last_chroma_error = f"Persistent Chroma unavailable: {exc}"
        _client = None
        _collection = None
        return None


def add_circular(circular: dict) -> dict:
    circular_id = circular.get("circular_id") or circular.get("id")
    content = circular.get("content") or circular.get("text") or ""
    metadata = {
        key: value
        for key, value in circular.items()
        if key not in {"content", "text", "embedding"}
    }
    if metadata.get("source_type") == "User added approved reference" or str(circular_id or "").startswith("USER-REF-"):
        content = clean_reference_text(content)
    return store_circular(circular_id, content, metadata)


def store_circular(circular_id: str, content: str, metadata: dict | None = None) -> dict:
    _ensure_dirs()
    if not circular_id:
        return {"status": "error", "reason": "circular_id is required", "circular_id": circular_id}

    metadata = metadata or {}
    metadata.setdefault("circular_id", circular_id)
    metadata.setdefault("source", "local_seed")
    metadata.setdefault("stored_at", metadata.get("issue_date") or "local_seed")
    if metadata.get("source_type") == "User added approved reference" or str(circular_id or "").startswith("USER-REF-"):
        original_content = content or ""
        content = clean_reference_text(original_content)
        title_content = f"{original_content}\n{content}"
        metadata["title"] = derive_reference_title(
            title_content,
            uploaded_file_name=metadata.get("file_name"),
            user_title=metadata.get("title"),
            fallback="Approved Policy Reference",
        )
        metadata["domain"] = infer_reference_domain(content, metadata.get("domain"))
        metadata["category"] = infer_reference_category(content, metadata["domain"], metadata.get("category"))
        metadata["withdrawn"] = _has_withdrawn_marker(original_content) or _has_withdrawn_marker(content)
        if metadata["withdrawn"]:
            metadata["source_status"] = "Withdrawn / archived"
    record = _fallback_record(circular_id, content or "", metadata)

    _upsert_fallback_record(record)

    collection = _get_collection()
    if collection is None:
        return {
            "status": "stored_fallback",
            "reason": _last_chroma_error or "ChromaDB unavailable",
            "circular_id": circular_id,
            "fallback_memory_path": str(FALLBACK_MEMORY_PATH),
        }

    try:
        collection.upsert(
            ids=[circular_id],
            documents=[content or ""],
            embeddings=[record["embedding"]],
            metadatas=[_safe_metadata(metadata)],
        )
        return {
            "status": "stored",
            "circular_id": circular_id,
            "chroma_mode": _client_mode,
            "fallback_memory_path": str(FALLBACK_MEMORY_PATH),
        }
    except Exception as exc:
        return {
            "status": "stored_fallback",
            "reason": str(exc),
            "circular_id": circular_id,
            "fallback_memory_path": str(FALLBACK_MEMORY_PATH),
        }


def cleanup_user_references() -> dict:
    records = _read_fallback_memory()
    if not records:
        return {"status": "ok", "updated": 0}

    updated_count = 0
    cleaned_records = []
    changed_records = []

    for record in records:
        circular_id = record.get("circular_id") or (record.get("metadata") or {}).get("circular_id")
        if not _is_user_reference_id(circular_id):
            cleaned_records.append(record)
            continue

        metadata = dict(record.get("metadata") or {})
        original_content = record.get("content") or ""
        cleaned_content = clean_reference_text(original_content)
        title_content = f"{original_content}\n{cleaned_content}"
        readable_title = derive_reference_title(
            title_content,
            uploaded_file_name=metadata.get("file_name"),
            user_title=metadata.get("title") or record.get("title"),
            fallback="Approved Policy Reference",
        )
        domain = infer_reference_domain(
            cleaned_content,
            metadata.get("domain") or record.get("domain"),
        )
        category = infer_reference_category(
            cleaned_content,
            domain,
            metadata.get("category") or record.get("category"),
        )
        withdrawn = _has_withdrawn_marker(original_content) or _has_withdrawn_marker(cleaned_content)
        source_status = "Withdrawn / archived" if withdrawn else metadata.get("source_status", "")

        metadata.update(
            {
                "circular_id": circular_id,
                "title": readable_title,
                "domain": domain,
                "category": category,
                "source": metadata.get("source") or "user_added_reference",
                "source_type": "User added approved reference",
                "withdrawn": withdrawn,
                "source_status": source_status,
            }
        )

        new_record = _fallback_record(circular_id, cleaned_content, metadata)
        changed = (
            record.get("content") != cleaned_content
            or record.get("title") != readable_title
            or record.get("category") != category
            or record.get("source_status") != new_record.get("source_status")
            or (record.get("metadata") or {}).get("title") != readable_title
            or (record.get("metadata") or {}).get("domain") != domain
            or (record.get("metadata") or {}).get("category") != category
            or (record.get("metadata") or {}).get("source_status") != source_status
            or bool((record.get("metadata") or {}).get("withdrawn")) != withdrawn
            or record.get("display_text") != new_record.get("display_text")
        )
        if changed:
            updated_count += 1
            changed_records.append(new_record)
            reference_path = CIRCULARS_DIR / f"{circular_id}.txt"
            if reference_path.exists():
                try:
                    reference_path.write_text(cleaned_content, encoding="utf-8")
                except OSError:
                    pass

        cleaned_records.append(new_record)

    if updated_count:
        _write_fallback_memory(cleaned_records)
        collection = _get_collection()
        if collection is not None:
            for record in changed_records:
                try:
                    collection.upsert(
                        ids=[record["circular_id"]],
                        documents=[record.get("content") or ""],
                        embeddings=[record["embedding"]],
                        metadatas=[_safe_metadata(record.get("metadata") or {})],
                    )
                except Exception:
                    continue

    return {"status": "ok", "updated": updated_count}


def delete_circular(circular_id: str) -> dict:
    _ensure_dirs()
    if not circular_id:
        return {"status": "error", "reason": "circular_id is required", "circular_id": circular_id}

    fallback_deleted = _delete_fallback_record(circular_id)
    chroma_deleted = False
    chroma_error = None

    collection = _get_collection()
    if collection is not None:
        try:
            existing = collection.get(ids=[circular_id]).get("ids", [])
            if existing:
                collection.delete(ids=[circular_id])
                chroma_deleted = True
        except Exception as exc:
            chroma_error = str(exc)

    if not fallback_deleted and not chroma_deleted:
        return {
            "status": "not_found",
            "circular_id": circular_id,
            "fallback_deleted": False,
            "chroma_deleted": False,
            "chroma_error": chroma_error,
        }

    return {
        "status": "deleted",
        "circular_id": circular_id,
        "fallback_deleted": fallback_deleted,
        "chroma_deleted": chroma_deleted,
        "chroma_error": chroma_error,
    }


def _search_fallback(query: str, n_results: int = 3) -> list[dict[str, Any]]:
    query_embedding = embed_text(query, dimensions=EMBEDDING_DIMENSIONS)
    scored = []

    for record in _read_fallback_memory():
        embedding = record.get("embedding")
        if not isinstance(embedding, list):
            embedding = embed_text(record.get("content", ""), dimensions=EMBEDDING_DIMENSIONS)
        score = _cosine_similarity(query_embedding, embedding)
        scored.append((score, record))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [
        _format_record(record, similarity_score=score, source="json_fallback")
        for score, record in scored[: max(0, n_results)]
        if score > 0
    ]


def search_similar(query: str, n_results: int = 3) -> list:
    if not query or not query.strip() or n_results <= 0:
        return []

    collection = _get_collection()
    if collection is not None:
        try:
            count = collection.count()
            if count == 0:
                return []

            results = collection.query(
                query_embeddings=[embed_text(query, dimensions=EMBEDDING_DIMENSIONS)],
                n_results=min(n_results, count),
                include=["documents", "metadatas", "distances"],
            )
            ids = results.get("ids", [[]])[0]
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]

            formatted = []
            for index, circular_id in enumerate(ids):
                distance = distances[index] if index < len(distances) else 1.0
                score = max(0.0, 1.0 - float(distance))
                metadata = metadatas[index] if index < len(metadatas) else {}
                content = documents[index] if index < len(documents) else ""
                formatted.append(
                    _format_record(
                        {
                            "circular_id": circular_id,
                            "title": metadata.get("title") or circular_id,
                            "category": metadata.get("category") or "Regulatory Compliance",
                            "content": content,
                            "metadata": metadata,
                            "source": f"chroma_{_client_mode}",
                        },
                        similarity_score=score,
                        source=f"chroma_{_client_mode}",
                    )
                )
            return formatted
        except Exception:
            return _search_fallback(query, n_results=n_results)

    return _search_fallback(query, n_results=n_results)


def list_circulars() -> list:
    return list_stored_circulars()


def list_stored_circulars() -> list:
    records = _read_fallback_memory()
    if records:
        return [_format_record(record, source="json_fallback") for record in records]

    collection = _get_collection()
    if collection is None:
        return []

    try:
        result = collection.get(include=["documents", "metadatas"])
        ids = result.get("ids", [])
        documents = result.get("documents", [])
        metadatas = result.get("metadatas", [])
        return [
            _format_record(
                {
                    "circular_id": ids[index],
                    "content": documents[index] if index < len(documents) else "",
                    "metadata": metadatas[index] if index < len(metadatas) else {},
                },
                source=f"chroma_{_client_mode}",
            )
            for index in range(len(ids))
        ]
    except Exception:
        return []


def clear_store() -> dict:
    global _collection
    deleted_fallback = False
    if FALLBACK_MEMORY_PATH.exists():
        FALLBACK_MEMORY_PATH.unlink()
        deleted_fallback = True

    collection = _get_collection()
    chroma_cleared = False
    if collection is not None:
        try:
            ids = collection.get().get("ids", [])
            if ids:
                collection.delete(ids=ids)
            chroma_cleared = True
        except Exception:
            chroma_cleared = False

    return {
        "status": "cleared",
        "fallback_deleted": deleted_fallback,
        "chroma_cleared": chroma_cleared,
    }


def store_status() -> dict:
    collection = _get_collection()
    count = 0
    if collection is not None:
        try:
            count = collection.count()
        except Exception:
            count = 0

    return {
        "chroma_available": collection is not None,
        "chroma_mode": _client_mode,
        "chroma_error": _last_chroma_error,
        "collection_count": count,
        "fallback_memory_path": str(FALLBACK_MEMORY_PATH),
        "fallback_count": len(_read_fallback_memory()),
    }


if __name__ == "__main__":
    print(json.dumps(store_status(), indent=2))
