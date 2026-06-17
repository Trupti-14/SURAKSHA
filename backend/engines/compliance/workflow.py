from .scout import get_circular_by_id
from .delta import compare_policy
from .actions import extract_action_points


def run_compliance_workflow(circular_id=None, new_content=None):

    if circular_id:
        circular = get_circular_by_id(circular_id)

        if not circular:
            return {"error": "Circular not found"}

        content = circular["content"]

    else:
        content = new_content

    baseline_policy = """
    MFA required
    Fraud monitoring enabled
    Customer authentication mandatory
    """

    delta = compare_policy(
        baseline_policy,
        content
    )

    actions = extract_action_points(content)

    return {
        "delta": delta,
        "actions": actions
    }