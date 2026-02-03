#!/usr/bin/env python3
"""
Cultural Intelligence Test Module
Refactored using Clean Architecture (Core/MVC).
Delegates logic to benchmark_modules.cultural_intelligence.core.evaluators.
"""

import time
from typing import Any, Dict
from benchmark_modules.base_test import BaseTest
from benchmark_modules.cultural_intelligence.core.evaluators import CulturalIntelligenceEvaluator


class CulturalIntelligenceTest(BaseTest):
    """
    Evaluates Cultural Intelligence / Fit in German context.
    Acts as a runner, delegating scoring to CulturalIntelligenceEvaluator.
    """

    def execute(
        self, model: str, llm_client: Any, provider: str = "ollama"
    ) -> Dict[str, Any]:
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

        # Execute via client
        try:
            response_text = llm_client.query(
                prompt=full_prompt, model=model, provider=provider, temperature=0.5
            )
        except Exception as e:
            response_text = f"Error executing model: {str(e)}"

        # Use clean execution time (excluding timeouts/retries) if available
        if hasattr(llm_client, "last_query_duration") and llm_client.last_query_duration > 0:
            execution_time = llm_client.last_query_duration
        else:
            execution_time = time.time() - start_time

        return {
            "response": response_text,
            "raw_response": response_text,
            "execution_time": execution_time,
            "metadata": {
                "model": model, 
                "provider": provider,
                **getattr(llm_client, "last_response_metadata", {})
            },
        }

    def score_response(self, response: str) -> Dict[str, Any]:
        """
        Delegates scoring to CulturalIntelligenceEvaluator.
        """
        evaluator = CulturalIntelligenceEvaluator(self.asset)
        return evaluator.score_response(response)
