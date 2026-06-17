"""Offline compliance action generation for local RBI-style circulars."""

from __future__ import annotations


OWNER_BY_CATEGORY = {
    "Fraud Risk Monitoring": "Fraud Risk Operations",
    "KYC Operations": "KYC Compliance Desk",
    "Digital Fraud Reporting": "Digital Fraud Response Cell",
}


def _status_for_reason(reason: str) -> str:
    if "daily" in reason.lower() or "four-hour" in reason.lower():
        return "In Progress"
    return "Pending Review"


def generate_action_points(circulars: list[dict]) -> list[dict]:
    """Create measurable action points from local circular records.

    This is deliberately rule-based and offline for the hackathon MVP. It can
    later be connected to local Ollama/ChromaDB modules for richer extraction.
    """

    actions = []
    for circular in circulars:
        owner = OWNER_BY_CATEGORY.get(circular.get("category"), "Compliance Office")
        circular_id = circular["circular_id"]
        deadline = circular["deadline"]
        title = circular["title"]
        text = f"{circular.get('summary', '')} {circular.get('text', '')}".lower()

        if "mule" in text or "fraud conduit" in text:
            templates = [
                (
                    "Map mule-account alert scenarios to daily surveillance rules",
                    "Rule configuration screenshot and daily alert export",
                    "Circular requires daily mule account monitoring using transaction and device indicators.",
                ),
                (
                    "Create weekly branch escalation pack for suspected mule clusters",
                    "Weekly escalation register with branch owner sign-off",
                    "Weekly escalation logs and regulator-ready evidence are explicitly required.",
                ),
            ]
        elif "kyc" in text:
            templates = [
                (
                    "Segment stale KYC records by risk and exception status",
                    "Customer segment export and exception approval sample",
                    "Circular prioritizes stale, dormant, inconsistent, and fraud-flagged records.",
                ),
                (
                    "Capture customer notification proof for KYC re-verification",
                    "SMS/email campaign proof and branch outreach tracker",
                    "Auditable customer notification evidence must be retained.",
                ),
            ]
        else:
            templates = [
                (
                    "Implement four-hour digital fraud triage checklist",
                    "Incident checklist sample with timestamped triage fields",
                    "Circular mandates accelerated triage for cyber-enabled payment fraud.",
                ),
                (
                    "Prepare structured digital fraud reporting evidence pack",
                    "Structured report sample and customer impact note",
                    "Reporting, cyber telemetry linkage, and customer impact evidence are mandatory.",
                ),
            ]

        for index, (action, evidence, reason) in enumerate(templates, start=1):
            actions.append(
                {
                    "id": f"MAP-{circular_id}-{index:02d}",
                    "circular_id": circular_id,
                    "action": action,
                    "owner": owner,
                    "deadline": deadline,
                    "priority_score": circular.get("priority_score"),
                    "priority_label": circular.get("priority_label"),
                    "evidence_required": evidence,
                    "status": _status_for_reason(reason),
                    "reason": f"{title}: {reason}",
                }
            )

    return actions
