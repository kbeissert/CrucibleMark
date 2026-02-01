"""
Evaluators for structural elements (tables, formatting).
"""
from typing import Tuple
from ..models import UXCriterion
from ..constants import MIN_TABLE_COLUMNS
from .base import CriterionEvaluator

# pylint: disable=too-few-public-methods

class MarkdownTableEvaluator(CriterionEvaluator):
    """
    Evaluates if the response contains a valid Markdown table.
    """

    def evaluate(self, response: str, criterion: UXCriterion) -> Tuple[float, str]:
        """
        Checks for table syntax and minimum row count.

        Args:
            response: LLM response.
            criterion: Criterion configuration.

        Returns:
            Score and explanation.
        """
        points = criterion.points
        has_table = "|" in response and "-" in response

        # Count rows that look like table rows (have enough pipes)
        # Note: Original code used global MIN_TABLE_COLUMNS
        table_rows = len(
            [
                line
                for line in response.split("\n")
                if line.count("|") >= MIN_TABLE_COLUMNS
            ]
        )
        min_rows = criterion.min_rows

        if has_table and table_rows >= min_rows:
            return points, f"✓ {criterion.name}: {table_rows} Zeilen ({points}p)"

        if has_table:
            # Partial credit logic from original code
            partial = (float(table_rows) / min_rows) * points
            return (
                partial,
                f"⚠ {criterion.name}: {table_rows}/{min_rows} Zeilen ({partial:.1f}p)",
            )

        return 0.0, f"✗ {criterion.name}: Keine Tabelle gefunden"


class StructureValidationEvaluator(CriterionEvaluator):
    """
    Evaluates if specific structural text elements are present.
    """

    def evaluate(self, response: str, criterion: UXCriterion) -> Tuple[float, str]:
        """
        Checks if required structural strings are found.

        Args:
            response: LLM response.
            criterion: Criterion configuration.

        Returns:
            Score and explanation.
        """
        points = criterion.points
        required_structure = criterion.required_structure

        found = [
            elem for elem in required_structure if elem.lower() in response.lower()
        ]

        if len(found) == len(required_structure):
            return (
                points,
                f"✓ {criterion.name}: Alle Strukturelemente vorhanden ({points}p)",
            )

        missing = set(required_structure) - set(found)
        return 0.0, f"✗ {criterion.name}: Fehlende Elemente: {', '.join(missing)}"
