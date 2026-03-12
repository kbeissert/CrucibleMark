"""
Base classes and common functionality for UX Writing evaluators.

This module defines the abstract base class for criterion evaluators
and the issue evaluator logic used across different benchmarks.
"""

import re
from abc import ABC, abstractmethod
from typing import Tuple, List
from utils.similarity import SemanticSimilarity
from ..models import UXCriterion, UXIssue
from ..constants import (
    MIN_SENTENCE_LENGTH,
    SIMILARITY_THRESHOLD,
    DEFAULT_REQUIRED_RATIO,
)


class CriterionEvaluator(ABC):
    """Abstract base class for criterion evaluators."""

    # pylint: disable=too-few-public-methods

    @abstractmethod
    def evaluate(self, response: str, criterion: UXCriterion) -> Tuple[float, str]:
        """
        Evaluates a single criterion against the response.

        Args:
            criterion: The criterion to evaluate.

        Returns:
            Tuple containing (score, explanation_string).
        """


class IssueEvaluator:
    """Evaluates error detection issues using hybrid matching."""

    @staticmethod
    def check_issue_mentioned(
        response_lower: str,
        keywords: List[str],
        required_ratio: float = DEFAULT_REQUIRED_RATIO,
    ) -> bool:
        """
        Prüft ob ein Issue in der Response erwähnt wurde.
        Nutzt Hybrid-Ansatz: String-Matching + Semantic Similarity.

        Args:
            response_lower: Lowercase response text.
            keywords: List of keywords to match.
            required_ratio: Ratio of keywords matched required for success.

        Returns:
            True if issue is considered mentioned/detected.
        """
        # Strip reasoning tags before processing (DeepSeek <think> tags)
        response_lower = re.sub(
            r"<think>.*?</think>", "", response_lower, flags=re.DOTALL
        )

        if not keywords:
            return False

        # 1. WCAG Nummer Check (Regex)
        has_wcag_number = any(re.match(r"\d\.\d\.\d", kw) for kw in keywords)
        if has_wcag_number:
            for kw in keywords:
                if re.match(r"\d\.\d\.\d", kw) and kw in response_lower:
                    return True  # Wenn WCAG Nummer im Text vorkommt -> Treffer

        # 2. String Matching (Keyword Count)
        matches = sum(1 for kw in keywords if kw.lower() in response_lower)
        # required_ratio defaults to 0.6 but can be overridden
        required_matches = max(1, int(len(keywords) * required_ratio))

        if matches >= required_matches:
            return True

        # 3. Semantic Similarity (Fallback)
        query = " ".join(keywords)  # Konstruiere eine Query aus den Keywords

        # Splitte Response in Sätze (grob)
        sentences = [
            s.strip()
            for s in response_lower.split(".")
            if len(s.strip()) > MIN_SENTENCE_LENGTH
        ]

        # Wenn keine Sätze gefunden, nutze Chunks
        if not sentences:
            sentences = [
                response_lower[i : i + 200] for i in range(0, len(response_lower), 200)
            ]

        # Suche besten Match
        # Assuming SemanticSimilarity is available and configured
        try:
            best_score = SemanticSimilarity.find_best_match(query, sentences)
            return best_score > SIMILARITY_THRESHOLD
        except Exception:  # pylint: disable=broad-exception-caught
            # Fallback if similarity check fails (e.g. model not loaded)
            return False

    @classmethod
    def evaluate(cls, response_lower: str, issue: UXIssue) -> Tuple[float, str, bool]:
        """
        Evaluates a specific issue against the response.

        Args:
            response_lower: Lowercase response text.
            issue: The issue to evaluate.

        Returns:
            Tuple: (points_awarded, explanation, is_match).
        """
        # Use issue-specific ratio if present, else default to DEFAULT_REQUIRED_RATIO
        ratio = (
            issue.required_ratio
            if issue.required_ratio is not None
            else DEFAULT_REQUIRED_RATIO
        )
        matched = cls.check_issue_mentioned(
            response_lower, issue.keywords, required_ratio=ratio
        )

        # If inverse_match is True, we want matched to be False for points
        if issue.inverse_match:
            if not matched:
                return (
                    issue.points,
                    f"✓ {issue.issue}: Erfolgreich vermieden ({issue.points}p)",
                    False,
                )
            return 0.0, f"✗ {issue.issue}: Unerwünscht gefunden", True
        if matched:
            return issue.points, f"✓ {issue.issue}: Erkannt ({issue.points}p)", True

        return 0.0, f"✗ {issue.issue}: Nicht erkannt", False
