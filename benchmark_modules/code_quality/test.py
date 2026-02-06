#!/usr/bin/env python3
"""
Code Quality Test Module
Refactored using Clean Architecture (Core/MVC).
Delegates logic to benchmark_modules.code_quality.core.evaluators.
"""

import sys
import time
from pathlib import Path
from typing import Any, Dict

# Ensure root directory is in sys.path
root_dir = Path(__file__).parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from benchmark_modules.base_test import BaseTest  # noqa: E402
from benchmark_modules.code_quality.core.constants import (  # noqa: E402
    DEFAULT_TEMPERATURE,
    TOKEN_MULTIPLIER,
)
from benchmark_modules.code_quality.core.evaluators import CodeQualityEvaluator
from schemas.result import BenchmarkResult  # Correct import


class CodeQualityTest(BaseTest):
    """
    Test module for Code Quality and Accessibility.
    Acts as a lightweight runner, delegating scoring to CodeQualityEvaluator.
    """

    def execute(
        self,
        model: str,
        llm_client: Any,  # TODO: Später durch LLMClient Interface ersetzen
        provider: str = "ollama",
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Executes the Code Quality test for a given model.

        Args:
            model: Model identifier
            llm_client: Client for LLM interaction
            provider: Provider name (default: "ollama")
            **kwargs: Additional arguments

        Returns:
            Dict containing raw_response, execution_time, tokens_used, metadata
        """
        prompt = self.asset["prompt"]
        full_prompt = f"{self.asset.get('context', '')}\n\n{prompt}".strip()

        start = time.time()

        try:
            # Deterministic output via low temperature
            response = llm_client.query(
                model,
                full_prompt,
                provider=provider,
                temperature=DEFAULT_TEMPERATURE,
                **kwargs,
            )
            # Use clean execution time (excluding timeouts/retries) if available
            if hasattr(llm_client, "last_query_duration") and llm_client.last_query_duration > 0:
                elapsed = llm_client.last_query_duration
            else:
                elapsed = time.time() - start

            approx_tokens = int(len(response.split()) * TOKEN_MULTIPLIER)

            return BenchmarkResult(
                status="success",
                primary_score=None,
                rendered_value="Pending",
                raw_response=response,
                execution_time=elapsed,
                tokens_used=approx_tokens,
                cost_usd=getattr(llm_client, "last_request_cost", 0.0),
                model_version=getattr(llm_client, "last_response_metadata", {}).get("system_fingerprint", "unknown"),
                meta={
                    "model": model,
                    "asset_id": self.asset["metadata"]["id"],
                    "prompt_length": len(full_prompt),
                    **getattr(llm_client, "last_response_metadata", {}),
                }
            )
        except Exception as e:
            return BenchmarkResult(
                status="error",
                rendered_value="ERROR",
                raw_response=str(e),
                execution_time=0.0,
                meta={
                    "model": model, 
                    "asset_id": self.asset.get("metadata", {}).get("id", "unknown"),
                    "error": str(e)
                }
            )

    def score_response(self, response: str) -> Dict[str, Any]:
        """
        Delegates scoring to the core evaluator.
        """
        evaluator = CodeQualityEvaluator(self.asset)
        return evaluator.score_response(response)
