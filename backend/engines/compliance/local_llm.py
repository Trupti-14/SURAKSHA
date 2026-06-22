import json
import os
import re
import time
import urllib.error
import urllib.request


OLLAMA_GENERATE_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "phi3"
VALID_MODES = {"auto", "rules", "ollama"}
FAILURE_COOLDOWN_SECONDS = 30
_DISABLED_UNTIL = 0.0


def get_llm_mode():
    mode = (os.getenv("COMPLIANCE_LLM_MODE") or "auto").strip().lower()
    return mode if mode in VALID_MODES else "auto"


def get_ollama_model():
    return (os.getenv("OLLAMA_MODEL") or DEFAULT_MODEL).strip() or DEFAULT_MODEL


def _timeout_seconds():
    raw_value = (os.getenv("COMPLIANCE_OLLAMA_TIMEOUT_SECONDS") or "3").strip()
    try:
        timeout = float(raw_value)
    except ValueError:
        timeout = 3.0
    return min(max(timeout, 0.5), 10.0)


def is_llm_enabled():
    return get_llm_mode() != "rules"


def _extract_json_object(text):
    if not text:
        return None

    cleaned = str(text).strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, flags=re.I | re.S)
    if fenced:
        cleaned = fenced.group(1).strip()

    try:
        return json.loads(cleaned)
    except (TypeError, ValueError):
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    try:
        return json.loads(cleaned[start : end + 1])
    except (TypeError, ValueError):
        return None


def _generate(prompt, *, model=None, timeout=None):
    global _DISABLED_UNTIL

    if not is_llm_enabled():
        return None
    if time.monotonic() < _DISABLED_UNTIL:
        return None

    payload = {
        "model": model or get_ollama_model(),
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0,
            "top_p": 0.2,
            "num_predict": 900,
        },
    }

    request = urllib.request.Request(
        OLLAMA_GENERATE_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout or _timeout_seconds()) as response:
            body = response.read().decode("utf-8", errors="replace")
    except (OSError, TimeoutError, urllib.error.URLError, urllib.error.HTTPError, ValueError):
        _DISABLED_UNTIL = time.monotonic() + FAILURE_COOLDOWN_SECONDS
        return None

    try:
        decoded = json.loads(body)
    except ValueError:
        _DISABLED_UNTIL = time.monotonic() + FAILURE_COOLDOWN_SECONDS
        return None

    generated_text = decoded.get("response")
    if not isinstance(generated_text, str) or not generated_text.strip():
        _DISABLED_UNTIL = time.monotonic() + FAILURE_COOLDOWN_SECONDS
        return None
    return generated_text.strip()


def generate_json(prompt, *, model=None, timeout=None):
    generated_text = _generate(prompt, model=model, timeout=timeout)
    return _extract_json_object(generated_text)


def extract_circular_fields(circular_text):
    text = (circular_text or "").strip()
    if len(text) < 120:
        return None

    excerpt = text[:9000]
    prompt = f"""
You are a local RBI compliance extraction assistant running offline.
Return only strict JSON. Do not include markdown.

Extract these fields from the circular text:
- summary: one concise factual sentence
- key_obligations: array of concrete obligations stated in the circular
- deadlines: array of timelines/deadlines exactly as stated where possible
- domain: short compliance domain label
- impacted_departments: array of bank teams/functions impacted

Rules:
- Use only the circular text below.
- Prefer obligations containing shall, must, should, ensure, maintain, submit, report, notify, retain, monitor, review, audit, escalate, approve, incident, access, logs, BCP, DR, CISO, SOC.
- Do not invent RBI requirements.
- Keep each obligation specific and implementation-ready.

Circular text:
{excerpt}
""".strip()
    return generate_json(prompt)


def compare_obligation_to_reference(obligation, existing_reference, domain=None):
    obligation_text = (obligation or "").strip()
    reference_text = (existing_reference or "").strip()
    if len(obligation_text) < 20 or len(reference_text) < 30:
        return None

    prompt = f"""
You are a local RBI compliance comparison assistant running offline.
Return only strict JSON. Do not include markdown.

Compare the new obligation to the existing approved reference.
Return:
- gap_found: boolean
- gap_summary: one concrete sentence describing the missing/changed control if a gap exists
- change_type: one of missing_policy, deadline_changed, reporting_frequency_changed, evidence_required, department_owner_missing, audit_trail_missing, new_obligation, manual_review
- confidence: number from 0 to 1

Rules:
- Use only the two texts below.
- Do not say a reference matches if it is about a different domain.
- Do not use customer notification text as fraud reporting timeline evidence.
- Do not use generic audit/evidence text as CERT-In/cyber incident response evidence.
- If uncertain, set gap_found true with change_type manual_review and confidence below 0.7.

Domain: {domain or "unknown"}

New obligation:
{obligation_text[:1800]}

Existing approved reference:
{reference_text[:1800]}
""".strip()
    return generate_json(prompt)
