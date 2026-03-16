"""
Code Quality Evaluator - Facade Pattern.
Delegates scoring to specialized sub-modules.
"""

from typing import Any, Dict, List, Tuple
import re

from .error_detection import ErrorDetector
from .scoring_helpers import ScoringHelpers
from .constants import (
    ERROR_INVALID_RESPONSE,
    ERROR_TEST_FAILED,
    SCORING_CATEGORIES,
    REASONING_TAGS,
)


class CodeQualityEvaluator:
    """
    Main evaluator for Code Quality benchmarks.
    Orchestrates error detection, solution quality, and formatting checks.
    """

    def __init__(self, asset: Dict[str, Any]) -> None:
        self.asset = asset
        self.error_detector = ErrorDetector()
        self.scoring_helpers = ScoringHelpers()

    def score_response(self, response: str) -> Dict[str, Any]:
        """
        Facade Method: Main scoring entry point.
        Delegates to specialized scorers.
        """
        # Clean reasoning tags (e.g. DeepSeek <think>) before scoring
        clean_response = self._clean_reasoning_tags(response)

        if not clean_response or clean_response.strip() == "":
            return {
                "status": "error",
                "total_score": 0,
                "max_score": 100,
                "category_scores": {},
                "details": [ERROR_INVALID_RESPONSE],
                "violations": [ERROR_TEST_FAILED],
            }

        scoring_config = self.asset["scoring"]
        total_possible = scoring_config.get("total_points", 100)

        results: Dict[str, Any] = {
            "category_scores": {},
            "details": [],
            "violations": [],
            "total_achieved": 0.0,
        }

        response_lower = clean_response.lower()

        # 1. Error Detection (Handled specifically due to violations logic)
        ed_conf = scoring_config.get("error_detection", {})
        ed_score, ed_details, ed_violations = self.error_detector.score_error_detection(
            response_lower, ed_conf
        )
        self._process_category_result(
            "error_detection", ed_score, ed_details, ed_conf.get("weight", 0), results
        )
        results["violations"].extend(ed_violations)

        # 2. Generic Categories (Solution Quality, Formatting, Expertise)
        for cat in SCORING_CATEGORIES:
            if cat not in scoring_config:
                if cat == "expertise":  # Explicitly handle optional expertise
                    results["category_scores"][cat] = {"achieved": 0, "max": 0}
                continue

            cat_conf = scoring_config.get(cat, {})
            score, cat_details = self._score_generic_category(
                clean_response, response_lower, cat_conf
            )
            self._process_category_result(
                cat, score, cat_details, cat_conf.get("weight", 0), results
            )

        return {
            "status": "success",
            "total_score": round(results["total_achieved"], 2),
            "max_score": total_possible,
            "category_scores": results["category_scores"],
            "details": results["details"],
            "violations": results["violations"],
        }

    def _clean_reasoning_tags(self, response: str) -> str:
        """Removes <think>...</think> blocks from reasoning models."""
        cleaned = response
        for tag in REASONING_TAGS:
            pattern = f"<{tag}>.*?</{tag}>"
            cleaned = re.sub(pattern, "", cleaned, flags=re.DOTALL)
        return cleaned.strip()

    def _evaluate_criterion_dispatch(
        self, criterion: Dict[str, Any], response: str, response_lower: str
    ) -> Tuple[float, str]:
        """Dispatches criterion evaluation to appropriate scorer."""
        method = criterion.get("check_method")
        if not isinstance(method, str):
            return 0.0, ""

        # Normalize method name (snake_case expected)
        method_name = f"score_{method}"

        # Dynamic dispatch to ScoringHelpers
        if hasattr(self.scoring_helpers, method_name):
            scorer = getattr(self.scoring_helpers, method_name)

            # Different methods need different parameters
            if method in ["keyword_presence", "list_detection"]:
                return scorer(response_lower, criterion)
            else:
                return scorer(response, criterion)

        # Unknown method
        return 0.0, f"⚠️ Unknown check_method: {method}"

    def _score_generic_category(
        self, response: str, response_lower: str, config: Dict[str, Any]
    ) -> Tuple[float, List[str]]:
        """Generic category scoring (solution quality, formatting, expertise)."""
        score = 0.0
        details = []
        for criterion in config.get("criteria", []):
            delta, detail = self._evaluate_criterion_dispatch(
                criterion, response, response_lower
            )
            score += delta
            if detail:
                details.append(detail)
        return round(score, 2), details

    def _process_category_result(
        self,
        category_key: str,
        score: float,
        cat_details: List[str],
        weight: int,
        results: Dict[str, Any],
    ) -> None:
        """Updates results dict with category score."""
        results["category_scores"][category_key] = {
            "achieved": score,
            "max": weight,
        }
        results["details"].extend(cat_details)
        results["total_achieved"] += score
