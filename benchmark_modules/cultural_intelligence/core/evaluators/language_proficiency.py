"""
Language Proficiency Evaluator Module.
"""
from typing import Tuple, List, Dict, Any
from benchmark_modules.cultural_intelligence.core.constants import (
    GERMAN_WORD_MARKERS,
    FORMAL_MARKERS,
    INFORMAL_MARKERS,
    MIN_GERMAN_WORDS,
    FORMALITY_THRESHOLD
)
from .utils import evaluate_keyword_presence

class LanguageProficiencyEvaluator:
    """
    Evaluates German language proficiency in LLM responses.

    Scoring dimensions:
    - German word markers (presence of common German words)
    - Formality level (Sie vs Du)
    - Grammar correctness (bonus points)
    """

    # pylint: disable=too-few-public-methods

    @staticmethod
    def score_proficiency(response: str, criteria: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Score language proficiency based on German markers.

        Args:
            response: LLM response text
            criteria: List of proficiency criteria from asset config

        Returns:
            Dictionary containing score, details, and metadata.
        """
        score = 0.0
        details = []
        response_lower = response.lower()

        german_word_count = LanguageProficiencyEvaluator._count_german_words(response_lower)

        for criterion in criteria:
            points = criterion.get("points", 0)
            check_method = criterion.get("check_method", "keyword_presence")
            
            if check_method == "german_word_count":
                s, d = LanguageProficiencyEvaluator._check_german_words(
                    german_word_count, criterion, points
                )
                score += s
                details.append(d)

            elif check_method == "formality_check":
                s, d = LanguageProficiencyEvaluator._check_formality(
                    response_lower, criterion, points
                )
                score += s
                details.append(d)

            elif check_method == "keyword_presence":
                name = criterion.get("name", "Unknown")
                s, d = evaluate_keyword_presence(response_lower, criterion, points, name)
                score += s
                details.append(d)

        formality_level, formal_ratio = LanguageProficiencyEvaluator._detect_formality(
            response_lower
        )

        return {
            "score": round(score, 2),
            "details": details,
            "metadata": {
                "german_word_count": german_word_count,
                "formality_level": formality_level,
                "formal_ratio": round(formal_ratio, 2)
            }
        }

    @staticmethod
    def _count_german_words(response_lower: str) -> int:
        """Count presence of common German words."""
        german_words_found = [
            word for word in GERMAN_WORD_MARKERS 
            if word in response_lower
        ]
        return len(german_words_found)

    @staticmethod
    def _check_german_words(
        count: int, criterion: Dict[str, Any], points: float
    ) -> Tuple[float, str]:
        """Check if german word count meets minimum."""
        name = criterion.get("name", "Unknown")
        min_count = criterion.get("min_count", MIN_GERMAN_WORDS)
        if count >= min_count:
            return points, f"✓ {name}: {count} German words found (+{points}p)"
        return 0.0, f"○ {name}: {count}/{min_count} German words"

    @staticmethod
    def _check_formality(
        response_lower: str, criterion: Dict[str, Any], points: float
    ) -> Tuple[float, str]:
        """Check if formality matches expected level."""
        name = criterion.get("name", "Unknown")
        formality_level, _ = LanguageProficiencyEvaluator._detect_formality(response_lower)
        expected_level = criterion.get("expected_level", "formal")

        if formality_level == expected_level:
            return points, f"✓ {name}: {formality_level.capitalize()} detected (+{points}p)"
        return 0.0, f"○ {name}: Expected {expected_level}, got {formality_level}"

    @staticmethod
    def _detect_formality(response_lower: str) -> Tuple[str, float]:
        """
        Detect formality level based on pronoun usage.

        Returns:
            (formality_level, formal_ratio)
        """
        formal_count = sum(
            1 for marker_list in FORMAL_MARKERS.values()
            for marker in marker_list
            if marker in response_lower
        )

        informal_count = sum(
            1 for marker_list in INFORMAL_MARKERS.values()
            for marker in marker_list
            if marker in response_lower
        )

        total_markers = formal_count + informal_count

        if total_markers == 0:
            return ("unknown", 0.5)

        formal_ratio = formal_count / total_markers

        if formal_ratio >= FORMALITY_THRESHOLD:
            return ("formal", formal_ratio)
        if formal_ratio <= (1 - FORMALITY_THRESHOLD):
            return ("informal", formal_ratio)
        return ("mixed", formal_ratio)
