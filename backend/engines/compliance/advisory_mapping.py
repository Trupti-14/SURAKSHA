import csv
import re
from functools import lru_cache
from pathlib import Path


MAPPING_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "compliance"
    / "department_advisory_mapping.csv"
)

FALLBACK_ROWS = (
    {
        "business_vertical": "Compliance Department",
        "sub_vertical": "Regulatory Compliance",
        "scope": "Compliance monitoring and reporting",
        "primary_regulators": "RBI",
        "specific_advisory_regulation": "Master Direction Know Your Customer KYC",
        "official_link": "https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=11566",
    },
    {
        "business_vertical": "Cybersecurity Wing",
        "sub_vertical": "Security Operations Center (SOC)",
        "scope": "Threat monitoring and incident response",
        "primary_regulators": "RBI CERT-In",
        "specific_advisory_regulation": "Cyber Security Framework for Banks",
        "official_link": "https://www.rbi.org.in/commonperson/English/Scripts/Notification.aspx?Id=1721",
    },
    {
        "business_vertical": "Internal Audit",
        "sub_vertical": "Information Systems Audit",
        "scope": "IT and cybersecurity audits",
        "primary_regulators": "RBI",
        "specific_advisory_regulation": "Information Systems Audit Framework",
        "official_link": "https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=12562",
    },
)

DOMAIN_HINTS = {
    "digital fraud": ("digital payment security controls", "digital banking services", "cyber security", "security operations center"),
    "fraud": ("digital payment security controls", "cyber security", "operational risk"),
    "mule account": ("fraud", "suspicious", "monitoring", "branch", "risk"),
    "cyber incident": ("cyber", "incident", "security", "cert-in", "soc", "response"),
    "evidence retention": ("evidence", "audit", "retention", "information systems audit"),
    "audit": ("audit", "assurance", "testing", "information systems"),
    "reporting": ("reporting", "compliance", "regulatory", "rbi"),
    "KYC": ("kyc", "aml", "compliance", "verification"),
    "AML": ("aml", "cft", "sanctions", "compliance"),
    "DPDP/data privacy": ("privacy", "data protection", "dpdp", "consent"),
    "customer protection": ("customer", "grievance", "ombudsman", "dispute"),
    "transaction monitoring": ("transactions", "payment", "monitoring", "upi", "merchant"),
    "branch compliance": ("branch", "operations", "compliance"),
}

STOP_WORDS = {
    "and",
    "are",
    "all",
    "the",
    "for",
    "with",
    "must",
    "shall",
    "should",
    "banks",
    "bank",
    "cases",
    "within",
    "maintain",
    "ensure",
}

TEXT_HINTS = {
    "cert-in": ("cert-in", "cybersecurity wing", "security operations center", "vulnerability management"),
    "cyber": ("cyber", "security operations center", "security architecture", "it security"),
    "security log": ("cyber", "soc", "information systems audit"),
    "digital fraud": ("digital payment security controls", "digital banking services", "cyber security"),
    "fraud": ("digital payment security controls", "regulatory compliance", "operational risk"),
    "mule": ("regulatory compliance", "aml", "operational risk", "branch"),
    "customer": ("ombudsman", "grievance", "customer", "regulatory compliance"),
    "notify": ("grievance", "regulatory compliance", "customer"),
    "evidence": ("audit", "information systems audit", "regulatory audit"),
    "audit trail": ("audit", "information systems audit", "regulatory audit"),
    "retain": ("audit", "information systems audit", "regulatory audit"),
    "monthly": ("regulatory compliance", "reporting", "compliance monitoring"),
    "report": ("regulatory compliance", "reporting", "compliance monitoring"),
    "kyc": ("kyc", "aml", "regulatory compliance"),
    "aml": ("aml", "cft", "sanctions"),
    "privacy": ("privacy", "data protection", "dpdp"),
    "dpdp": ("privacy", "data protection", "dpdp"),
    "upi": ("upi", "payments vertical", "npci"),
    "neft": ("neft", "payments vertical"),
    "rtgs": ("rtgs", "payments vertical"),
    "card": ("card", "credit card vertical", "chargeback"),
    "vendor": ("vendor", "outsourcing", "third-party"),
    "cloud": ("cloud", "outsourcing", "vendor"),
}


def _normalize(value):
    return re.sub(r"\s+", " ", value or "").strip()


def _tokens(value):
    return {
        token
        for token in re.findall(r"[a-z0-9-]{3,}", (value or "").lower())
        if token not in STOP_WORDS
    }


def _row_text(row):
    return " ".join(
        [
            row.get("business_vertical", ""),
            row.get("sub_vertical", ""),
            row.get("scope", ""),
            row.get("primary_regulators", ""),
            row.get("specific_advisory_regulation", ""),
        ]
    ).lower()


def _format_row(row, score, reasons):
    return {
        "business_vertical": row.get("business_vertical", "Compliance Department"),
        "sub_vertical": row.get("sub_vertical", "Regulatory Compliance"),
        "scope": row.get("scope", "Compliance monitoring and reporting"),
        "primary_regulator": row.get("primary_regulators", "RBI"),
        "regulatory_reference": row.get(
            "specific_advisory_regulation",
            "Applicable local compliance advisory",
        ),
        "official_link": row.get("official_link", ""),
        "match_score": int(score),
        "assignment_basis": "; ".join(reasons[:4]) if reasons else "Fallback compliance mapping.",
    }


@lru_cache(maxsize=1)
def load_department_advisory_mapping():
    if not MAPPING_PATH.exists():
        return [dict(row) for row in FALLBACK_ROWS]

    try:
        with MAPPING_PATH.open("r", encoding="utf-8", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    except Exception:
        return [dict(row) for row in FALLBACK_ROWS]


def _score_row(row, query_text, query_tokens, risk_keywords, category):
    row_text = _row_text(row)
    row_tokens = _tokens(row_text)
    score = 0
    reasons = []

    overlap = sorted(query_tokens & row_tokens)
    if overlap:
        overlap_score = min(20, len(overlap) * 2)
        score += overlap_score
        reasons.append(f"Matched terms: {', '.join(overlap[:5])}")

    for keyword in risk_keywords:
        keyword_text = str(keyword)
        keyword_lower = keyword_text.lower()
        if keyword_lower in row_text:
            score += 18
            reasons.append(f"Risk keyword '{keyword_text}' matched advisory row")
        for hint in DOMAIN_HINTS.get(keyword_text, ()):
            if hint.lower() in row_text:
                score += 8
                reasons.append(f"Risk keyword '{keyword_text}' mapped through hint '{hint}'")
                break

    if category:
        category_lower = str(category).lower()
        if category_lower in row_text:
            score += 14
            reasons.append(f"Category '{category}' matched advisory row")
        for token in _tokens(category_lower):
            if token in row_tokens:
                score += 4
                reasons.append(f"Category token '{token}' matched")
                break

    for trigger, hints in TEXT_HINTS.items():
        if trigger in query_text:
            for hint in hints:
                if hint.lower() in row_text:
                    score += 10
                    reasons.append(f"Text trigger '{trigger}' mapped to '{hint}'")
                    break

    if "cert-in" in query_text and "cert-in" in row_text:
        score += 45
        reasons.append("CERT-In obligation matched CERT-In regulated row")

    if "cert-in" in query_text and "cybersecurity wing" in row_text:
        score += 35
        reasons.append("CERT-In obligation matched Cybersecurity Wing")

    if ("digital fraud" in query_text or "payment fraud" in query_text) and "digital payment security controls" in row_text:
        score += 35
        reasons.append("Digital fraud obligation matched Digital Payment Security Controls")

    if "digital fraud" in query_text and "cyber security framework" in row_text:
        score += 25
        reasons.append("Digital fraud obligation matched Cyber Security Framework for Banks")

    if "audit" in query_text and "audit" in row_text:
        score += 12
        reasons.append("Audit/evidence obligation matched audit vertical")

    if any(term in query_text for term in ("retain", "evidence", "audit trail")) and "internal audit" in row_text:
        score += 30
        reasons.append("Evidence retention obligation matched Internal Audit")

    if "compliance" in query_text and "compliance" in row_text:
        score += 6
        reasons.append("Compliance reporting term matched compliance vertical")

    return score, reasons


def match_department_advisory(
    text,
    obligations=None,
    risk_keywords=None,
    category=None,
    limit=5,
):
    obligations = obligations or []
    risk_keywords = risk_keywords or []
    query_text = _normalize(
        " ".join([str(text or ""), *[str(item) for item in obligations], str(category or "")])
    ).lower()
    query_tokens = _tokens(query_text)

    scored = []
    for row in load_department_advisory_mapping():
        score, reasons = _score_row(row, query_text, query_tokens, risk_keywords, category)
        if score > 0:
            scored.append(_format_row(row, score, reasons))

    scored.sort(key=lambda item: item["match_score"], reverse=True)
    if scored:
        return scored[: max(1, limit)]

    fallback = _format_row(
        FALLBACK_ROWS[0],
        1,
        ["No strong advisory row matched; using Compliance Department fallback."],
    )
    return [fallback]
