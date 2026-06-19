import re

from .scout import parse_circular_text


NO_PRIOR_POLICY = "No matching prior policy found."

DOMAIN_TERMS = {
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
    "fraud": "Fraud incident register, detection timestamp, reporting timestamp, customer impact note, and evidence reference",
    "customer": "Customer notification proof, timestamp, delivery status, and exception approval",
    "evidence": "Evidence retention register, archive proof, and audit trail export",
    "reporting": "Regulatory report sample, submission acknowledgement, and Compliance Office sign-off",
    "branch": "Branch escalation register, owner sign-off, and closure timestamp",
    "kyc": "KYC/AML verification tracker, exception approval sample, and suspicious account review note",
    "cyber": "Security log export, incident ticket, digital evidence hash, and containment note",
    "privacy": "DPDP assessment note, customer data handling log, and privacy approval evidence",
    "authentication": "Authentication control configuration screenshot and test evidence",
}


def _normalize_space(value):
    return re.sub(r"\s+", " ", value or "").strip()


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
    if any(term in lower for term in ("retain", "preserve", "evidence", "audit trail", "audit", "archive")):
        return "evidence"
    if any(term in lower for term in ("notify", "customer notification", "affected customer", "grievance")):
        return "customer"
    if any(term in lower for term in ("branch", "branch-level", "escalation", "escalate")):
        return "branch"
    if any(term in lower for term in ("kyc", "aml", "verification", "suspicious transaction")):
        return "kyc"
    if any(term in lower for term in ("cyber", "security log", "digital evidence", "incident")):
        return "cyber"
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
    if domain in {"fraud", "cyber"}:
        return "Critical" if change_type in {"missing_policy", "deadline_changed"} else "High"
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
        return _normalize_space(document.get("content") or document.get("text") or document.get("summary") or "")
    return _normalize_space(str(document or ""))


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

    if old_policy and _normalize_space(old_policy) and old_policy != NO_PRIOR_POLICY:
        documents.append(
            {
                "id": "provided_old_policy",
                "content": _normalize_space(old_policy),
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


def _gap_message(change_type, old_requirement, new_requirement, domain):
    if change_type == "deadline_changed":
        return f"Existing {domain} policy has a different deadline than the new RBI circular requirement."
    if change_type == "missing_policy":
        return f"No matching internal policy found for: {new_requirement}"
    if change_type == "reporting_frequency_changed":
        return f"Existing {domain} reporting process does not match the new reporting frequency."
    if change_type == "evidence_required":
        return f"Existing {domain} policy does not cover the evidence or retention requirement."
    if change_type == "department_owner_missing":
        return f"Existing process does not define the required department owner or escalation path."
    if change_type == "audit_trail_missing":
        return f"Existing process does not include the required audit trail controls."
    return f"Existing policy is incomplete for the new RBI obligation: {new_requirement}"


def _department_for_gap(domain, obligation):
    lower = (obligation or "").lower()
    if domain == "reporting" and any(term in lower for term in ("fraud", "mule", "digital fraud")):
        return "Fraud Risk Department + Compliance Office"
    if domain == "evidence" and any(term in lower for term in ("cyber", "digital evidence", "security log")):
        return "Cybersecurity / IT Security + Internal Audit"
    return DEPARTMENT_BY_DOMAIN.get(domain, "Compliance Office")


def _evidence_for_gap(domain, obligation):
    lower = (obligation or "").lower()
    if domain == "reporting" and any(term in lower for term in ("monthly", "report", "submit")):
        return "Monthly monitoring report, maker-checker approval, and Compliance Office submission proof"
    return EVIDENCE_BY_DOMAIN.get(domain, "Compliance evidence pack and owner sign-off")


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
                "affected_department": _department_for_gap(domain, obligation),
                "deadline": deadline,
                "evidence_required": _evidence_for_gap(domain, obligation),
                "confidence": _confidence(change_type, source_document),
                "source": source_document["id"] if source_document else "No matching prior policy found",
                "change_type": change_type,
            }
        )

        if len(gaps) >= 8:
            break

    if not gaps:
        gaps.append(
            {
                "id": "GAP-001",
                "gap": "No material policy gap detected; manual compliance confirmation is recommended.",
                "policy_gap": "No material policy gap detected; manual compliance confirmation is recommended.",
                "basis": "Scout obligations were compared with available regulatory memory and no strong delta was detected.",
                "severity": "Low",
                "old_requirement": "Relevant prior policy appears broadly aligned.",
                "new_requirement": obligations[0] if obligations else content[:180],
                "affected_department": "Compliance Office",
                "deadline": scout.get("deadline"),
                "evidence_required": "Compliance review note and owner sign-off",
                "confidence": 0.62,
                "source": "deterministic_delta",
                "change_type": "manual_review",
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
