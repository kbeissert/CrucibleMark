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

    def execute(self, model: str, llm_client: Any, provider: str = "ollama") -> dict:
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
        Delegates scoring to DocumentationEvaluator.
        """
        # Pass path so evaluator can deduce asset_id if needed
        evaluator = DocumentationEvaluator(self.asset, self.asset_path)
        return evaluator.score_response(response)
