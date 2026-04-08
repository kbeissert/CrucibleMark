#!/usr/bin/env python3
"""
Cultural Intelligence Test Module
Refactored using Clean Architecture (Core/MVC).
Delegates logic to benchmark_modules.cultural_intelligence.core.evaluators.
"""

import time
from typing import Any
from benchmark_modules.base_test import BaseTest
from benchmark_modules.cultural_intelligence.core.evaluators import (
    CulturalIntelligenceEvaluator,
)


from schemas.result import BenchmarkResult


class CulturalIntelligenceTest(BaseTest):
    """
    Evaluates Cultural Intelligence / Fit in German context.
    Acts as a runner, delegating scoring to CulturalIntelligenceEvaluator.
    """

    def execute(
        self, model: str, llm_client: Any, **kwargs: Any
    ) -> BenchmarkResult:
        """
        Executes the benchmark test using the provided LLM client.
        """
        start_time = time.time()

        # Build prompt from asset
        prompt = self.asset.get("prompt", "")
        if not prompt:
            prompt = self.asset.get("input_text", "")

        system_prompt = (
            "You are a helpful AI assistant specialized in German language and culture."
        )

        full_prompt = f"{system_prompt}\n\n{prompt}"
        provider = kwargs.get("provider")
        extra_kwargs = {k: v for k, v in kwargs.items() if k != "provider"}

        # Execute via client
        try:
            response_text = llm_client.query(
                prompt=full_prompt, model=model, provider=provider, temperature=0.5, **extra_kwargs
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            response_text = f"Error executing model: {str(e)}"

        # Use clean execution time (excluding timeouts/retries) if available
        if (
            hasattr(llm_client, "last_query_duration")
            and llm_client.last_query_duration > 0
        ):
            execution_time = llm_client.last_query_duration
        else:
            execution_time = time.time() - start_time

        # Extract meta
        meta = {
            "model": model,
            "provider": provider,
            **getattr(llm_client, "last_response_metadata", {}),
        }

        load_time = getattr(llm_client, "last_response_metadata", {}).get(
            "load_duration", 0.0
        )

        # Helper to safely get costs/tokens if avaiable in metadata
        # (This depends on llm_client populating metadata correctly)

        return BenchmarkResult(
            primary_score=None,
            max_score=100.0,  # Not scored yet
            rendered_value="Pending",
            evaluated_prompt=full_prompt,
            execution_time=execution_time,
            load_time=load_time,
            raw_response=response_text,
            tokens_used=getattr(llm_client, "last_token_usage", 0),
            cost_usd=getattr(llm_client, "last_request_cost", 0.0),
            meta=meta,
        )

    def score_response(self, result: BenchmarkResult) -> BenchmarkResult:
        """
        Delegates scoring to CulturalIntelligenceEvaluator.
        """
        evaluator = CulturalIntelligenceEvaluator(self.asset)
        score_dict = evaluator.score_response(result.raw_response)

        result.primary_score = score_dict.get("score", score_dict.get("total_score"))
        result.tier = score_dict.get("tier", "Tier 1 (Undefined)")
        result.data = score_dict
        result.rendered_value = f"{result.primary_score} %" if result.primary_score is not None else "N/A"

        return result
