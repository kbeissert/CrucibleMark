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
from schemas.result import BenchmarkResult

# Ensure root directory is in sys.path
root_dir = Path(__file__).parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from benchmark_modules.base_test import BaseTest  # noqa: E402
from benchmark_modules.ux_writing.core.models import (
    UXScenario,
    UXScoringConfig,
)  # noqa: E402
from benchmark_modules.ux_writing.core.evaluators import (
    IssueEvaluator,
    EvaluatorFactory,
)  # noqa: E402
from benchmark_modules.ux_writing.core.constants import (  # noqa: E402
    TIER_S_THRESHOLD,
    TIER_A_THRESHOLD,
    TIER_B_THRESHOLD,
    TIER_C_THRESHOLD,
    ASSET_REQUIRED_RATIOS,
    DEFAULT_REQUIRED_RATIO,
)
from utils.llm_client import LLMClient  # noqa: E402


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

    def execute(
        self, model: str, llm_client: LLMClient, provider: str = "ollama"
    ) -> BenchmarkResult:
        """
        Führt den Test für das geladene Asset aus.
        Returns BenchmarkResult object.
        """
        prompt = self.scenario.to_prompt()

        start_time = time.time()
        # Adapter for LLMClient.query(model, prompt, provider)
        response = llm_client.query(model=model, prompt=prompt, provider=provider)

        # Use clean execution time (excluding timeouts/retries) if available
        if (
            hasattr(llm_client, "last_query_duration")
            and llm_client.last_query_duration > 0
        ):
            execution_time = llm_client.last_query_duration
        else:
            execution_time = time.time() - start_time

        if not response:
            self.logger.error("Empty response received from LLM")
            response = ""

        # Merge metadata
        meta = self.asset.get("metadata", {}).copy()
        meta.update(getattr(llm_client, "last_response_metadata", {}))

        load_time = getattr(llm_client, "last_response_metadata", {}).get(
            "load_duration", 0.0
        )

        return BenchmarkResult(
            status="success",
            primary_score=None,
            rendered_value="Pending",
            execution_time=execution_time,
            load_time=load_time,
            raw_response=response,
            evaluated_prompt=prompt,
            tokens_used=getattr(llm_client, "last_token_usage", 0),
            cost_usd=getattr(llm_client, "last_request_cost", 0.0),
            model_version=getattr(llm_client, "last_response_metadata", {}).get(
                "system_fingerprint", "unknown"
            ),
            meta=meta,
        )

    def score_response(self, result: BenchmarkResult) -> BenchmarkResult:
        """
        Bewertet die Antwort basierend auf den Kriterien im Asset.

        Args:
            result: Das vom Runner generierte BenchmarkResult-Objekt.

        Returns:
            Aktualisiertes BenchmarkResult mit Scores, Tier und Details.
        """
        scores, details = self._evaluate_response(result.raw_response, self.scenario.scoring)

        total_score = scores.get("total", 0.0)

        # Format category scores for display
        category_scores = {}
        for key, value in scores.items():
            if key == "total":
                continue
            # Simple fallback for visualization to match base runner expectation {achieved, max}
            category_scores[key] = {
                "achieved": round(value, 1),
                "max": 100,  # Placeholder as max is dynamic
            }

        score_dict = {
            "total_score": total_score,
            "max_score": 100,  # Normalized to 100 in logic
            "category_scores": category_scores,
            "status": "success",
            "tier": self._calculate_tier(total_score),
            "details": details,
        }
        
        result.primary_score = score_dict.get("score", score_dict.get("total_score"))
        result.tier = score_dict.get("tier", "Tier 1 (Undefined)")
        result.data = score_dict
        result.rendered_value = f"{result.primary_score} %" if result.primary_score is not None else "N/A"
        
        return result

    def _calculate_tier(self, score: float) -> str:
        """
        Berechnet das Tier basierend auf dem Score.

        Args:
            score: Erreichter Gesamtscore.

        Returns:
            Tier-Name (z.B. "Tier S (Expert)").
        """
        if score >= TIER_S_THRESHOLD:
            return "Tier S (Expert)"
        if score >= TIER_A_THRESHOLD:
            return "Tier A (Professional)"
        if score >= TIER_B_THRESHOLD:
            return "Tier B (Competent)"
        if score >= TIER_C_THRESHOLD:
            return "Tier C (Novice)"
        return "Tier D (Inadequate)"

    def _evaluate_response(
        self, response: str, config: UXScoringConfig
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Führt die eigentliche Bewertung durch.

        Args:
            response: Antworttext.
            config: Scoring-Konfiguration aus dem Asset.

        Returns:
            Tuple: (Score-Breakdown Dict, Liste von Detail-Strings).
        """
        total_score = 0.0
        breakdown = {
            "error_detection": 0.0,
            "solution_quality": 0.0,
            "formatting": 0.0,
            "total": 0.0,
        }
        details = []

        # 1. Error Detection (Issues)
        if config.error_detection:
            ed_score = 0.0

            all_issues = (
                config.error_detection.labeled_issues
                + config.error_detection.standard_issues
                + config.error_detection.advanced_issues
                + config.error_detection.expert_issues
            )

            # Determine Ratio Baseline based on Config or Asset ID
            if (
                config.error_detection
                and config.error_detection.default_required_ratio is not None
            ):
                default_ratio = config.error_detection.default_required_ratio
            else:
                asset_id = self.asset.get("metadata", {}).get("id", "")
                default_ratio = ASSET_REQUIRED_RATIOS.get(
                    asset_id, DEFAULT_REQUIRED_RATIO
                )

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
