"""
Base Benchmark Runner
Stellt gemeinsame Funktionalität für lokale und kommerzielle Runner bereit.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Tuple
from datetime import datetime

from utils.llm_client import LLMClient
from utils.config_validator import ConfigValidator
from utils.result_manager import ResultManager
from utils.module_loader import load_test_class
from utils.constants import QUALITY_EXCELLENT, QUALITY_GOOD, QUALITY_OK

from schemas.result import BenchmarkResult

logger = logging.getLogger(__name__)


class BaseBenchmarkRunner:
    """Abstrakte Basisklasse für Benchmark Runner."""

    def __init__(self):
        self.validator = ConfigValidator()
        self.client = LLMClient(config=self.validator.config)
        self.result_manager = ResultManager(self.validator)

    @staticmethod
    def get_quality_badge(percentage: float) -> str:
        """Gibt Qualitäts-Badge basierend auf Konstanten zurück."""
        if percentage >= QUALITY_EXCELLENT:
            return "🏆"
        if percentage >= QUALITY_GOOD:
            return "⭐"
        if percentage >= QUALITY_OK:
            return "✓"
        if percentage >= 1.0:
            return "📉"
        return "❌"

    def execute_test_module(
        self,
        model: str,
        asset_path: Path,
        benchmark_info: Dict[str, Any],
        provider: str = "ollama",
    ) -> Tuple[Any, BenchmarkResult]:
        """Lädt und führt ein Test-Modul aus (Shared Logic)."""
        # Pfad-Logik vereinheitlichen
        if "path" in benchmark_info:
            # z.B. benchmark_modules/code_quality/assets -> benchmark_modules/code_quality/test.py
            path = Path(benchmark_info["path"])
            if path.name == "assets":
                module_path = path.parent / "test.py"
            else:
                module_path = path / "test.py"
        else:
            # Fallback für Local Runner Config-Stil
            module_path = (
                Path(
                    benchmark_info.get("module_path", "benchmark_modules/code_quality")
                )
                / "test.py"
            )

        test_class_name = benchmark_info.get("test_class", "CodeQualityTest")

        try:
            test_cls = load_test_class(module_path, test_class_name)
        except (FileNotFoundError, ImportError, AttributeError) as e:
            raise FileNotFoundError(
                f"Test-Modul fehlerhaft: {module_path} ({e})"
            ) from e

        test_instance = test_cls(asset_path)
        # exec_result is now a BenchmarkResult object
        exec_result = test_instance.execute(model, self.client, provider=provider)

        # Inject finish_reason if available
        if hasattr(self.client, "last_response_metadata"):
            fr = self.client.last_response_metadata.get("finish_reason")
            if fr:
                exec_result.finish_reason = str(fr)
                if str(fr).lower() in ["length", "max_tokens"]:
                    exec_result.token_limit_cutoff = True

            fb = self.client.last_response_metadata.get("token_limit_fallback")
            if fb:
                # Add it to the model so the schema allows it
                exec_result.token_limit_fallback = True

            tlu = self.client.last_response_metadata.get("token_limit_used")
            if tlu is not None:
                exec_result.token_limit_used = tlu

        return test_instance, exec_result

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def build_base_result(
        self,
        model: str,
        asset_data: Dict[str, Any],
        exec_result: BenchmarkResult,  # Updated type hint
        provider: str,
    ) -> Dict[str, Any]:
        """Erstellt das standardisierte Ergebnis-Dictionary."""
        score = exec_result.data
        asset_id = asset_data.get("metadata", {}).get("id", "unknown")
        asset_name = asset_data.get("metadata", {}).get("name") or asset_data.get(
            "metadata", {}
        ).get("topic", asset_id)

        # Division by zero protection
        max_score = exec_result.max_score
        total_score = exec_result.primary_score if exec_result.primary_score is not None else 0.0
        percentage = round((total_score / max_score * 100), 1) if max_score > 0 else 0.0

        # Prepare tokens per second logic
        tps = 0.0
        if exec_result.execution_time > 0 and getattr(exec_result, "tokens_used", 0) > 0:
            tps = round(exec_result.tokens_used / exec_result.execution_time, 2)

        # Build dict from BenchmarkResult object + Scoring
        result = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": exec_result.status,
            "provider": provider,
            "model": model,
            "asset_id": asset_id,
            "asset_name": asset_name,
            "total_score": total_score,
            "max_score": max_score,
            "percentage": percentage,
            "tier": exec_result.tier,
            # Use object attributes
            "execution_time": round(exec_result.execution_time, 4),
            "tokens_used": getattr(exec_result, "tokens_used", 0),
            "tokens_per_second": tps,
            "load_time": round(getattr(exec_result, "load_time", 0.0), 4),
            "response_length": len(exec_result.raw_response),
            "finish_reason": getattr(exec_result, "finish_reason", None),
            "token_limit_cutoff": getattr(exec_result, "token_limit_cutoff", False),
            "token_limit_fallback": getattr(exec_result, "token_limit_fallback", False),
            "token_limit_used": getattr(exec_result, "token_limit_used", None),
            "tier": score.get("tier", "Tier 1 (Undefined)"),
        }

        # Add category scores
        for cat, val in score.get("category_scores", {}).items():
            result[cat] = f"{val['achieved']}/{val['max']}"

        return result
