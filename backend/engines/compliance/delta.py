def compare_policy(old_policy, new_policy):

    old_words = set(old_policy.lower().split())
    new_words = set(new_policy.lower().split())

    missing_controls = list(new_words - old_words)

    return {
        "gap_found": len(missing_controls) > 0,
        "missing_controls": missing_controls[:20]
    }