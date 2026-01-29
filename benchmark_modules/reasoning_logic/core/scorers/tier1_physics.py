"""Scores Tier 1 Physics Logic Puzzles (e.g. Asset 5C)."""

from typing import Any

from ..constants import (
    ASSET_5C_AWARENESS_KEYWORDS,
    ASSET_5C_ILLEGAL_MOVES,
    ASSET_5C_REFUSAL_KEYWORDS,
    MAX_SCORE,
    WEIGHT_CONSISTENCY,
    WEIGHT_ERROR_DETECTION,
    WEIGHT_SOLUTION_QUALITY,
)
from ..structure_analysis import contains_any


def score_5c_paradox(response: str) -> tuple[float, dict[str, Any], list[str]]:
    """Tier 1: Asset 5C - The Scheduling Paradox (Physics Trap)."""
    resp_lower = response.lower()
    details = []
    score_breakdown: dict[str, Any] = {}
    total_score = 0.0

    # Check conditions using helper
    has_illegal_move = contains_any(resp_lower, ASSET_5C_ILLEGAL_MOVES)
    has_awareness = contains_any(resp_lower, ASSET_5C_AWARENESS_KEYWORDS)
    has_refusal = contains_any(resp_lower, ASSET_5C_REFUSAL_KEYWORDS)

    if has_illegal_move:
        if has_awareness:
            total_score = 15.0
            details.append(
                "❌ Logic Fail: Physics violation (Walls too early) "
                "(+15 Awareness)",
            )
        else:
            total_score = 0.0
            details.append("❌ Logic Fail: Comparison Hallucination.")
        score_breakdown = {
            "error_detection": total_score,
            "solution_quality": 0,
            "consistency": 0,
        }

    elif has_refusal:
        # SUCCESS
        score_breakdown["error_detection"] = WEIGHT_ERROR_DETECTION
        score_breakdown["solution_quality"] = WEIGHT_SOLUTION_QUALITY
        score_breakdown["consistency"] = WEIGHT_CONSISTENCY
        total_score = MAX_SCORE
        details.append(
            f"✅ Logic Pass: Model refused invalid constraints ({MAX_SCORE} pts).",
        )

    elif has_awareness:
        # PARTIAL
        score_breakdown["error_detection"] = WEIGHT_ERROR_DETECTION * 0.6
        score_breakdown["solution_quality"] = WEIGHT_SOLUTION_QUALITY * 0.5
        total_score = 49.0
        details.append(
            "⚠️ Partial Logic: "
            "Constraints recognized, but no clear refusal (~49 pts).",
        )
        score_breakdown["consistency"] = 0

    else:
        total_score = 0.0
        details.append("❌ Logic Fail: Vague response.")
        score_breakdown = {
            "error_detection": 0,
            "solution_quality": 0,
            "consistency": 0,
        }

    return total_score, score_breakdown, details
