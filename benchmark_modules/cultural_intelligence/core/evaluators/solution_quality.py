"""
Solution Quality Evaluator Module.
"""

from typing import Any
from .utils import evaluate_keyword_presence


class SolutionQualityEvaluator:
    """
    Evaluates overall solution quality for cultural intelligence tasks.

    Scoring dimensions:
    - Keyword presence (required terms)
    - Tone consistency
    - Completeness
    """

    # pylint: disable=too-few-public-methods

    @staticmethod
    def score_quality(response: str, criteria: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Score solution quality based on keyword criteria.

        Args:
            response: LLM response text
            criteria: List of quality criteria from asset config

        Returns:
            Dictionary with score and details.
        """
        score = 0.0
        details = []
        response_lower = response.lower()

        for criterion in criteria:
            name = criterion.get("name", "Unknown")
            points = criterion.get("points", 0)
            check_method = criterion.get("check_method", "keyword_presence")

            if check_method == "keyword_presence":
                s, d = evaluate_keyword_presence(
                    response_lower, criterion, points, name
                )
                score += s
                details.append(d)
            else:
                details.append(f"○ {name}: unsupported check_method '{check_method}'")

        return {"score": round(score, 2), "details": details}
