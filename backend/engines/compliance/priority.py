from datetime import datetime


def _priority_label(score: int) -> str:
    if score >= 9:
        return "Critical"
    if score >= 7:
        return "High"
    if score >= 5:
        return "Medium"
    return "Low"


def _priority_reason(action_text: str, deadline_days: int, score: int) -> str:
    reasons = []
    lower_action = action_text.lower()

    if deadline_days <= 7:
        reasons.append("implementation deadline is within 7 days")
    elif deadline_days <= 15:
        reasons.append("implementation deadline is within 15 days")
    elif deadline_days <= 30:
        reasons.append("implementation deadline is within 30 days")

    if any(k in lower_action for k in ["security", "fraud", "kyc", "aml", "authentication"]):
        reasons.append("banking risk keywords are present")
    elif any(k in lower_action for k in ["audit", "report", "log"]):
        reasons.append("audit or reporting evidence is required")

    if not reasons:
        reasons.append("standard offline compliance scoring was applied")

    return f"{_priority_label(score)} priority because " + "; ".join(reasons) + "."


def calculate_priority(action_points: list) -> list:
    prioritized = []

    for ap in action_points:
        try:
            deadline_days = int(ap.get("deadline_days", 30))
        except (TypeError, ValueError):
            deadline_days = 30

        if deadline_days <= 7:
            score = 10
        elif deadline_days <= 15:
            score = 8
        elif deadline_days <= 30:
            score = 6
        elif deadline_days <= 60:
            score = 4
        else:
            score = 2

        action_text = ap.get("action", "").lower()
        if any(k in action_text for k in ["security", "fraud", "kyc", "aml", "authentication"]):
            score = min(10, score + 2)
        elif any(k in action_text for k in ["audit", "report", "log"]):
            score = min(10, score + 1)

        action_text = ap.get("action", "")
        label = _priority_label(score)

        prioritized.append({
            **ap,
            "priority_score": score,
            "priority_label": label,
            "priority_reason": _priority_reason(action_text, deadline_days, score),
            "calculated_at": datetime.utcnow().isoformat()
        })

    return sorted(prioritized, key=lambda x: x["priority_score"], reverse=True)
