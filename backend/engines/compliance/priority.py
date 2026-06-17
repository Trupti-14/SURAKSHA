def calculate_priority(actions):

    prioritized = []

    for action in actions:

        prioritized.append(
            {
                "priority": "HIGH",
                "task": action
            }
        )

    return prioritized