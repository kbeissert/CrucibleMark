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

from benchmark_modules.base_test import BaseTest  # noqa: E402
from benchmark_modules.content_transformation.core.constants import (  # noqa: E402
    DEFAULT_TEMPERATURE,
    TOKEN_MULTIPLIER,
)
from benchmark_modules.content_transformation.core.evaluators import ContentTransformationEvaluator  # noqa: E402


class ContentTransformationTest(BaseTest):
    """
    Test-Modul für Content Transformation & Adaption.
    Acts as a runner, delegating scoring to ContentTransformationEvaluator.
    """

    def execute(self, model: str, llm_client: Any, provider: str = "ollama") -> dict:
        """
        Führt Content Transformation Test aus
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
            # Use specific temperature for Content Transformation - needs creativity
            response = llm_client.query(
                model,
                full_prompt,
                provider=provider,
                temperature=DEFAULT_TEMPERATURE,
                max_tokens=2048
            )
            # Use clean execution time if available, otherwise fallback to wall clock
            if hasattr(llm_client, "last_query_duration") and llm_client.last_query_duration > 0:
                elapsed = llm_client.last_query_duration
            else:
                elapsed = time.time() - start

            # Token-Approximation
            approx_tokens = int(len(response.split()) * TOKEN_MULTIPLIER)

            return {
                "raw_response": response,
                "execution_time": elapsed,
                "tokens_used": approx_tokens,
                "metadata": {
                    "model": model,
                    "asset_id": self.asset["metadata"]["id"],
                    "prompt_length": len(full_prompt),
                    **getattr(llm_client, "last_response_metadata", {}),
                },
            }
        except Exception as e:
            return {
                "raw_response": f"ERROR: {str(e)}",
                "execution_time": 0.0,
                "tokens_used": 0,
                "metadata": {"model": model, "error": str(e)},
            }

    def score_response(self, response: str) -> dict:
        """
        Delegates scoring to ContentTransformationEvaluator.
        """
        evaluator = ContentTransformationEvaluator(self.asset)
        return evaluator.score_response(response)
