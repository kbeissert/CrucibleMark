"""
Scoring Utilities.
Shared helper functions for scoring calculations.
"""

from typing import Any, Dict, Optional


def calculate_score_contributions(
    result: Dict[str, Any],
    asset_cfg: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Calculate routine/reasoning score contributions.
    """
    if not asset_cfg or "score_contribution" not in asset_cfg:
        return result

    contrib = asset_cfg["score_contribution"]
    score_base = result.get("percentage", 0.0)
    
    # Validation/Calculation if percentage missing
    if "percentage" not in result and result.get("max_score", 0) > 0:
            score_base = (result.get("total_score", 0) / result.get("max_score", 1)) * 100

    result["routine_contribution"] = round(score_base * contrib.get("routine", 0.0), 2)
    result["reasoning_contribution"] = round(score_base * contrib.get("reasoning", 0.0), 2)

    return result
