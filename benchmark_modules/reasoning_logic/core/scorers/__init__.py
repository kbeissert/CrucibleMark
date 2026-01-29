"""Core scorers for reasoning assets."""

from typing import Tuple


def check_condition(
    condition: bool,
    points: float,
    success_msg: str,
    fail_msg: str,
    partial_condition: bool = False,
    partial_points: float = 0.0,
    partial_msg: str = "",
) -> Tuple[float, str]:
    """Helper to evaluate a scoring condition.

    Args:
        condition: The primary success condition.
        points: Points to award if primary condition is met.
        success_msg: Message for success.
        fail_msg: Message for failure (if neither condition met).
        partial_condition: The partial success condition.
        partial_points: Points for partial success.
        partial_msg: Message for partial success.

    Returns:
        Tuple of (awarded_points, log_message)

    """
    if condition:
        return points, f"✅ {success_msg}"
    if partial_condition:
        return partial_points, f"⚠️ {partial_msg}"
    return 0.0, f"❌ {fail_msg}"
