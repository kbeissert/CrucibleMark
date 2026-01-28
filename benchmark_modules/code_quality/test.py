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

from benchmark_modules.base_test import BaseTest
from benchmark_modules.code_quality.core.constants import (
    DEFAULT_TEMPERATURE,
    TOKEN_MULTIPLIER,
)
from benchmark_modules.code_quality.core.evaluators import CodeQualityEvaluator


class CodeQualityTest(BaseTest):
    """
    Test-Modul für Code-Qualität und Accessibility.
    Acts as a lightweight runner, delegating scoring to CodeQualityEvaluator.
    """

    def execute(
        self, model: str, llm_client: Any, provider: str = "ollama", **kwargs
    ) -> Dict[str, Any]:
        """
        Führt den Code Quality Test aus.
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
            elapsed = time.time() - start

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

    def score_response(self, response: str) -> Dict[str, Any]:
        """
        Delegates scoring to the core evaluator.
        """
        evaluator = CodeQualityEvaluator(self.asset)
        return evaluator.score_response(response)
