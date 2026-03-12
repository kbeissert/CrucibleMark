"""
Evaluators for validation rules (Regex, Code presence, Length constraints).
"""

import re
from typing import Tuple
from ..models import UXCriterion
from ..constants import MAX_BUTTON_LENGTH, DEFAULT_MIN_REGEX_MATCHES
from .base import CriterionEvaluator

# pylint: disable=too-few-public-methods


class RegexEvaluator(CriterionEvaluator):
    """
    Evaluates if the response contains matches for a specific regex pattern.
    Useful for checking specific formats like WCAG identifiers (x.x.x).
    """

    def evaluate(self, response: str, criterion: UXCriterion) -> Tuple[float, str]:
        points = criterion.points

        # Fallback to WCAG pattern if not provided, just like original code
        pattern = criterion.check_pattern or r"\d\.\d\.\d"

        matches = re.findall(pattern, response)
        # Assuming count_unique is True based on original code defaults,
        # though original code checked a dict key.
        count = len(set(matches))
        min_required = DEFAULT_MIN_REGEX_MATCHES

        if count >= min_required:
            return points, f"✓ {criterion.name}: {count} Treffer ({points}p)"

        partial = (float(count) / min_required) * points
        return (
            partial,
            f"⚠ {criterion.name}: {count}/{min_required} Treffer ({partial:.1f}p)",
        )


class CodeValidationEvaluator(CriterionEvaluator):
    """
    Evaluates if the response contains required code elements or blocks.
    Checks for presence of specific strings/tokens in code.
    """

    def evaluate(self, response: str, criterion: UXCriterion) -> Tuple[float, str]:
        points = criterion.points
        required = criterion.required_elements
        min_blocks = criterion.min_code_blocks

        total_found = 0
        found_elements = []

        for elem in required:
            count = response.count(elem)
            if count > 0:
                total_found += count
                found_elements.append(f"{elem}({count}x)")

        if total_found >= min_blocks:
            found_summary = ", ".join(found_elements[:3])
            return (
                points,
                f"✓ {criterion.name}: {total_found} Code-Beispiele "
                f"({found_summary}) ({points}p)",
            )

        return (
            0.0,
            f"✗ {criterion.name}: {total_found}/{min_blocks} Code-Beispiele",
        )


class LengthValidationEvaluator(CriterionEvaluator):
    """
    Evaluates if specific elements (like buttons) match length constraints.
    Checks that button labels do not exceed a character limit.
    """

    def evaluate(self, response: str, criterion: UXCriterion) -> Tuple[float, str]:
        points = criterion.points
        # Assuming generic param parsing or usage of additional_params if needed
        # but models.py has specific fields for now or we rely on defaults.
        # Original code used hardcoded MAX_BUTTON_LENGTH default
        max_length = MAX_BUTTON_LENGTH

        button_pattern = r'["\']([^"\']{1,100})["\']'
        buttons = re.findall(button_pattern, response)

        if not buttons:
            return 0.0, f"⚠ {criterion.name}: Keine Button-Labels gefunden"

        too_long = [b for b in buttons if len(b) > max_length]

        if len(too_long) == 0:
            return (
                points,
                f"✓ {criterion.name}: Alle Buttons <{max_length} Zeichen ({points}p)",
            )

        return (
            points * 0.5,
            f"⚠ {criterion.name}: {len(too_long)} Buttons zu lang (z.B. '{too_long[0][:30]}...')",
        )
