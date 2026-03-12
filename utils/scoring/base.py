"""
Base interfaces for Scoring components.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseScorer(ABC):
    """
    Abstract Base Class for all Scoring Mechanisms.
    Ensures every scorer implements a standardized scoring method.
    """

    @abstractmethod
    def score_response(
        self,
        response: str,
        asset: Dict[str, Any],
        **kwargs,  # Context, previous messages, etc.
    ) -> Dict[str, Any]:
        """
        Scores a text response against the provided asset configuration.
        """
        pass

    def calculate_score_contributions(
        self, result: Dict[str, Any], asset_cfg: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate routine/reasoning score contributions.
        Moves logic from old scoring_utils.py to BaseScorer for reuse.
        """
        if not asset_cfg or "score_contribution" not in asset_cfg:
            return result

        contrib = asset_cfg["score_contribution"]
        score_base = result.get("percentage", 0.0)
        # If percentage is missing, maybe calculate from total/max?
        # For now assume result has percentage or calculate it
        if "percentage" not in result and result.get("max_score", 0) > 0:
            score_base = (
                result.get("total_score", 0) / result.get("max_score", 1)
            ) * 100

        result["routine_contribution"] = round(
            score_base * contrib.get("routine", 0.0), 2
        )
        result["reasoning_contribution"] = round(
            score_base * contrib.get("reasoning", 0.0), 2
        )

        return result
