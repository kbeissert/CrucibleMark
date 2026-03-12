"""
Cultural Fit Evaluator Module.
"""

from typing import List, Dict, Any
from benchmark_modules.cultural_intelligence.core.constants import (
    REGIONAL_EXPRESSIONS,
    POLITENESS_MARKERS,
)
from .utils import evaluate_keyword_presence


class CulturalFitEvaluator:
    """
    Evaluates cultural appropriateness for German-speaking contexts.

    Scoring dimensions:
    - Regional awareness (DE/AT/CH)
    - Politeness markers
    - Context-appropriate formality
    """

    # pylint: disable=too-few-public-methods

    @staticmethod
    def score_cultural_fit(
        response: str, criteria: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Score cultural fit based on regional and politeness markers.

        Args:
            response: LLM response text
            criteria: List of cultural criteria from asset config

        Returns:
            Dictionary containing score, details, and metadata.
        """
        score = 0.0
        details = []
        response_lower = response.lower()

        # Count politeness markers
        politeness_count = sum(
            1 for marker in POLITENESS_MARKERS if marker in response_lower
        )

        # Detect regional markers
        regional_markers = CulturalFitEvaluator._detect_regional_markers(response_lower)
        if regional_markers:
            dominant_region = max(regional_markers, key=regional_markers.get)
        else:
            dominant_region = "unknown"

        # Score each criterion
        for criterion in criteria:
            name = criterion.get("name", "Unknown")
            points = criterion.get("points", 0)
            check_method = criterion.get("check_method", "keyword_presence")

            if check_method == "politeness_count":
                min_count = criterion.get("min_count", 1)
                if politeness_count >= min_count:
                    score += points
                    details.append(
                        f"✓ {name}: {politeness_count} politeness markers (+{points}p)"
                    )
                else:
                    details.append(
                        f"○ {name}: {politeness_count}/{min_count} politeness markers"
                    )

            elif check_method == "regional_awareness":
                expected_region = criterion.get("expected_region", "de")
                if dominant_region == expected_region:
                    score += points
                    details.append(
                        f"✓ {name}: {dominant_region.upper()} markers detected (+{points}p)"
                    )
                else:
                    details.append(
                        f"○ {name}: Expected {expected_region.upper()}, "
                        f"got {dominant_region.upper()}"
                    )

            elif check_method == "keyword_presence":
                s, d = evaluate_keyword_presence(
                    response_lower, criterion, points, name
                )
                score += s
                details.append(d)

        return {
            "score": round(score, 2),
            "details": details,
            "metadata": {
                "politeness_marker_count": politeness_count,
                "regional_markers": list(regional_markers.keys()),
                "dominant_region": dominant_region,
            },
        }

    @staticmethod
    def _detect_regional_markers(response_lower: str) -> Dict[str, int]:
        """
        Detect regional markers (DE/AT/CH) in response.

        Returns:
            {"de": count, "at": count, "ch": count}
        """
        regional_counts = {"de": 0, "at": 0, "ch": 0}

        for region, categories in REGIONAL_EXPRESSIONS.items():
            for _, terms in categories.items():
                for term in terms:
                    if term in response_lower:
                        regional_counts[region] += 1

        return {k: v for k, v in regional_counts.items() if v > 0}
