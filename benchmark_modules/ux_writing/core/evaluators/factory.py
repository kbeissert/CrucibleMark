"""
Factory for creating evaluator instances.
"""
from .base import CriterionEvaluator
from .keyword import KeywordPresenceEvaluator, KeywordAbsenceEvaluator
from .structure import MarkdownTableEvaluator, StructureValidationEvaluator
from .validation import RegexEvaluator, CodeValidationEvaluator, LengthValidationEvaluator

class EvaluatorFactory:
    """
    Factory class to retrieve specific CriterionEvaluator implementations
    based on the check method name.
    """
    # pylint: disable=too-few-public-methods

    _evaluators = {
        "keyword_presence": KeywordPresenceEvaluator(),
        "keyword_absence": KeywordAbsenceEvaluator(),
        "markdown_table_validation": MarkdownTableEvaluator(),
        "structure_validation": StructureValidationEvaluator(),
        "regex": RegexEvaluator(),
        "code_validation": CodeValidationEvaluator(),
        "length_validation": LengthValidationEvaluator(),
        # Map readability to keyword presence for now as per original code logic usually
        # but let's see if we need a specific one.
        # Original code mapped "readability_score" -> score_readability which used kw search
        "readability_score": KeywordPresenceEvaluator(),
        "readability_mention": KeywordPresenceEvaluator(),
    }

    @classmethod
    def get_evaluator(cls, check_method: str) -> CriterionEvaluator:
        """
        Returns the evaluator instance for the given method name.

        Args:
            check_method: Name of the evaluation method.

        Returns:
            An instance of CriterionEvaluator.
        """
        return cls._evaluators.get(check_method, KeywordPresenceEvaluator())
