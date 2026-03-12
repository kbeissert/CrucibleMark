#!/usr/bin/env python3
"""
Documentation Quality Test Module
Refactored using Clean Architecture (Core/MVC).
Delegates logic to benchmark_modules.documentation_quality.core.evaluators.
"""

import sys
import time
from pathlib import Path
from typing import Any

# Ensure root directory is in sys.path
root_dir = Path(__file__).parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from schemas.result import BenchmarkResult  # noqa: E402
from benchmark_modules.base_test import BaseTest  # noqa: E402
from benchmark_modules.documentation_quality.core.constants import (  # noqa: E402
    DEFAULT_TEMPERATURE,
    TOKEN_MULTIPLIER,
)
from benchmark_modules.documentation_quality.core.evaluators import DocumentationEvaluator  # noqa: E402


class DocumentationTest(BaseTest):
    """
    Test-Modul für Documentation Quality mit Tiered Difficulty.
    Acts as a runner, delegating scoring to DocumentationEvaluator.
    """

    def execute(self, model: str, llm_client: Any, provider: str = "ollama") -> BenchmarkResult:
        """
        Führt Documentation Quality Test aus
        """
        prompt = self.asset["prompt"]

        # Context hinzufügen falls vorhanden
        if "context" in self.asset:
            full_prompt = f"{self.asset['context']}\n\n{prompt}"
        else:
            full_prompt = prompt

        # LLM Query
        start = time.time()

        try:
            # Use temperature 0.3 for Documentation Quality
            response = llm_client.query(
                model, full_prompt, provider=provider, temperature=DEFAULT_TEMPERATURE
            )
            # Use clean execution time if available, otherwise fallback to wall clock
            if hasattr(llm_client, "last_query_duration") and llm_client.last_query_duration > 0:
                elapsed = llm_client.last_query_duration
            else:
                elapsed = time.time() - start

            # Token-Approximation
            approx_tokens = int(len(response.split()) * TOKEN_MULTIPLIER)

            load_time = getattr(llm_client, "last_response_metadata", {}).get("load_duration", 0.0)

            return BenchmarkResult(
                status="success",
                primary_score=None,
                rendered_value="Pending",
                raw_response=response,
                evaluated_prompt=full_prompt,
                execution_time=elapsed,
                load_time=load_time,
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
                raw_response=f"ERROR: {str(e)}",
                execution_time=0.0,
                meta={"model": model, "error": str(e)}
            )

    def score_response(self, response: str) -> dict:
        """
        Delegates scoring to DocumentationEvaluator.
        """
        # Pass path so evaluator can deduce asset_id if needed
        evaluator = DocumentationEvaluator(self.asset, self.asset_path)
        return evaluator.score_response(response)
