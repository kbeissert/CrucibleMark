"""
Facade for Documentation Quality evaluation.
Handles orchestration of specialized sub-evaluators.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import re

from ..constants import TIER_THRESHOLDS
from .semantic_matcher import SemanticMatcher
from .tiered_scoring import TieredScoringEngine
from .solution_quality import SolutionQualityEvaluator
from .structure_validator import StructureValidator
from .readability_scorer import ReadabilityScorer
from .completeness_checker import CompletenessChecker


class DocumentationEvaluator:
    """
    Facade for Documentation Quality evaluation.
    Maintains v1.0 interface for backward compatibility while orchestrating
    specialized sub-evaluators.
    """

    # pylint: disable=too-few-public-methods

    def __init__(self, asset: Dict[str, Any], asset_path: Optional[Path] = None):
        self.asset = asset
        self.asset_path = asset_path or Path("")

        # Extract asset_id
        if "metadata" in asset and "id" in asset["metadata"]:
            self.asset_id = asset["metadata"]["id"]
        else:
            self.asset_id = self.asset_path.stem

    def score_response(self, response: str) -> dict:
        """
        Orchestrates scoring process using specialized engines.

        Args:
            response: LLM response string.

        Returns:
            Dictionary containing score results and metadata.
        """
        # Clean reasoning tags (e.g. DeepSeek <think> or <thought>)
        clean_response = self._clean_reasoning_tags(response)

        if (
            not clean_response
            or clean_response.startswith("ERROR:")
            or clean_response.strip() == ""
        ):
            return self._create_error_score("Invalid or error response")

        scoring_config = self.asset["scoring"]
        total_possible = scoring_config["total_points"]

        category_scores: Dict[str, Any] = {}
        details: List[str] = []
        violations: List[str] = []
        total_achieved: float = 0.0

        response_lower = clean_response.lower()

        # 1. Error Detection (Delegated to TieredScoringEngine)
        ed_score, ed_details, ed_violations = self._score_error_detection(
            response_lower, scoring_config["error_detection"]
        )
        category_scores["error_detection"] = {
            "achieved": float(ed_score),
            "max": float(scoring_config["error_detection"]["weight"]),
        }
        details.extend(ed_details)
        violations.extend(ed_violations)
        total_achieved += ed_score

        # 2. Solution Quality (Delegated to SolutionQualityEvaluator)
        sq_score, sq_details = self._score_solution_quality(
            response_lower, scoring_config["solution_quality"]
        )
        category_scores["solution_quality"] = {
            "achieved": float(sq_score),
            "max": float(scoring_config["solution_quality"]["weight"]),
        }
        details.extend(sq_details)
        total_achieved += sq_score

        # Phase 2: Advanced Validators (Structure, Readability, Completeness)
        # Use CLEAN response for structure check
        adv_results = self._run_advanced_validators(clean_response, details, violations)

        return {
            "status": "success",
            "total_score": round(total_achieved, 2),
            "max_score": total_possible,
            "percentage": round((total_achieved / total_possible) * 100, 2),
            "category_scores": category_scores,
            "details": details,
            "violations": violations,
            "metadata": {
                "response_length": len(clean_response),
                "word_count": len(clean_response.split()),
                **adv_results,
            },
        }

    def _clean_reasoning_tags(self, response: str) -> str:
        """Removes <think>...</think> blocks from reasoning models."""
        if not response:
            return ""
        cleaned = response
        # Supporting multiple variants
        tags = ["think", "thought", "reasoning"]
        for tag in tags:
            pattern = f"<{tag}>.*?</{tag}>"
            cleaned = re.sub(pattern, "", cleaned, flags=re.DOTALL)
        return cleaned.strip()

    def _run_advanced_validators(
        self, response: str, details: List[str], violations: List[str]
    ) -> Dict[str, Any]:
        """Runs Phase 2 validators: Structure, Readability, Completeness."""
        doc_type = self.asset.get("metadata", {}).get("doc_type", "readme")
        results = {"doc_type": doc_type}

        # Structure Validation
        structure = StructureValidator.validate_markdown_structure(response, doc_type)
        if not structure["is_valid"]:
            violations.extend(structure["violations"])
        results["structure"] = structure["stats"]
        results["structure_violations"] = structure["violations"]

        # Completeness Check
        completeness = CompletenessChecker.check_completeness(response, doc_type)
        for missing in completeness["missing_sections"]:
            violations.append(f"✗ Missing required section: {missing}")
        results["completeness_score"] = completeness["score"]

        # Readability (Conditional)
        readability = None
        if doc_type in ["setup_guide", "tutorial"]:
            readability = ReadabilityScorer.calculate_readability(response)
            if readability and readability["flesch_reading_ease"] > 60:
                details.append("✓ Readability: Good (Flesch > 60)")
        results["readability"] = readability

        return results

    def _score_error_detection(self, response: str, config: dict) -> tuple:
        """Delegates error detection to TieredScoringEngine."""
        score: float = 0.0
        details = []
        violations = []

        tier_configs = {
            "labeled": ("labeled_issues", TIER_THRESHOLDS["labeled"]),
            "standard": ("standard_issues", TIER_THRESHOLDS["standard"]),
            "advanced": ("advanced_issues", TIER_THRESHOLDS["advanced"]),
            "expert": ("expert_issues", TIER_THRESHOLDS["expert"]),
        }

        engine = TieredScoringEngine(self.asset_id)

        for tier_name, (tier_key, default_threshold) in tier_configs.items():
            tier_issues = config.get(tier_key, [])

            tier_score, tier_details, tier_violations = engine.score_tier(
                response, tier_issues, tier_name.title(), default_threshold
            )

            score += tier_score
            details.extend(tier_details)
            violations.extend(tier_violations)

        return round(score, 2), details, violations

    def _score_solution_quality(self, response: str, config: dict) -> tuple:
        """Delegates solution quality to SolutionQualityEvaluator."""
        criteria = config.get("criteria", [])
        return SolutionQualityEvaluator.score_criteria(response, criteria)

    def _create_error_score(self, error_msg: str) -> dict:
        """Creates error result structure."""
        return {
            "status": "error",
            "total_score": 0,
            "max_score": 100,
            "percentage": 0,
            "category_scores": {
                "error_detection": {"achieved": 0, "max": 70},
            },
            "details": [error_msg],
            "violations": [error_msg],
        }


__all__ = [
    "DocumentationEvaluator",
    "SemanticMatcher",
    "TieredScoringEngine",
    "SolutionQualityEvaluator",
    "StructureValidator",
    "ReadabilityScorer",
    "CompletenessChecker",
]
