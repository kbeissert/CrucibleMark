"""Module for test.py."""
import logging
import time
from pathlib import Path
from typing import Any

from benchmark_modules.base_test import BaseTest
from benchmark_modules.cli_benchmark.core.constants import SYSTEM_PROMPT
from benchmark_modules.cli_benchmark.core.evaluator import CLIEvaluator
from schemas.result import BenchmarkResult

logger = logging.getLogger(__name__)

class CLIBenchmarkTest(BaseTest):
    """
    Test-Klasse für CLI Benchmark in the Standard Execution Mode.
    Führt jeweils eine Shell-Simulations-Aufgabe aus.
    """

    def __init__(self, asset_path: Path) -> None:
        """Initialize."""
        super().__init__(asset_path)
        self.evaluator = CLIEvaluator()

    def execute(
        self,
        model: str,
        llm_client: Any,
        provider: str = "ollama",
        **kwargs: Any,
    ) -> BenchmarkResult:
        """Executes a single CLI task."""
        q = {
            "id": self.asset.get("metadata", {}).get("id", "Unknown"),
            "name": self.asset.get("metadata", {}).get("name", "Unknown"),
            "tier": self.asset.get("metadata", {}).get("tier", 1),
            "description": self.asset.get("description", ""),
            "tools": self.asset.get("tools", []),
            "golden": self.asset.get("golden", {}),
        }

        task_prompt = (
            f"Task: {q['name']}\nDescription: {q['description']}\n"
            f"Tools: {q['tools']}\nGenerate the bash commands to solve this:"
        )

        start_t = time.time()
        output_text = ""

        # Module config default
        temp = 0.1
        top_p = 0.9

        try:
            output_text = llm_client.query(
                model=model,
                provider=provider,
                system=SYSTEM_PROMPT,
                prompt=task_prompt,
                temperature=temp,
                top_p=top_p,
            )
            status = "success"
        except (OSError, RuntimeError, ValueError) as e:
            output_text = "Error calling model"
            status = "error"
            logger.error("Error calling model: %s", e)

        if hasattr(llm_client, "last_query_duration") and getattr(llm_client, "last_query_duration", 0) > 0:
            elapsed = llm_client.last_query_duration
        else:
            elapsed = time.time() - start_t

        load_time = getattr(llm_client, "last_response_metadata", {}).get("load_duration", 0.0)

        # Assuming roughly 4 chars per token for simple estimation if token count not available
        tokens = int(len(output_text) / 4)

        return BenchmarkResult(
            status=status,
            primary_score=None,
            rendered_value="",
            evaluated_prompt=task_prompt,
            execution_time=float(elapsed),
            load_time=float(load_time),
            tokens_used=int(tokens),
            cost_usd=0.0,
            raw_response=output_text,
            model_version="unknown"
        )

    def score_response(self, response: str) -> dict[str, Any]:
        """Evaluate response using the CLIEvaluator."""
        q = {
            "id": self.asset.get("metadata", {}).get("id", "Unknown"),
            "name": self.asset.get("metadata", {}).get("name", "Unknown"),
            "tier": self.asset.get("metadata", {}).get("tier", 1),
            "description": self.asset.get("description", ""),
            "tools": self.asset.get("tools", []),
            "golden": self.asset.get("golden", {}),
        }

        eval_res = self.evaluator.evaluate(q, response)
        pct = eval_res.get("solutionquality", 0.0)

        return {
            "total_score": pct,
            "max_score": 100,
            "details": eval_res,
        }
