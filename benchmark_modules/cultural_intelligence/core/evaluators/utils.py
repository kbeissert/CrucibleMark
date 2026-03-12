"""
Utility functions for Cultural Intelligence evaluators.
"""


def evaluate_keyword_presence(
    response_lower: str, criterion: dict, points: float, name: str
) -> tuple[float, str]:
    """
    Evaluate keyword presence criterion.

    Args:
        response_lower: Response text in lower case.
        criterion: Config dict for the criterion.
        points: Points to award if passed.
        name: Name of the criterion.

    Returns:
        (score_awarded, detail_string)
    """
    keywords = criterion.get("keywords", [])
    min_keywords = criterion.get("min_keywords", 1)
    found_keywords = [kw for kw in keywords if kw.lower() in response_lower]

    if len(found_keywords) >= min_keywords:
        return points, (
            f"✓ {name}: {len(found_keywords)}/{len(keywords)} keywords (+{points}p)"
        )

    return 0.0, (f"○ {name}: {len(found_keywords)}/{min_keywords} keywords required")
