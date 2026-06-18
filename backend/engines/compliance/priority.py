from datetime import datetime

def calculate_priority(action_points: list) -> list:
    prioritized = []

    for ap in action_points:
        deadline_days = ap.get("deadline_days", 30)

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

        label = "CRITICAL" if score >= 9 else "HIGH" if score >= 7 else "MEDIUM" if score >= 5 else "LOW"

        prioritized.append({
            **ap,
            "priority_score": score,
            "priority_label": label,
            "calculated_at": datetime.utcnow().isoformat()
        })

    return sorted(prioritized, key=lambda x: x["priority_score"], reverse=True)