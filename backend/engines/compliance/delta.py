import subprocess
import json

def _ask_phi3(prompt: str) -> str:
    try:
        result = subprocess.run(
            ["ollama", "run", "phi3", prompt],
            capture_output=True, text=True, timeout=60
        )
        return result.stdout.strip()
    except Exception as e:
        return ""

def compare_policy(old_policy: str, new_policy: str) -> dict:
    # Basic keyword gap detection (always runs)
    old_words = set(old_policy.lower().split())
    new_words = set(new_policy.lower().split())
    missing_controls = list(new_words - old_words)

    # Phi-3 enhanced analysis
    prompt = f"""You are a banking compliance analyst.
Compare these two policy texts and identify compliance gaps.

EXISTING POLICY:
{old_policy[:500]}

NEW CIRCULAR:
{new_policy[:500]}

Reply in JSON only:
{{"gap_found": true/false, "summary": "one sentence", "risk_level": "LOW/MEDIUM/HIGH", "key_changes": ["change1", "change2"]}}"""

    phi3_response = _ask_phi3(prompt)
    
    try:
        clean = phi3_response.strip().strip("```json").strip("```").strip()
        phi3_result = json.loads(clean)
        return {
            "gap_found": phi3_result.get("gap_found", len(missing_controls) > 0),
            "missing_controls": missing_controls[:10],
            "summary": phi3_result.get("summary", ""),
            "risk_level": phi3_result.get("risk_level", "MEDIUM"),
            "key_changes": phi3_result.get("key_changes", []),
            "analysis_by": "phi3"
        }
    except Exception:
        return {
            "gap_found": len(missing_controls) > 0,
            "missing_controls": missing_controls[:10],
            "summary": "Keyword-based analysis (Phi-3 unavailable)",
            "risk_level": "MEDIUM",
            "key_changes": [],
            "analysis_by": "keyword"
        }