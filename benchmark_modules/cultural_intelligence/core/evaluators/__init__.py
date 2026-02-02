"""
Cultural Intelligence Evaluators Facade.

This module provides the main entry point (CulturalIntelligenceEvaluator)
and exposes specialized evaluators for language proficiency, cultural fit,
solution quality, and regional consistency.
"""

from typing import Any, Dict
from pathlib import Path
from .language_proficiency import LanguageProficiencyEvaluator
from .cultural_fit import CulturalFitEvaluator
from .solution_quality import SolutionQualityEvaluator
from .regional_validator import RegionalConsistencyValidator
from .formality_scorer import FormalityScorer
from .legacy import LegacyEvaluator

class CulturalIntelligenceEvaluator:
    """
    Facade for Cultural Intelligence evaluation.
    Maintains v1.0 interface for backward compatibility.
    """

    # pylint: disable=too-few-public-methods

    def __init__(self, asset: Dict[str, Any], asset_path: Path = None):
        self.asset = asset
        self.asset_path = asset_path or Path("")

    def score_response(self, response: str) -> dict:
        """
        Evaluate Cultural Intelligence response.

        Scoring Categories:
        1. Language Proficiency (40 points) - German markers, formality
        2. Cultural Fit (30 points) - Regional expressions, politeness
        3. Solution Quality (30 points) - Keyword presence

        Args:
            response: LLM response string

        Returns:
            dict with total_score, category_scores, details, metadata
        """
        if not response or response.startswith("ERROR:"):
            return self._create_error_score("Invalid or error response")

        # Legacy Dispatch
        if "scoring" not in self.asset:
            # Delegate to legacy evaluator
            legacy = LegacyEvaluator(self.asset)
            return legacy.score_response(response)

        scoring_config = self.asset["scoring"]
        total_possible = scoring_config.get("total_points", 100)
        category_scores = {}
        details = []
        total_achieved = 0.0

        # ===== KATEGORIE 1: Language Proficiency (40 Punkte) =====
        if "language_proficiency" in scoring_config:
            lang_result = LanguageProficiencyEvaluator.score_proficiency(
                response,
                scoring_config["language_proficiency"]["criteria"]
            )
            category_scores["language_proficiency"] = {
                "achieved": lang_result["score"],
                "max": scoring_config["language_proficiency"]["weight"]
            }
            details.extend(lang_result["details"])
            total_achieved += lang_result["score"]

        # ===== KATEGORIE 2: Cultural Fit (30 Punkte) =====
        if "cultural_fit" in scoring_config:
            cultural_result = CulturalFitEvaluator.score_cultural_fit(
                response,
                scoring_config["cultural_fit"]["criteria"]
            )
            category_scores["cultural_fit"] = {
                "achieved": cultural_result["score"],
                "max": scoring_config["cultural_fit"]["weight"]
            }
            details.extend(cultural_result["details"])
            total_achieved += cultural_result["score"]

        # ===== KATEGORIE 3: Solution Quality (30 Punkte) =====
        if "solution_quality" in scoring_config:
            quality_result = SolutionQualityEvaluator.score_quality(
                response,
                scoring_config["solution_quality"]["criteria"]
            )
            category_scores["solution_quality"] = {
                "achieved": quality_result["score"],
                "max": scoring_config["solution_quality"]["weight"]
            }
            details.extend(quality_result["details"])
            total_achieved += quality_result["score"]

        # Metadata collection (using get() for safety if category skipped)
        metadata = {
            "response_length": len(response),
            "word_count": len(response.split())
        }
        if "language_proficiency" in category_scores:
            metadata.update(lang_result.get("metadata", {}))
        if "cultural_fit" in category_scores:
            metadata.update(cultural_result.get("metadata", {}))

        # NEW: Regional consistency check
        regional_check = RegionalConsistencyValidator.validate_consistency(response)
        metadata["regional_consistency"] = regional_check["is_consistent"]
        metadata["regional_violations"] = regional_check["violations"]
        metadata["dominant_region"] = regional_check["dominant_region"]

        # NEW: Enhanced formality scoring
        formality = FormalityScorer.calculate_formality(response)
        metadata["formality"] = formality

        return {
            "status": "success",
            "total_score": round(total_achieved, 2),
            "max_score": total_possible,
            "percentage": round((total_achieved / total_possible) * 100, 2),
            "category_scores": category_scores,
            "details": details,
            "metadata": metadata
        }

    def _create_error_score(self, error_msg: str) -> dict:
        """Create error score for invalid responses."""
        return {
            "status": "error",
            "total_score": 0,
            "max_score": 100,
            "percentage": 0,
            "category_scores": {
                "language_proficiency": {"achieved": 0, "max": 40},
                "cultural_fit": {"achieved": 0, "max": 30},
                "solution_quality": {"achieved": 0, "max": 30}
            },
            "details": [error_msg],
            "metadata": {"error": error_msg}
        }

__all__ = [
    "CulturalIntelligenceEvaluator",
    "LanguageProficiencyEvaluator",
    "CulturalFitEvaluator",
    "SolutionQualityEvaluator",
    "RegionalConsistencyValidator",
    "FormalityScorer"
]
