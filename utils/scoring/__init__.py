"""
Scoring Package for CrucibleMark.
Provides a unified interface for different scoring strategies (Regex, LLM, Rubric, etc.)
"""

from .base import BaseScorer
from .regex_scorer import RegexScorer
# from .llm_scorer import LLMScorer  # Coming soon
# from .rubric_scorer import RubricScorer # Migration target
