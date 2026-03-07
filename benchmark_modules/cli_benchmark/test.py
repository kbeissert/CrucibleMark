"""Module for test.py."""
import json
import logging
import time
from pathlib import Path
from typing import Any

import yaml

from benchmark_modules.cli_benchmark.core.constants import (
    BIG_TOKEN_THRESHOLD,
    CLI_BRONZE_THRESHOLD,
    CLI_GOLD_THRESHOLD,
    CLI_SILVER_THRESHOLD,
    INLINE_GREEN,
    INLINE_ORANGE,
    INLINE_STAR,
    INLINE_TROPHY,
    INLINE_YELLOW,
    SYSTEM_PROMPT,
)
from benchmark_modules.cli_benchmark.core.evaluator import CLIEvaluator
from benchmark_modules.cli_benchmark.core.tasks import CLITaskLoader
from schemas.result import BenchmarkResult

logger = logging.getLogger(__name__)


class CLIBenchmarkTest:
    """
    Test-Klasse für CLI Benchmark. Führt Shell-Simulations-Aufgaben aus.
    Batch Mode.
    """

    def __init__(self) -> None:
        """Initialize."""
        self.loader = CLITaskLoader()
        self.evaluator = CLIEvaluator()
        self.questions = []
        self.num_runs = 1
        self.config = {}
        self.generation_config = {"temperature": 0.1}  # fallback
        self._load_module_config()

    def _load_module_config(self) -> None:
        """Loads execution and generation parameters from config.yaml."""
        try:
            config_path = Path(__file__).parent / "config.yaml"
            if config_path.exists():
                with config_path.open("r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    self.config = data.get("config", {})

                    # Override defaults with generation config
                    module_gen = data.get("generation", {})
                    self.generation_config.update(module_gen)

                    execution = data.get("execution", {})
                    self.num_runs = execution.get("min_runs", 1)
        except Exception as _e:  # pylint: disable=broad-exception-caught
            logger.warning("Failed to load module config", exc_info=True)

    def load_questions(self, _assets_dir: str | None = None) -> None:
        """Lädt die Liste an CSV-Tasks."""
        self.questions = self.loader.load_tasks()

    # pylint: disable=too-many-locals,too-many-arguments,too-many-positional-arguments
    def _evaluate_single_task(
        self,
        q: dict,
        model: str,
        llm_client: Any,
        provider: str,
        idx: int,
        total_questions: int,
    ) -> dict:
        """Kapselt die Bearbeitung und Auswertung eines einzelnen Tasks."""
        q_name = str(q.get("name", q.get("id", "Unknown")))[:25]
        print(
            f"   ⏳ [{idx}/{total_questions}] {q_name}: Test läuft...",
            end="\r",
            flush=True,
        )

        task_prompt = (
            f"Task: {q['name']}\nDescription: {q['description']}\n"
            f"Tools: {q['tools']}\nGenerate the bash commands to solve this:"
        )

        start_t = time.time()
        output_text = ""
        try:
            temp = self.generation_config.get("temperature", 0.1)
            top_p = self.generation_config.get("top_p", 0.9)

            output_text = llm_client.query(
                model=model,
                provider=provider,
                system=SYSTEM_PROMPT,
                prompt=task_prompt,
                temperature=temp,
                top_p=top_p,
            )
        except Exception as _e:  # pylint: disable=broad-exception-caught
            output_text = "Error calling model"
            logger.error("Error calling model: %s", _e)

        elapsed = time.time() - start_t
        tokens = int(len(output_text) / 4)

        eval_res = self.evaluator.evaluate(q, output_text)

        pct = eval_res.get("solutionquality", 0.0)
        if pct >= INLINE_TROPHY:
            badge_inline = "🏆"
        elif pct >= INLINE_STAR:
            badge_inline = "⭐"
        elif pct >= INLINE_GREEN:
            badge_inline = "🟢"
        elif pct >= INLINE_YELLOW:
            badge_inline = "🟡"
        elif pct >= INLINE_ORANGE:
            badge_inline = "🟠"
        else:
            badge_inline = "🔴"

        if tokens > BIG_TOKEN_THRESHOLD:
            token_str = f"{tokens / 1000.0:.1f}k T"
        else:
            token_str = f"{tokens} T"

        status_icon = "✓" if eval_res.get("status") == "success" else "✗"

        print(" " * 80, end="\r")
        print(
            f"   {status_icon} [{idx}/{total_questions}] {q_name:<25}: "
            f"{pct:>5.1f}% {badge_inline} | {token_str} | {elapsed:>4.1f}s"
        )

        return {
            "task_id": q.get("id"),
            "task_name": q.get("name"),
            "model_output": output_text,
            "eval": eval_res,
            "time_s": elapsed,
            "tokens": tokens,
            "solutionquality": pct,
            "status": eval_res.get("status"),
        }

    # pylint: disable=too-many-locals
    def execute(
        self, model: str, llm_client: Any, provider: str = "ollama", **_kwargs: Any
    ) -> BenchmarkResult:
        """
        Führt das Batch-Modul aus.
        """
        if not self.questions:
            self.load_questions()

        total_score = 0.0
        details = []
        total_time = 0.0
        total_tokens = 0
        success_count = 0
        total_q = len(self.questions)

        print("Fortschritt:")
        for idx, q in enumerate(self.questions, 1):
            res = self._evaluate_single_task(
                q, model, llm_client, provider, idx, total_q
            )

            total_time += res["time_s"]
            total_tokens += res["tokens"]
            total_score += res["solutionquality"]
            if res["status"] == "success":
                success_count += 1

            details.append(
                {
                    "task_id": res["task_id"],
                    "task_name": res["task_name"],
                    "model_output": res["model_output"],
                    "eval": res["eval"],
                    "time_s": res["time_s"],
                }
            )

        avg_score = total_score / total_q if total_q else 0.0

        if avg_score >= CLI_GOLD_THRESHOLD:
            badge = "CLI Gold 🥇"
        elif avg_score >= CLI_SILVER_THRESHOLD:
            badge = "CLI Silver 🥈"
        elif avg_score >= CLI_BRONZE_THRESHOLD:
            badge = "CLI Bronze 🥉"
        else:
            badge = "CLI Fail ❌"

        succ_rate = f"{(success_count / max(total_q, 1)) * 100:.1f}%"
        report = {
            "status": "success",
            "score": avg_score,
            "badge": badge,
            "success_rate": succ_rate,
            "details": details,
        }

        return BenchmarkResult(
            status="success",
            primary_score=float(avg_score),
            rendered_value=f"{badge} ({avg_score:.1f}/100)",
            execution_time=float(total_time),
            tokens_used=int(total_tokens),
            cost_usd=0.0,
            raw_response=json.dumps(report),
            model_version="unknown",
            data={
                "subscores": {
                    "routine": avg_score,
                    "reasoning": avg_score * (success_count / max(total_q, 1)),
                },
                "raw_score": avg_score / 100.0,
                "display": {"summary": f"{success_count}/{total_q} Tasks Successful"},
            },
        )
