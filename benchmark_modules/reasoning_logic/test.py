"""
Reasoning Logic Test Module
Refactored for Modularity/MVC.
Delegates logic to benchmark_modules.reasoning_logic.core.evaluators.
"""

import time
from typing import Any, cast
from benchmark_modules.base_test import BaseTest
from benchmark_modules.reasoning_logic.core.constants import (
    TOKEN_ESTIMATION_FACTOR,
    DEFAULT_TEMPERATURE,
    SYSTEM_PROMPT_REASONING,
    MODEL_REASONING_CAPABILITIES,
)
from benchmark_modules.reasoning_logic.core.evaluators import (
    ReasoningEvaluator,
    RUBRICS,
)
from schemas.result import BenchmarkResult


class ReasoningLogicTest(BaseTest):
    """
    Testklasse für Logical Reasoning & Problem Solving.
    Acts as a runner, delegating scoring to ReasoningEvaluator.
    """

    def execute(
        self,
        model: str,
        llm_client: Any,
        provider: str = "ollama",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Executes the reasoning test.
        """
        prompt = self.asset["prompt"]
        system_prompt = self.get_system_prompt()

        full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"

        start = time.time()
        # Note: We rely on llm_client.query to handle the actual API call
        response = llm_client.query(
            model, full_prompt, provider=provider, temperature=DEFAULT_TEMPERATURE
        )
        # Use clean execution time (excluding timeouts/retries) if available
        if (
            hasattr(llm_client, "last_query_duration")
            and llm_client.last_query_duration > 0
        ):
            elapsed = llm_client.last_query_duration
        else:
            elapsed = time.time() - start

        approx_tokens = self._estimate_tokens(response)

        # Determine Reasoning Capability
        reasoning_cap, reasoning_type = self._get_reasoning_capability(model)

        load_time = getattr(llm_client, "last_response_metadata", {}).get(
            "load_duration", 0.0
        )

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
            model_version=getattr(llm_client, "last_response_metadata", {}).get(
                "system_fingerprint", "unknown"
            ),
            data={
                "reasoning_capability_score": reasoning_cap,
                "reasoning_type": reasoning_type,
            },
            meta={
                "model": model,
                "asset_id": self.asset["metadata"]["id"],
                **getattr(llm_client, "last_response_metadata", {}),
            },
        )

    def score_response(self, response: str) -> dict[str, Any]:
        """
        Delegates scoring to ReasoningEvaluator.
        """
        evaluator = ReasoningEvaluator(self.asset)
        eval_result = evaluator.score_response(response)

        # Flatten breakdown for CSV (Granular Scoring Support)
        if "category_scores" in eval_result:
            asset_id = self.asset["metadata"]["id"]
            rubric = RUBRICS.get(asset_id, {})

            for key, data in eval_result["category_scores"].items():
                achieved = data["achieved"]
                # Try to get max weight from rubric
                max_weight = rubric.get(key, {}).get("weight", "??")

                # Add flattened key to result (e.g., 'problem_recognition': '20.0/20')
                eval_result[key] = f"{achieved}/{max_weight}"

        return eval_result

    def get_system_prompt(self) -> str:
        """
        Spezifischer System-Prompt, der Reasoning explizit anfordert.
        """
        return SYSTEM_PROMPT_REASONING

    def _estimate_tokens(self, text: str) -> int:
        """Estimates token count for stats."""
        return int(len(text.split()) * TOKEN_ESTIMATION_FACTOR)

    def _get_reasoning_capability(self, model: str) -> tuple[int, str]:
        """Determines reasoning capability based on model name."""
        model_lower = model.lower()

        # Check specific models
        for key, cap in MODEL_REASONING_CAPABILITIES.items():
            if key == "default":
                continue

            if key in model_lower:
                match_val = str(cap.get("match")) if cap.get("match") else None
                if match_val and match_val not in model_lower:
                    continue
                return cast(int, cap["score"]), str(cap["type"])

        # Default fallback
        default = MODEL_REASONING_CAPABILITIES["default"]
        return cast(int, default["score"]), str(default["type"])
