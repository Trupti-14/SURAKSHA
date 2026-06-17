"""Ollama-ready local language helper with deterministic offline fallback."""

from __future__ import annotations

import json
import os
import re
import socket
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


OLLAMA_HOST = "127.0.0.1"
OLLAMA_PORT = 11434
OLLAMA_URL = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/api/generate"
DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")

OBLIGATION_TERMS = (
    "must",
    "shall",
    "required",
    "mandatory",
    "report",
    "retain",
    "review",
    "complete",
    "submit",
)


def _sentences(text: str | None) -> list[str]:
    if not text:
        return []

    candidates = re.split(r"(?<=[.!?])\s+", str(text).strip())
    return [sentence.strip() for sentence in candidates if sentence.strip()]


def is_local_llm_available() -> bool:
    """Return True when a local Ollama service is reachable on loopback."""

    try:
        with socket.create_connection((OLLAMA_HOST, OLLAMA_PORT), timeout=0.25):
            return True
    except OSError:
        return False


def _call_ollama(prompt: str) -> str | None:
    if not is_local_llm_available():
        return None

    payload = json.dumps(
        {
            "model": DEFAULT_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0},
        }
    ).encode("utf-8")
    request = Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=5) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, json.JSONDecodeError, TimeoutError):
        return None

    result = body.get("response")
    if isinstance(result, str) and result.strip():
        return result.strip()

    return None


def summarize_policy_text(text: str) -> str:
    """Summarize policy text using local Ollama when available, otherwise rules."""

    if not text:
        return "No policy text was provided for review."

    prompt = (
        "Summarize this banking compliance text in two concise sentences. "
        "Do not claim external AI or cloud processing.\n\n"
        f"{text}"
    )
    local_result = _call_ollama(prompt)
    if local_result:
        return local_result

    sentences = _sentences(text)
    if not sentences:
        return "No policy text was provided for review."

    return " ".join(sentences[:2])


def extract_obligations_with_fallback(text: str) -> list[str]:
    """Extract likely compliance obligations with local fallback logic."""

    if not text:
        return []

    prompt = (
        "Extract concrete banking compliance obligations as a short bullet list. "
        "Use only the supplied text.\n\n"
        f"{text}"
    )
    local_result = _call_ollama(prompt)
    if local_result:
        obligations = [
            line.strip(" -\t")
            for line in local_result.splitlines()
            if line.strip(" -\t")
        ]
        if obligations:
            return obligations

    obligations = []
    for sentence in _sentences(text):
        lowered = sentence.lower()
        if any(term in lowered for term in OBLIGATION_TERMS):
            obligations.append(sentence)

    return obligations


def generate_explainable_reason(context: dict[str, Any] | str) -> str:
    """Generate a clear compliance reason from supplied local context."""

    if isinstance(context, dict):
        title = context.get("title") or context.get("circular_id") or "Circular"
        priority = context.get("priority_label")
        deadline = context.get("deadline")
        reason = context.get("priority_reason") or context.get("reason")
        parts = [str(title)]
        if priority:
            parts.append(f"priority is {priority}")
        if deadline:
            parts.append(f"deadline is {deadline}")
        if reason:
            parts.append(str(reason))
        return "; ".join(parts)

    summary = summarize_policy_text(str(context))
    return f"Compliance reason: {summary}"
