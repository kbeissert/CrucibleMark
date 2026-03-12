"""
Formality Scorer module.

Provides detailed formality scoring on a continuous scale.
"""

# pylint: disable=relative-beyond-top-level
from ..constants import FORMAL_MARKERS, INFORMAL_MARKERS


class FormalityScorer:
    """
    Measures formality level on a continuous scale.

    Unlike binary Sie/Du detection, this provides a 0.0-1.0 score
    based on multiple formality indicators.
    """

    # pylint: disable=too-few-public-methods

    @staticmethod
    def calculate_formality(response: str) -> dict:
        """
        Calculate formality score (0.0 = very informal, 1.0 = very formal).

        Returns:
            {
                "formality_score": float,  # 0.0-1.0
                "formality_level": str,    # "very_informal".."very_formal"
                "formal_count": int,
                "informal_count": int,
                "indicators": dict
            }
        """
        response_lower = response.lower()

        formal_indicators = []
        informal_indicators = []

        # Count formal markers
        for category, markers in FORMAL_MARKERS.items():
            for marker in markers:
                if marker in response_lower:
                    formal_indicators.append(f"{marker} ({category})")

        # Count informal markers
        for category, markers in INFORMAL_MARKERS.items():
            for marker in markers:
                if marker in response_lower:
                    informal_indicators.append(f"{marker} ({category})")

        formal_count = len(formal_indicators)
        informal_count = len(informal_indicators)
        total_markers = formal_count + informal_count

        if total_markers == 0:
            formality_score = 0.5  # Neutral (no markers)
            formality_level = "neutral"
        else:
            formality_score = formal_count / total_markers

            # Classify formality level
            if formality_score >= 0.9:
                formality_level = "very_formal"
            elif formality_score >= 0.7:
                formality_level = "formal"
            elif formality_score <= 0.1:
                formality_level = "very_informal"
            elif formality_score <= 0.3:
                formality_level = "informal"
            else:
                formality_level = "neutral"

        return {
            "formality_score": round(formality_score, 2),
            "formality_level": formality_level,
            "formal_count": formal_count,
            "informal_count": informal_count,
            "indicators": {
                "formal": formal_indicators,
                "informal": informal_indicators,
            },
        }
