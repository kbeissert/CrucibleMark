"""
Scoring Utilities.
Shared helper functions for scoring calculations.
"""

from typing import Any

from utils.model_utils import _safe_name


def normalize_model_name(s: str) -> str:
    """Canonical model name normalization for CSV/dict lookups.

    Delegiert an ``utils.model_utils._safe_name`` (SSoT für Card-Filenames)
    und normalisiert zusätzlich auf lower-case. Wird von generate_review.py
    und score_calculator.py verwendet.
    """
    return _safe_name(s).lower()


def calculate_score_contributions(
    result: dict[str, Any], asset_cfg: dict[str, Any] | None
) -> dict[str, Any]:
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
    result["reasoning_contribution"] = round(
        score_base * contrib.get("reasoning", 0.0), 2
    )

    return result


def calculate_hybrid_score(
    regex_score: float,
    judge_score: float | None,
    asset_config: dict[str, Any] | None,
    module_config: dict[str, Any] | None,
    judge_enabled: bool,
) -> float:
    """
    Formel A (Judge aktiv):
      Gewichte aus asset_config.scoring_weights
      -> Fallback: module_config.scoring.fallback_weights
      -> Fallback: 50/50

    Formel B (kein Judge):
      return regex_score unverändert
    """
    if not judge_enabled or judge_score is None:
        # Formel B - Rückwärtskompatibel, kein Breaking Change
        return regex_score

    # Configurations might be None
    ac = asset_config or {}
    mc = module_config or {}

    # Gewichte laden: Asset -> Modul-Fallback -> Hard Default
    # Use explicit None check — an empty dict {} is a valid "no weights" signal,
    # not a "not configured" signal. The `or` chain would skip {} (falsy).
    _asset_w = ac.get("scoring_weights")
    _module_w = mc.get("scoring", {}).get("fallback_weights")
    weights = _asset_w if _asset_w is not None else (_module_w if _module_w is not None else {"regex": 0.50, "judge": 0.50})

    regex_w = weights.get("regex", 0.50)
    judge_w = weights.get("judge", 0.50)

    # Normalisierung falls Summe != 1
    total = regex_w + judge_w
    if total != 1.0 and total > 0.0:
        regex_w /= total
        judge_w /= total

    return (regex_score * regex_w) + (judge_score * judge_w)
