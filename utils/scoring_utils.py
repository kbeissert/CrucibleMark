"""Scoring calculation utilities for benchmarks."""
from typing import Dict, Any, Optional

def calculate_score_contributions(
    result: Dict[str, Any],
    asset_cfg: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Calculate routine/reasoning score contributions.
    
    This function applies the score_contribution weights from 
    the benchmark config to split a percentage score into 
    routine and reasoning components.
    
    Args:
        result: Test result dict with 'percentage' key
        asset_cfg: Benchmark config with 'score_contribution' key
        
    Returns:
        Updated result dict with:
        - 'routine_contribution': Weighted routine score
        - 'reasoning_contribution': Weighted reasoning score
        
    Example:
        >>> result = {'percentage': 80.0}
        >>> cfg = {'score_contribution': {'routine': 0.7, 'reasoning': 0.3}}
        >>> calculate_score_contributions(result, cfg)
        {'percentage': 80.0, 'routine_contribution': 56.0, 'reasoning_contribution': 24.0}
    """
    if not asset_cfg or "score_contribution" not in asset_cfg:
        return result

    contrib = asset_cfg["score_contribution"]
    score_base = result.get("percentage", 0.0)

    result["routine_contribution"] = round(score_base * contrib.get("routine", 0.0), 2)
    result["reasoning_contribution"] = round(score_base * contrib.get("reasoning", 0.0), 2)

    return result
