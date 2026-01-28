"""
Reasoning Logic Test Module
Refactored for Modularity/MVC.
Delegates logic to benchmark_modules.reasoning_logic.core.evaluators.
"""

import time
from typing import Any, Dict
from benchmark_modules.base_test import BaseTest
from benchmark_modules.reasoning_logic.core.constants import TOKEN_ESTIMATION_FACTOR
from benchmark_modules.reasoning_logic.core.evaluators import ReasoningEvaluator


class ReasoningLogicTest(BaseTest):
    """
    Testklasse für Logical Reasoning & Problem Solving.
    Acts as a runner, delegating scoring to ReasoningEvaluator.
    """

    def execute(
        self, model: str, llm_client: Any, provider: str = "ollama"
    ) -> Dict[str, Any]:
        """
        Executes the reasoning test.
        """
        prompt = self.asset["prompt"]
        system_prompt = self.get_system_prompt()

        full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"

        start = time.time()
        # Note: We rely on llm_client.query to handle the actual API call
        response = llm_client.query(
            model, full_prompt, provider=provider, temperature=0.6
        )
        elapsed = time.time() - start

        approx_tokens = len(response.split()) * TOKEN_ESTIMATION_FACTOR

        # Determine Reasoning Capability
        model_lower = model.lower()
        reasoning_cap = 20  # Default: Pattern Matching
        reasoning_type = "Pattern Matching"

        if "deepseek" in model_lower and "r1" in model_lower:
            reasoning_cap = 100
            reasoning_type = "Explicit Reasoning"
        elif "qwen" in model_lower: # Qwen is generally strong at CoT
            reasoning_cap = 70
            reasoning_type = "Implicit Reasoning"

        return {
            "raw_response": response,
            "execution_time": elapsed,
            "tokens_used": approx_tokens,
            "metadata": {
                "model": model,
                "asset_id": self.asset["metadata"]["id"],
                "reasoning_capability_score": reasoning_cap,
                "reasoning_type": reasoning_type
            },
        }

    def score_response(self, response: str) -> Dict[str, Any]:
        """
        Delegates scoring to ReasoningEvaluator.
        """
        evaluator = ReasoningEvaluator(self.asset)
        return evaluator.score_response(response)

    def get_system_prompt(self) -> str:
        """
        Spezifischer System-Prompt, der Reasoning explizit anfordert.
        """
        return (
            "You are a logic expert. Solve the given problem step-by-step. "
            "Show your reasoning process clearly ('Chain of Thought'). "
            "Finally, provide the clear Answer."
        )
