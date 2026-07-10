"""
Scoring Helper Methods.
Contains all check methods (regex, keyword, semantic, etc.) used by various Scorers.
"""

from typing import Any
import re
from utils.similarity import SemanticSimilarity


class ScoringHelpers:
    """Collection of scoring methods for different criterion types."""

    def __init__(self) -> None:
        self.similarity_engine = SemanticSimilarity()

    def score_regex(self, text: str, criterion: dict[str, Any]) -> tuple[float, str]:
        """Scores based on regex pattern matching."""
        pattern = criterion.get("pattern", "")
        points = criterion.get("points", 0)
        negate = criterion.get("negate", False)

        found = bool(re.search(pattern, text, re.MULTILINE | re.IGNORECASE))
        if negate:
            if not found:
                return (
                    points,
                    f"✓ {criterion.get('description')}: Kein unerwünschtes Muster gefunden",
                )
            return (
                0.0,
                f"✗ {criterion.get('description')}: Unerwünschtes Muster gefunden",
            )
        if found:
            return points, f"✓ {criterion.get('description')}"
        return 0.0, f"✗ {criterion.get('description')} nicht gefunden"

    def score_keyword_presence(
        self, text_lower: str, criterion: dict[str, Any]
    ) -> tuple[float, str]:
        """Scores based on keyword presence."""
        keywords = [k.lower() for k in criterion.get("keywords", [])]
        points = criterion.get("points", 0)
        found = any(k in text_lower for k in keywords)
        if found:
            return points, f"✓ {criterion.get('description')}"
        return 0.0, f"✗ {criterion.get('description')} (-{points}p)"

    def score_list_detection(
        self, text_lower: str, criterion: dict[str, Any]
    ) -> tuple[float, str]:
        """Alias for keyword_presence."""
        return self.score_keyword_presence(text_lower, criterion)

    def score_code_validation(
        self, text: str, criterion: dict[str, Any]
    ) -> tuple[float, str]:
        """Validates code structure and required elements."""
        required_elements = criterion.get("required_elements", [])
        points = criterion.get("points", 0)
        missing = [el for el in required_elements if el not in text]
        if not missing:
            return points, f"✓ {criterion.get('description')}"
        return (
            0.0,
            f"✗ {criterion.get('description')}: Fehlende Elemente: {', '.join(missing)}",
        )

    def score_markdown_table_validation(
        self, text: str, criterion: dict[str, Any]
    ) -> tuple[float, str]:
        """Validates markdown table structure."""
        lines = text.split("\n")
        table_lines = [
            line for line in lines if "|" in line and len(line.split("|")) > 2
        ]
        points = criterion.get("points", 0)
        if len(table_lines) >= criterion.get("min_rows", 3):
            return points, f"✓ {criterion.get('description')}"
        return 0.0, "✗ Tabelle nicht erkannt oder zu klein"

    def score_semantic_similarity(
        self, text: str, criterion: dict[str, Any]
    ) -> tuple[float, str]:
        """Calculates semantic similarity to reference text."""
        reference = criterion.get("reference_text", "")
        threshold = criterion.get("threshold", 0.7)
        points = criterion.get("points", 0)
        score = self.similarity_engine.calculate_similarity(text, reference)
        if score >= threshold:
            return points, f"✓ Inhaltliche Übereinstimmung ({score:.2f})"
        return 0.0, f"✗ Inhalt weicht ab ({score:.2f} < {threshold})"
