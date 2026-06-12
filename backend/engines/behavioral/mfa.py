from enum import Enum


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class MFAAction(str, Enum):
    PASSKEY_ALLOWED = "PASSKEY_ALLOWED"
    STEP_UP_REQUIRED = "STEP_UP_REQUIRED"
    SESSION_BLOCKED = "SESSION_BLOCKED"


def evaluate_mfa(risk_score: int) -> dict:
    """
    Evaluate adaptive MFA decision based on behavioral risk score.

    Risk Rules:
    0-30   -> Passkey allowed
    31-70  -> TOTP / biometric step-up required
    71-100 -> Block session
    """

    if risk_score < 0 or risk_score > 100:
        raise ValueError("risk_score must be between 0 and 100")

    if risk_score <= 30:
        return {
            "risk_score": risk_score,
            "risk_level": RiskLevel.LOW.value,
            "mfa_action": MFAAction.PASSKEY_ALLOWED.value,
            "session_status": "NORMAL",
            "message": "Low behavioral risk detected. Passkey authentication allowed.",
            "requires_totp": False,
            "requires_biometric": False,
            "session_blocked": False,
        }

    if risk_score <= 70:
        return {
            "risk_score": risk_score,
            "risk_level": RiskLevel.MEDIUM.value,
            "mfa_action": MFAAction.STEP_UP_REQUIRED.value,
            "session_status": "ESCALATED",
            "message": "Medium behavioral risk detected. TOTP or biometric step-up required.",
            "requires_totp": True,
            "requires_biometric": True,
            "session_blocked": False,
        }

    return {
        "risk_score": risk_score,
        "risk_level": RiskLevel.HIGH.value,
        "mfa_action": MFAAction.SESSION_BLOCKED.value,
        "session_status": "BLOCKED",
        "message": "High behavioral risk detected. Session blocked immediately.",
        "requires_totp": False,
        "requires_biometric": False,
        "session_blocked": True,
    }


if __name__ == "__main__":
    test_scores = [15, 45, 85]

    for score in test_scores:
        print(evaluate_mfa(score))