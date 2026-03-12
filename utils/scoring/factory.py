"""
Scorer Factory.
Provides easy access to Scorer instances.
"""

from typing import Dict, Type
from .base import BaseScorer
from .regex_scorer import RegexScorer
from .llm_scorer import LLMScorer


class ScorerFactory:
    """Factory class to retrieve Scorer instances by name."""

    _scorers: Dict[str, Type[BaseScorer]] = {
        "regex": RegexScorer,
        "rule": RegexScorer,  # Alias
        "llm": LLMScorer,
        "ai": LLMScorer,  # Alias
    }

    @classmethod
    def get_scorer(cls, method_name: str) -> BaseScorer:
        """
        Returns a scorer instance for the given method name.

        Args:
            method_name: "regex", "llm", etc.

        Returns:
            An instance of a BaseScorer subclass.

        Raises:
            ValueError: If method is unknown.
        """
        scorer_cls = cls._scorers.get(method_name.lower())
        if not scorer_cls:
            # Fallback or Error?
            # For now, default to Regex for backward compatibility or raise
            raise ValueError(f"Unknown scoring method: {method_name}")

        return scorer_cls()


def get_scorer(method_name: str) -> BaseScorer:
    """Helper function alias for ScorerFactory.get_scorer"""
    return ScorerFactory.get_scorer(method_name)
