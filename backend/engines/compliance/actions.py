def extract_action_points(content):

    action_points = []

    lines = content.split("\n")

    for line in lines:
        if "must" in line.lower():
            action_points.append(line.strip())

    return {
        "action_points": action_points
    }