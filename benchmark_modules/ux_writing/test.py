#!/usr/bin/env python3
"""
UX Writing & Microcopy Test Module
Refactored using clean architecture (Models, Evaluators, Services).
Compatible with BaseBenchmarkRunner.
"""

import sys
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Ensure root directory is in sys.path
root_dir = Path(__file__).parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from benchmark_modules.base_test import BaseTest
from benchmark_modules.ux_writing.models import UXScenario, UXScoringConfig
from benchmark_modules.ux_writing.evaluators import IssueEvaluator, EvaluatorFactory

# Constants for Tier Calculation
TIER_S_THRESHOLD = 95.0
TIER_A_THRESHOLD = 85.0
TIER_B_THRESHOLD = 70.0
TIER_C_THRESHOLD = 50.0

class UXWritingTest(BaseTest):
    """
    Test-Modul für UX Writing & Microcopy.
    Orchestrates Loading -> Execution -> Evaluation -> Reporting.
    Compatible with CrucibleMark BaseBenchmarkRunner.
    """

    def __init__(self, asset_path: Path):
        """
        Initialisiert den Test mit einem Asset.
        """
        super().__init__(asset_path)
        self.logger = logging.getLogger(__name__)
        # Convert raw dictionary asset (loaded by BaseTest) to UXScenario model
        # BaseTest loads self.asset
        self.scenario = UXScenario.from_dict(self.asset)

    def execute(self, model: str, llm_client: Any, provider: str = "ollama") -> Dict[str, Any]:
        """
        Führt den Test für das geladene Asset aus.
        """
        prompt = self.scenario.to_prompt()

        start_time = time.time()
        # Adapter for LLMClient.query(model, prompt, provider)
        response = llm_client.query(model=model, prompt=prompt, provider=provider)
        execution_time = time.time() - start_time

        if not response:
            self.logger.error("Empty response received from LLM")
            response = ""

        return {
            "raw_response": response,
            "response": response,
            "execution_time": execution_time,
            "metadata": self.asset.get("metadata", {})
        }

    def score_response(self, response: str) -> Dict[str, Any]:
        """
        Bewertet die Antwort basierend auf den Kriterien im Asset.
        """
        scores, details = self._evaluate_response(response, self.scenario.scoring)
        
        total_score = scores.get("total", 0.0)
        
        # Format category scores for display
        category_scores = {}
        for key, value in scores.items():
            if key == "total":
                continue
            # Simple fallback for visualization to match base runner expectation {achieved, max}
            category_scores[key] = {
                "achieved": round(value, 1),
                "max": 100 # Placeholder as max is dynamic
            }

        return {
            "total_score": total_score,
            "max_score": 100.0, # Normalized to 100 in logic
            "category_scores": category_scores,
            "status": "success",
            "tier": self._calculate_tier(total_score),
            "details": details
        }

    def _calculate_tier(self, score: float) -> str:
        """Calculates Tier based on score."""
        if score >= TIER_S_THRESHOLD:
            return "Tier S (Expert)"
        if score >= TIER_A_THRESHOLD:
            return "Tier A (Professional)"
        if score >= TIER_B_THRESHOLD:
            return "Tier B (Competent)"
        if score >= TIER_C_THRESHOLD:
            return "Tier C (Novice)"
        return "Tier D (Inadequate)"

    def _evaluate_response(self, response: str, config: UXScoringConfig) -> Tuple[Dict[str, float], List[str]]:
        """
        Core evaluation logic ported from previous implementation.
        """
        total_score = 0.0
        breakdown = {
            "error_detection": 0.0,
            "solution_quality": 0.0,
            "formatting": 0.0,
            "bonus": 0.0,
            "total": 0.0
        }
        details = []

        # 1. Error Detection (Issues)
        if config.error_detection:
            ed_score = 0.0
            
            all_issues = (
                config.error_detection.labeled_issues +
                config.error_detection.standard_issues +
                config.error_detection.advanced_issues +
                config.error_detection.expert_issues
            )
            
            # Determine Ratio Baseline based on Asset ID (User Tuning)
            asset_id = self.asset.get("metadata", {}).get("id", "")
            ASSET_RATIOS = {
                "ux_writing_004": 1.0,  # A11y (Harder)
                "ux_writing_003": 0.5,  # Onboarding (Softer)
                "ux_writing_005": 0.4,  # Microcopy (Reset to Original)
            }
            default_ratio = ASSET_RATIOS.get(asset_id, 0.6)

            for issue in all_issues:
                 # Apply dynamic ratio if not explicitly set in YAML
                 if issue.required_ratio is None:
                     issue.required_ratio = default_ratio

                 # points, explanation, matched_boolean
                 points, msg, _ = IssueEvaluator.evaluate(response.lower(), issue)
                 ed_score += points
                 if points > 0 or "✗" in msg:
                     # details.append(msg)
                     pass
            
            breakdown["error_detection"] = ed_score
            total_score += breakdown["error_detection"]

        # 2. Checklist Criteria (Solution Quality)
        if config.solution_quality:
            sq_score = 0.0
            for criterion in config.solution_quality.criteria:
                evaluator = EvaluatorFactory.get_evaluator(criterion.check_method)
                points, msg = evaluator.evaluate(response, criterion)
                sq_score += points
                details.append(msg)
            
            breakdown["solution_quality"] = sq_score
            total_score += sq_score

        # 3. Formatting (Keywords & Structure)
        if config.formatting:
            fmt_score = 0.0
            for criterion in config.formatting.criteria:
                evaluator = EvaluatorFactory.get_evaluator(criterion.check_method)
                points, msg = evaluator.evaluate(response, criterion)
                fmt_score += points
                details.append(msg)
            
            breakdown["formatting"] = fmt_score
            total_score += fmt_score

        # Cap at 100
        breakdown["total"] = min(total_score, 100.0)
        return breakdown, details
