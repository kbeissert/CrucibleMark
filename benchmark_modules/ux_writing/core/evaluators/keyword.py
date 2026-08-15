"""
Evaluators for keyword presence and absence.
"""

from ..models import UXCriterion
from .base import CriterionEvaluator

# pylint: disable=too-few-public-methods


class KeywordPresenceEvaluator(CriterionEvaluator):
    """
    Evaluates if specific positive keywords are present in the response.
    """

    def evaluate(self, response: str, criterion: UXCriterion) -> tuple[float, str]:
        """
        Checks if required keywords are present in the response.

        Args:
            response: LLM response.
            criterion: Criterion configuration.

        Returns:
            Score and explanation.
        """
        points = criterion.points
        keywords = criterion.keywords
        # Simple containment check
        found_keywords = [kw for kw in keywords if kw.lower() in response.lower()]
        min_required = criterion.min_keywords

        if len(found_keywords) >= min_required:
            display_kws = ", ".join(found_keywords[:3])
            return (
                points,
                f"✓ {criterion.name}: {len(found_keywords)}/{min_required} "
                f"({display_kws}) ({points}p)",
            )
        display_kws = ", ".join(found_keywords) if found_keywords else "keine"
        return (
            0.0,
            f"✗ {criterion.name}: {len(found_keywords)}/{min_required} ({display_kws})",
        )


class KeywordAbsenceEvaluator(CriterionEvaluator):
    """
    Evaluates if forbidden keywords are absent from the response.
    """

    def evaluate(self, response: str, criterion: UXCriterion) -> tuple[float, str]:
        """
        Checks if forbidden keywords are absent from the response.

        Args:
            response: LLM response.
            criterion: Criterion configuration.

        Returns:
            Score and explanation.
        """
        points = criterion.points
        forbidden = criterion.forbidden_keywords
        found_forbidden = [kw for kw in forbidden if kw.lower() in response.lower()]
        max_violations = criterion.max_violations

        if len(found_forbidden) <= max_violations:
            return (
                points,
                f"✓ {criterion.name}: Keine verbotenen Begriffe ({points}p)",
            )
        return (
            0.0,
            f"✗ {criterion.name}: Verbotene Begriffe gefunden: {', '.join(found_forbidden)}",
        )
