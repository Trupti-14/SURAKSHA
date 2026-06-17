"""Rule-based offline priority scoring for compliance circulars."""

from __future__ import annotations

from datetime import date, datetime


HIGH_RISK_KEYWORDS = ("fraud", "mule", "cyber", "cybersecurity", "payment")
IMPACT_KEYWORDS = ("penalty", "reporting", "customer impact", "breach", "mandatory")


def _parse_date(value: str) -> date | None:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def calculate_priority(circular: dict, today: date | None = None) -> dict:
    """Return a 1-10 priority score using transparent offline rules.

    This avoids external LLM/cloud APIs. A later advanced track can replace or
    enrich this with local Ollama/ChromaDB retrieval while keeping the API shape.
    """

    today = today or date.today()
    text = " ".join(
        str(circular.get(field, ""))
        for field in ("title", "category", "summary", "new_policy", "text")
    ).lower()

    score = 3
    reasons = ["base compliance review score"]

    risk_hits = [keyword for keyword in HIGH_RISK_KEYWORDS if keyword in text]
    if risk_hits:
        score += min(3, len(risk_hits))
        reasons.append(f"risk keywords: {', '.join(risk_hits)}")

    impact_hits = [keyword for keyword in IMPACT_KEYWORDS if keyword in text]
    if impact_hits:
        score += min(2, len(impact_hits))
        reasons.append(f"impact/reporting terms: {', '.join(impact_hits)}")

    deadline = _parse_date(circular.get("deadline"))
    if deadline:
        days_left = (deadline - today).days
        if days_left <= 7:
            score += 3
            reasons.append(f"deadline within 7 days ({max(days_left, 0)} days left)")
        elif days_left <= 21:
            score += 2
            reasons.append(f"deadline within 21 days ({days_left} days left)")
        elif days_left <= 45:
            score += 1
            reasons.append(f"deadline within 45 days ({days_left} days left)")

    priority_score = max(1, min(10, score))
    if priority_score >= 8:
        priority_label = "Critical"
    elif priority_score >= 6:
        priority_label = "High"
    elif priority_score >= 4:
        priority_label = "Medium"
    else:
        priority_label = "Low"

    return {
        "priority_score": priority_score,
        "priority_label": priority_label,
        "priority_reason": "; ".join(reasons),
    }
