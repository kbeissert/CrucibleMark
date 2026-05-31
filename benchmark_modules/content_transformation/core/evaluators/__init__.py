"""
Content Transformation Evaluator (Facade)
Orchestrates the evaluation process by delegating to specialized evaluators.
"""

from typing import Any, Dict

from utils.benchmark_utils import clean_reasoning_tags
from .tiered_scoring import TieredScoringEngine
from .content_quality import ContentQualityEvaluator
from .format_validator import FormatValidator
from .tone_evaluator import ToneEvaluator
from .semantic_matcher import SemanticMatcher

__all__ = [
    "ContentTransformationEvaluator",
    "TieredScoringEngine",
    "ContentQualityEvaluator",
    "FormatValidator",
    "ToneEvaluator",
    "SemanticMatcher",
]


class ContentTransformationEvaluator:
    """
    Evaluator class for Content Transformation benchmarks.
    Encapsulates scoring logic for Error Detection (Tiered) and Solution Quality.
    """

    def __init__(self, asset: Dict[str, Any]):
        self.asset = asset

    def score_response(self, response: str) -> dict:
        """
        Bewertet Content Transformation Antwort nach Tiered Difficulty System

        Scoring-Kategorien:
        1. Error Detection (70 Punkte) - Tiered (Labeled -> Expert)
           (Prüft ob geforderte Elemente vorhanden sind / Fehler vermieden wurden)
        2. Solution Quality (30 Punkte) - Kreativität, Flow, Format

        Args:
            response: LLM-Response als String

        Returns:
            Dict mit Score-Details
        """
        # Clean reasoning tags (e.g. DeepSeek <think>) before scoring
        clean_response = self._clean_reasoning_tags(response)

        # Logic for Two-Part Scoring (Analysis + Transformation)
        # If "TRANSFORMATION" separates the sections, we split them.
        # - Analysis part covers "Error Detection" (Concept Identification)
        # - Transformation part covers "Solution Quality" (Structure/Execution)

#        analysis_part = ""
        transformation_part = clean_response

        transformation_start = clean_response.find("TRANSFORMATION")
        if transformation_start > 0:
            # analysis_part = clean_response[:transformation_start]
            transformation_part = clean_response[transformation_start:]
        elif "ANALYSE" in clean_response and "1/x" in clean_response:
            # Heuristic fallback if TRANSFORMATION keyword missing but parts exist
            # Split at first numbered tweet pattern approx
            pass

        if not transformation_part or transformation_part.startswith("ERROR:"):
            return self._create_error_score("Invalid or error response")

        scoring_config = self.asset["scoring"]
        total_possible = scoring_config["total_points"]

        category_scores = {}
        details: list[str] = []
        violations: list[str] = []
        total_achieved: float = 0.0

        # Prepare texts
        # If we have an explicit analysis part, we use it for Error Detection.
        # Otherwise, we use the transformation part (fallback).
        # We append transformation to analysis if analysis is too short to avoid losing context
        # for keywords that might appear in the intro.
        # error_detection_text = (analysis_part + "\n" + transformation_part).lower()
        # But wait, the user said: "Problem: Scorer sucht nach Analyse-Keywords im GESAMTEN Response"
        # and "Scorer findet nur noch: ✓ 'Hook' → +5.0p".
        # This implies that searching the WHOLE text was GOOD for Error Detection.
        # The previous fix REMOVED the analysis part, which CAUSED the drop.
        # So for Error Detection, we should use the FULL response (cleaned).

        ed_text_to_use = clean_response.lower()
        sq_text_to_use = transformation_part.lower()

        # ===== KATEGORIE 1: Error Detection =====
        ed_weight = scoring_config["error_detection"]["weight"]
        ed_results = TieredScoringEngine.score_error_detection(
            ed_text_to_use, scoring_config["error_detection"]
        )
        ed_raw_score, ed_details, ed_violations, ed_max_possible = ed_results

        # Normalize Score to Weight (Scaling)
        if ed_max_possible > 0:
            ed_final_score = (ed_raw_score / ed_max_possible) * ed_weight
        else:
            ed_final_score = 0.0

        category_scores["error_detection"] = {
            "achieved": round(ed_final_score, 2),
            "raw_score": ed_raw_score,
            "max": ed_weight,
            "raw_max": ed_max_possible,
        }
        details.extend(ed_details)
        violations.extend(ed_violations)
        total_achieved += ed_final_score

        # ===== KATEGORIE 2: Solution Quality =====
        # Only score the Transformation part for Solution Quality
        # (e.g. structure, line breaks, length constraints of the tweets)

        # Check if Solution Quality exists in config - handled by evaluator usually but good to check
        if "solution_quality" in scoring_config:
            sq_weight = scoring_config["solution_quality"]["weight"]
            sq_raw_score, sq_details, sq_max_possible = (
                ContentQualityEvaluator.score_solution_quality(
                    sq_text_to_use, scoring_config["solution_quality"]
                )
            )

            # Normalize Score to Weight (Scaling)
            if sq_max_possible > 0:
                sq_final_score = (sq_raw_score / sq_max_possible) * sq_weight
            else:
                sq_final_score = 0.0

            category_scores["solution_quality"] = {
                "achieved": round(sq_final_score, 2),
                "raw_score": sq_raw_score,
                "max": sq_weight,
                "raw_max": sq_max_possible,
            }
            details.extend(sq_details)
            total_achieved += sq_final_score

        # HARD CONSTRAINT: Word Count (aus constraints.max_expected_words im Asset-YAML)
        # Progressiv gestaffelte Penalty: >120% -> -20%, >200% -> -40%, >300% -> -60%
        word_count = len(clean_response.split())
        max_words = self.asset.get("constraints", {}).get("max_expected_words")
        if max_words:
            ratio = word_count / max_words
            if ratio > 1.20:
                if ratio <= 2.0:
                    penalty_factor, tier_label = 0.20, "Mild Overshoot (>120%)"
                elif ratio <= 3.0:
                    penalty_factor, tier_label = 0.40, "Clear Violation (>200%)"
                else:
                    penalty_factor, tier_label = 0.60, "Constraint Ignored (>300%)"
                penalty = total_achieved * penalty_factor
                total_achieved = max(0, total_achieved - penalty)
                penalty_detail = (
                    f"> [!WARNING]\n"
                    f"> **[HARD CONSTRAINT VIOLATION – {tier_label}]** The model ignored the explicit word count limit of {max_words} words. "
                    f"Word count detected: {word_count} ({ratio:.0%} of limit). An automatic {int(penalty_factor * 100)}% deduction (-{penalty:.2f} pts) has been applied to the 'total_achieved' score."
                )
                details.append(penalty_detail)
                violations.append("Exceeded Max Word Count")

        return {
            "status": "success",
            "total_score": round(total_achieved, 2),
            "max_score": total_possible,
            "percentage": round((total_achieved / total_possible) * 100, 2),
            "category_scores": category_scores,
            "details": details,
            "violations": violations,
            "metadata": {
                "response_length": len(response),
                "word_count": len(response.split()),
            },
        }

    def _clean_reasoning_tags(self, response: str) -> str:
        """Removes reasoning tags. CT-specific: only <think> + extra patterns.

        Intentionally does NOT strip <thought> to avoid Glossary content loss.
        Delegates to utils.benchmark_utils.clean_reasoning_tags.
        """
        return clean_reasoning_tags(
            response,
            tags=["think"],
            extra_patterns=[
                r"<reflection>.*?</reflection>",
                r"\[Reasoning\].*?\[/Reasoning\]",
            ],
        )

    def _create_error_score(self, msg: str) -> dict:
        """Create a default error score structure."""
        return {
            "status": "error",
            "total_score": 0.0,
            "max_score": self.asset["scoring"]["total_points"],
            "percentage": 0.0,
            "category_scores": {},
            "details": [f"Error: {msg}"],
            "violations": [],
        }
