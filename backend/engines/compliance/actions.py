import subprocess
import json

def _ask_phi3(prompt: str) -> str:
    try:
        result = subprocess.run(
            ["ollama", "run", "phi3", prompt],
            capture_output=True, text=True, timeout=60
        )
        return result.stdout.strip()
    except Exception:
        return ""

def extract_action_points(content: str) -> dict:
    # Basic extraction — find lines with "must"
    lines = content.split("\n")
    basic_actions = [line.strip() for line in lines if "must" in line.lower() and len(line.strip()) > 10]

    # Phi-3 enhanced extraction
    prompt = f"""You are a banking compliance officer.
Extract all Measurable Action Points from this RBI circular.

CIRCULAR:
{content[:600]}

Reply in JSON only:
{{"action_points": [{{"id": "MAP-001", "action": "specific action", "department": "responsible dept", "deadline_days": 30}}]}}"""

    phi3_response = _ask_phi3(prompt)

    try:
        clean = phi3_response.strip().strip("```json").strip("```").strip()
        result = json.loads(clean)
        return result
    except Exception:
        # Fallback to basic extraction
        return {
            "action_points": [
                {"id": f"MAP-{str(i+1).zfill(3)}", "action": a, "department": "Compliance", "deadline_days": 30}
                for i, a in enumerate(basic_actions)
            ]
        }