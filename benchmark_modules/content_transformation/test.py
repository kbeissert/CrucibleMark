#!/usr/bin/env python3
"""
Content Transformation & Adaption Test Module
Refactored using Clean Architecture (Core/MVC).
Delegates logic to benchmark_modules.content_transformation.core.evaluators.
"""

import sys
import time
from pathlib import Path
from typing import Any

# Ensure root directory is in sys.path
root_dir = Path(__file__).parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# pylint: disable=wrong-import-position
from schemas.result import BenchmarkResult  # noqa: E402
from benchmark_modules.base_test import BaseTest  # noqa: E402
from utils.model_utils import get_model_version  # noqa: E402
from benchmark_modules.content_transformation.core.constants import (  # noqa: E402
    DEFAULT_TEMPERATURE,
    TOKEN_MULTIPLIER,
)
from benchmark_modules.content_transformation.core.evaluators import (  # noqa: E402
    ContentTransformationEvaluator,
)  # noqa: E402
# pylint: enable=wrong-import-position


class ContentTransformationTest(BaseTest):
    """
    Test-Modul für Content Transformation & Adaption.
    Acts as a runner, delegating scoring to ContentTransformationEvaluator.
    """

    def execute(
        self, model: str, llm_client: Any, provider: str = "ollama", **kwargs: Any
    ) -> BenchmarkResult:
        """
        Führt Content Transformation Test aus
        """
        prompt = self.asset["prompt"]

        # Context hinzufügen falls vorhanden
        full_prompt = f"{self.asset['context']}\n\n{prompt}" if "context" in self.asset else prompt

        # LLM Query
        start = time.time()
        extra_kwargs = {k: v for k, v in kwargs.items() if k not in ("provider",)}

        try:
            # Use specific temperature for Content Transformation - needs creativity
            response = llm_client.query(
                model,
                full_prompt,
                provider=provider,
                temperature=DEFAULT_TEMPERATURE,
                **extra_kwargs,
            )

            # Use clean execution time if available, otherwise fallback to wall clock
            if (
                hasattr(llm_client, "last_query_duration")
                and llm_client.last_query_duration > 0
            ):
                elapsed = llm_client.last_query_duration
            else:
                elapsed = time.time() - start

            # Token-Approximation
            approx_tokens = int(len(response.split()) * TOKEN_MULTIPLIER)

            load_time = getattr(llm_client, "last_response_metadata", {}).get(
                "load_duration", 0.0
            )

            return BenchmarkResult(
                status="success",
                primary_score=None,
            max_score=100.0,
                rendered_value="Pending",
                raw_response=response,
                evaluated_prompt=full_prompt,
                execution_time=elapsed,
                load_time=load_time,
                tokens_used=approx_tokens,
                cost_usd=getattr(llm_client, "last_request_cost", 0.0),
                model_version=get_model_version(model_name=model, provider=provider),
                tokens_per_second=0.0,
                token_limit_cutoff=False,
                token_limit_fallback=False,
                token_limit_used=None,
                finish_reason=getattr(llm_client, "last_response_metadata", {}).get(
                    "finish_reason", "completed"
                ),
                meta={
                    "model": model,
                    "asset_id": self.asset["metadata"]["id"],
                    "prompt_length": len(full_prompt),
                    **getattr(llm_client, "last_response_metadata", {}),
                },
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            return BenchmarkResult(
                status="error",
                primary_score=0.0,
                rendered_value="ERROR",
                raw_response=f"ERROR: {str(e)}",
                evaluated_prompt=full_prompt,
                execution_time=0.0,
                load_time=0.0,
                tokens_used=0,
                cost_usd=0.0,
                tokens_per_second=0.0,
                token_limit_cutoff=False,
                token_limit_fallback=False,
                token_limit_used=None,
                model_version=get_model_version(model_name=model, provider=provider),
                finish_reason="error",
                meta={"model": model, "error": str(e)},
            )

    def score_response(self, result: BenchmarkResult) -> BenchmarkResult:
        """
        Delegates scoring to ContentTransformationEvaluator.
        """
        evaluator = ContentTransformationEvaluator(self.asset)
        score_dict = evaluator.score_response(result.raw_response)

        result.primary_score = score_dict.get("score", score_dict.get("total_score"))
        result.tier = score_dict.get("tier", "Tier 1 (Undefined)")
        result.data = score_dict
        result.rendered_value = f"{result.primary_score} %" if result.primary_score is not None else "N/A"

        return result
