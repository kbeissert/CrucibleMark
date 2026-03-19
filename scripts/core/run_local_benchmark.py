#!/usr/bin/env python3
"""Benchmark Runner für lokale Ollama-Modelle."""

import argparse
from utils.constants import OLLAMA_DEFAULT_BASE_URL
import logging
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from schemas.result import BenchmarkResult

# Optional: Direct Ollama access for low-level operations
try:
    import ollama
except ImportError:
    ollama = None  # type: ignore

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# pylint: disable=wrong-import-position, import-error, duplicate-code
from utils.base_runner import BaseBenchmarkRunner
from utils.benchmark_ui import TerminalUI
from utils.benchmark_utils import (
    discover_assets,
    load_asset_yaml,
    save_debug_response,
)
from utils.logging_config import setup_logging

from utils.model_utils import (
    get_model_version,
    get_ollama_models_info,
    is_reasoning_model,
)
from utils.module_registry import load_active_benchmarks
from utils.scoring.judge_evaluator import evaluate_with_judge, generate_audit_log
from utils.scoring_utils import calculate_score_contributions
from utils.adaptive_pause import AdaptivePauseCalculator, BenchmarkMode

# Setup Logging centrally
setup_logging()


# pylint: enable=wrong-import-position, import-error

logger = logging.getLogger(__name__)


class LocalBenchmarkRunner(BaseBenchmarkRunner):
    """Benchmark Runner für lokale Ollama-Modelle."""

    # Benchmark Constants
    TIER_SCORE_HIGH = 80
    TIER_SCORE_LOW = 50
    TOKEN_K_FACTOR = 1000

    def __init__(
        self,
        debug_responses: bool = False,
        mode: BenchmarkMode = BenchmarkMode.PRODUCTION,
        audit_mode: bool = False,
    ):
        """Initialisiert Runner."""
        super().__init__()
        # If mode is passed explicitly, use it. Otherwise fall back to Env Var if set.
        env_mode = os.getenv("CRUCIBLE_BM_MODE")
        if env_mode == "DEV":
            self.mode = BenchmarkMode.DEV
        else:
            self.mode = mode

        self.audit_mode = audit_mode
        self.commercial_csv = Path(
            self.validator.config.get("output", {}).get("commercial_csv", "benchmark_scores/commercial_models_benchmark.csv")
        )
        self.debug_responses = (
            debug_responses or os.getenv("CRUCIBLE_DEBUG", "false").lower() == "true"
        )

        # Cache for Cold Start measurements to prevent redundant unloads
        self.warmup_cache: set[str] = set()

        # Load modules from config (Hydrated via Registry)
        self.benchmark_categories = load_active_benchmarks(self.validator.config)

    @staticmethod
    def get_ollama_models() -> List[str]:
        """Holt verfügbare Ollama-Modelle via SSOT Utility."""
        infos = get_ollama_models_info()
        # Extract names from the SSOT-provided dicts
        return [m["name"] for m in infos]

    def select_model(self) -> Optional[str]:
        """Interaktive Modell-Auswahl."""
        models = self.get_ollama_models()
        if not models:
            print("\n❌ Keine Ollama-Modelle gefunden!")
            print("Installiere Modelle mit: ollama pull qwen2.5-coder:7b-instruct")
            return None

        selected = TerminalUI.select_from_list(
            models,
            lambda m: m,
            prompt="Wähle ein Modell",
            title="🤖 Verfügbare lokale Modelle (Ollama)",
        )

        if selected:
            print(f"✓ Ausgewählt: {selected}")
            if is_reasoning_model(selected):
                print("\n⚠️  ACHTUNG: Reasoning-Modell erkannt!")
                print("   Diese Modelle nutzen Chain-of-Thought (Denkprozess).")
                print("   Die Ausführung wird signifikant länger dauern!")
            print("")
        return selected

    def select_benchmark(self) -> Optional[Dict[str, Any]]:
        """Interaktive Benchmark-Auswahl."""
        categories = list(self.benchmark_categories.items())
        selected_item = TerminalUI.select_from_list(
            categories,
            lambda item: (item[1]["name"], item[1]["description"]),
            prompt="Wähle einen Benchmark",
            title="📊 Verfügbare Benchmarks",
        )
        if selected_item:
            key, info = selected_item
            print(f"✓ Ausgewählt: {info['name']}\n")
            return {"key": key, **info}
        return None

    def discover_assets(self, category_path: str) -> List[Path]:
        """Findet alle Assets in einer Kategorie."""
        assets = discover_assets(category_path)
        if not assets:
            path_obj = Path(category_path)
            if not path_obj.exists():
                raise ValueError(f"Kategorie-Pfad nicht gefunden: {category_path}")
            raise ValueError(f"Keine Assets gefunden in: {category_path}")
        return assets

    def _measure_cold_start(self, model: str) -> Optional[Dict[str, Any]]:
        """
        Sends a lightweight probe to the model.
        Phase 1: Force Unload (Reset State)
        Phase 2: Probe (Measure Load Time)
        """
        # Skip if already measured in this session (prevents redundant unloads)
        if hasattr(self, "warmup_cache") and model in self.warmup_cache:
            return None

        print("\nChecking Model Status (Warmup)... ", end="", flush=True)

        try:
            # 1. Force Unload to ensure we measure real Cold Start AND apply new num_ctx
            # Using generate with keep_alive=0 unwraps the model from VRAM
            if ollama:
                try:
                    ollama.generate(model=model, prompt="", keep_alive=0)
                    # Give Ollama a split second to clear memory
                    time.sleep(0.5)
                except Exception as e:  # pylint: disable=broad-exception-caught
                    logger.debug("Could not force unload model: %s", e)
            else:
                logger.debug("Ollama library not available for force unload")

            # 2. Send Probe (now guarantees a reload with new config)
            # Note: For Reasoning models (e.g. DeepSeek-R1), the response might be in 'thinking' only
            try:
                _ = self.client.query(
                    model=model,
                    prompt="Ping",
                    max_tokens=50,  # Increased for Reasoning models (was: 2)
                    temperature=0.0,
                )
                # If query succeeded, response will be a string (even if empty)
            except Exception as probe_error:  # pylint: disable=broad-exception-caught
                # Probe failed - this is not critical, just log and continue
                logger.warning("⚠️ Warmup Probe Failed: %s", probe_error)
                print("⚠️  Probe Failed (continuing anyway)")
                return None

            # Extract detected load time
            meta = getattr(self.client, "last_response_metadata", {})
            load_time = meta.get("load_duration", 0.0)

            # Formatting for user feedback
            if load_time > 2.0:
                print(f"❄️  Cold Start Detected: {load_time:.2f}s")
            else:
                print(f"🔥 Model Warm ({load_time:.2f}s)")

            # Cache success to avoid repeating for this model in this session
            if hasattr(self, "warmup_cache"):
                self.warmup_cache.add(model)

            # Create a synthetic result for the CSV
            # This ensures the Leaderboard calculator can pick up 'max(load_time)'
            # even if all subsequent tests run fast.
            return {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "success",
                "provider": "ollama",
                "model": model,
                "asset_id": "system_warmup_probe",
                "asset_name": "System: Cold Start Probe",
                "total_score": 0.0,
                "max_score": 0.0,
                "percentage": 0.0,
                "execution_time": 0.1,  # Irrelevant for this row
                "load_time": round(load_time, 4),
                "response_length": 0,
                "tier": "Tier 0 (System)",
                "category": "System",
                "routine_contribution": 0,
                "reasoning_contribution": 0,
            }

        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"⚠️ Warmup Probe Failed: {e}")
            return None

    def _execute_test(
        self, model: str, asset_path: Path, benchmark_info: Dict[str, Any]
    ):
        """Executes the test using the dynamically loaded test class."""
        return self.execute_test_module(
            model, asset_path, benchmark_info, provider="ollama"
        )

    def _create_error_result(
        self, asset_path: Path, error_message: str
    ) -> Dict[str, Any]:
        """Creates an error result dictionary."""
        return {
            "status": "error",
            "error_message": error_message,
            "asset_id": asset_path.stem,
            "asset_name": asset_path.stem,
            "percentage": 0,
            "tier": "Tier 1",
            "execution_time": 0,
            "total_score": 0,
            "max_score": 0,
        }

    def _process_single_test(
        self,
        model: str,
        asset_path: Path,
        benchmark_info: Dict[str, Any],
        pause_calculator: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Führt einzelnen Test aus."""
        asset_data = load_asset_yaml(asset_path)
        if not asset_data:
            return self._create_error_result(asset_path, "Empty/Invalid Asset File")

        try:
            start_time = time.time()
            test_instance, exec_result = self._execute_test(
                model, asset_path, benchmark_info
            )
            if not exec_result.execution_time:
                exec_result.execution_time = time.time() - start_time
        except (FileNotFoundError, ImportError, AttributeError) as e:
            return self._create_error_result(asset_path, str(e))

        response = exec_result.raw_response
        exec_result = test_instance.score_response(exec_result)
        score = exec_result.data

        # Comparisons
        asset_id = asset_data.get("metadata", {}).get("id", asset_path.stem)

        # Build Result
        result = self._build_result_dict(
            model=model,
            asset_data=asset_data,
            exec_result=exec_result,
            response_preview=response,
        )

        # Calculates granular score contribution if configured
        benchmarks_list = benchmark_info.get("benchmarks", [])
        asset_id = result["asset_id"]
        # Find config for this asset
        asset_cfg = next((b for b in benchmarks_list if b["id"] == asset_id), None)

        # Calculate initial score contributions (based on Regex) for tracking/debug
        result = calculate_score_contributions(result, asset_cfg)

        # ---------------------------------------------------------------------
        # PHASE 2.5: LLM JUDGE INTEGRATION
        # ---------------------------------------------------------------------
        # Guaranteed Defaults
        for key in [
            "llm_judge_score",
            "llm_judge_reasoning",
            "llm_judge_latency_ms",
            "llm_judge_provider_used",
            "llm_judge_model_used",
            "llm_judge_parse_success",
            "judge_task_compliance",
            "judge_output_quality",
            "judge_standard_adherence",
        ]:
            result[key] = None

        result["scoring_method"] = "regex_fallback"

        judge_cfg_dict = self.validator.config.get("llm_judge", {})
        is_enabled = judge_cfg_dict.get("enabled", True)
        eval_module_id = benchmark_info.get("id", "")
        applicable_modules = judge_cfg_dict.get("applicable_modules") or []

        if is_enabled and eval_module_id in applicable_modules:
            if len(response.strip()) < 15:
                result["judge_progress_status"] = "⚠️ Judge: skip"
            else:
                # 3. Local Runner: AdaptivePauseCalculator/Ollama cooldown executed
                if pause_calculator:
                    current_stats = {
                        "execution_time": result.get("execution_time", 0),
                        "response_length": result.get("tokens_used", 0) * 4,
                    }
                    pause_calculator.wait(current_stats)

                # 5. Local Runner: Unload the TESTED Ollama model (free VRAM)
                import requests as _requests

                try:
                    _requests.post(
                        f"{OLLAMA_DEFAULT_BASE_URL}/api/generate",
                        json={"model": model, "keep_alive": 0},
                        timeout=5,
                    )
                except Exception:  # pylint: disable=broad-exception-caught
                    pass

                time.sleep(0.5)

                # 6. JudgeRunner instantiated & .score() called
                result = evaluate_with_judge(
                    result=result,
                    response=response,
                    asset_data=asset_data,
                    judge_cfg_dict=judge_cfg_dict,
                    eval_module_id=eval_module_id,
                    model=model,
                    asset_cfg=asset_cfg,
                    benchmark_info=benchmark_info
                )

        if getattr(self, "audit_mode", False):
            generate_audit_log(
                result=result,
                exec_result=exec_result,
                asset_data=asset_data,
                response=response,
                score=score
            )

        return result

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def _build_result_dict(
        self,
        model: str,
        asset_data: Dict[str, Any],
        exec_result: BenchmarkResult,
        response_preview: str,
    ) -> Dict[str, Any]:
        """Helper to construct the result dictionary."""
        # Use base runner implementation
        result = self.build_base_result(model, asset_data, exec_result, "ollama")

        # Add Model Version (ID)
        # Use cached global unified version if available
        if hasattr(self, "current_model_version") and self.current_model_version:
            result["model_version"] = self.current_model_version
        else:
            # Fallback (should not happen in standard runs)
            result["model_version"] = get_model_version(model, provider="ollama")

        # Add Token Usage (Prefer centralized tracking from client)
        tokens = 0
        if hasattr(self.client, "last_token_usage"):
            tokens = self.client.last_token_usage
        else:
            tokens = exec_result.tokens_used or 0

        result["tokens_used"] = tokens
        result["cost_usd"] = 0.0  # Local models are free

        # Add local benchmark specifics
        result.update(
            {
                "golden_similarity": 0.0,
            }
        )

        if response_preview.startswith("ERROR:"):
            result["error_message"] = response_preview
        elif not response_preview:
            result["error_message"] = "Empty Response"

        # Ensure tier is set if missing (legacy field support)
        if "tier" not in result:
            result["tier"] = "Tier 1 (Undefined)"

        # Debug Auto-Save Logic
        if result["percentage"] < 30 or getattr(self, "debug_responses", False):
            save_debug_response(
                result["model"],
                result["asset_id"],
                response_preview,
                f"{result['total_score']}/{result['max_score']} ({result['percentage']}%)",
                exec_result.data.get("reasoning", "No explanation provided"),
            )
        return result

    def _create_standard_result_from_batch(
        self,
        model: str,
        report: Dict[str, Any],
        result_wrapper: BenchmarkResult,
        model_version: str = "unknown",
        benchmark_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Erstellt ein Standard-Resultat aus einem Batch-Report."""
        benchmark_info = benchmark_info or {}
        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": report.get("status", "success"),
            "provider": "ollama",
            "model": model,
            "model_version": model_version,
            "asset_id": benchmark_info.get("id", "batch_module"),
            "asset_name": benchmark_info.get("name", "Batch Module"),
            "total_score": report.get("total_score", report.get("score", 0.0)),
            "max_score": 100,
            "percentage": report.get("total_score", report.get("score", 0.0)),
            "execution_time": round(result_wrapper.execution_time or 0, 1),
            "response_length": 0,
            "tier": report.get("tier", "N/A"),
            "cost_usd": report.get("statistics", {}).get("total_cost", 0.0),
            "tokens": report.get("statistics", {}).get("total_tokens", 0),
            "tokens_used": report.get("statistics", {}).get("total_tokens", 0),
        }


    def _run_standard_benchmark(
        self,
        model: str,
        benchmark_info: Dict[str, Any],
        assets: Optional[List[Path]] = None,
    ) -> List[Dict[str, Any]]:
        """Führt Standard-Benchmarks (Asset-basiert) aus."""

        # --- WARMUP / COLD START PROBE ---
        # Führt eine "Dummy"-Anfrage aus, um den Kaltstart separat zu messen.
        # Dies verhindert, dass der erste eigentliche Benchmark durch Ladezeiten verfälscht wird.
        warmup_result = self._measure_cold_start(model)

        # --- VERSIONING ---
        # Local model version is derived from Ollama model ID via get_model_version().
        self.current_model_version = get_model_version(model, provider="ollama")
        # ------------------

        # Use filtered assets if provided, otherwise discover all
        if assets is None:
            assets = self.discover_assets(benchmark_info["path"])

        results = []

        # Inject Warmup Result if available
        if warmup_result:
            # We enrich it with version info now that we have it
            warmup_result["model_version"] = self.current_model_version
            results.append(warmup_result)

        if not assets:
            print(f"⚠️  Keine Tests für {benchmark_info['name']} gefunden/ausstehend.")
            return (
                results  # Return results (might contain warmup) instead of empty list
            )

        print(
            f"\n{'=' * 60}\n📊 Starte Benchmark: {benchmark_info['name']}\n{'=' * 60}"
        )
        print(f"Modell: {model}\nTests: {len(assets)}\n{'=' * 60}\n")

        # Initialize Adaptive Pause Calculator
        pause_calculator = AdaptivePauseCalculator(model_name=model, mode=self.mode)

        results = []
        print("Fortschritt:")

        for i, asset_path in enumerate(assets, 1):
            # ADAPTIVE PAUSE: Moved to INSIDE _process_single_test for LLM Judge integration!

            asset_name = asset_path.stem.replace("asset_", "").replace("_", " ").title()
            print(
                f"   ⏳ [{i}/{len(assets)}] {asset_name}: Test läuft...",
                end="\r",
                flush=True,
            )

            try:
                result = self._process_single_test(
                    model, asset_path, benchmark_info, pause_calculator
                )

                results.append(result)
                self._print_result_status(i, len(assets), asset_name, result)
            except Exception as e:  # pylint: disable=broad-exception-caught  # pylint: disable=broad-exception-caught
                print(" " * 80, end="\r")
                print(
                    f"   ✗ [{i}/{len(assets)}] {asset_name}: Abgebrochen - {str(e)[:50]}"
                )

        return results

    def run_benchmark(
        self,
        model: str,
        benchmark_info: Dict[str, Any],
        num_runs: int = 1,
        assets: Optional[List[Path]] = None,
    ) -> List[Dict[str, Any]]:
        """Führt Benchmark für gewähltes Modell durch."""

        # Dispatch Batch Mode (e.g. Political Compass) via Config
        if benchmark_info.get("execution_mode") == "batch":
            return self.execute_batch_module(model=model, benchmark_info=benchmark_info, provider="ollama", num_runs=num_runs, existing_benchmarks=None)

        return self._run_standard_benchmark(model, benchmark_info, assets)

    def _print_result_status(
        self, idx: int, total: int, name: str, result: Dict[str, Any]
    ):
        """Prints the result of a single test line."""
        print(" " * 80, end="\r")

        if result.get("status") == "error":
            msg = result.get("error_message", "Error")
            msg_str = f"FAILED ({msg}) | Time: {result['execution_time']}s"
            print(f"   ✗ [{idx}/{total}] {name}: {msg_str}")
            return

        quality = self.get_quality_badge(result["percentage"])

        # Format tokens
        t_count = result.get("tokens_used", 0)
        token_str = (
            f"{t_count / self.TOKEN_K_FACTOR:.1f}k T"
            if t_count > self.TOKEN_K_FACTOR
            else f"{t_count} T"
        )

        base_msg = (
            f"   ✓ [{idx}/{total}] {name:<25}: {result['percentage']:>6.2f}% {quality} "
        )
        judge_status = result.get("judge_progress_status", "")
        judge_str = f" | {judge_status}" if judge_status else ""

        if result.get("reference_score", 0) > 0:
            diff = result["score_difference"]
            sym = "+" if diff > 0 else ""
            # e.g. | vs Ref: +2.0 🟢 | 1.2k T | 12.3s
            icon = "🟢" if diff >= 0 else "🔴"
            print(
                f"{base_msg}| vs Ref: {sym}{diff:.1f} {icon} | {token_str:>7} | {result['execution_time']:>5.1f}s{judge_str}"
            )
        else:
            print(
                f"{base_msg}| {token_str:>7} | {result['execution_time']:>5.1f}s{judge_str}"
            )


def main():
    """CLI Entry Point."""
    parser = argparse.ArgumentParser(description="CrucibleMark Local Benchmark Runner")
    parser.add_argument(
        "--debug-responses",
        action="store_true",
        help="Save all responses to debug files",
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Run in DEV mode (Fast iteration, shorter pauses). Default is PRODUCTION.",
    )
    args, _ = parser.parse_known_args()

    # Determine Benchmark Mode
    mode = BenchmarkMode.DEV if args.dev else BenchmarkMode.PRODUCTION

    runner = LocalBenchmarkRunner(debug_responses=args.debug_responses, mode=mode)
    print(f"\n{'=' * 60}\n🚀 LOKALE MODELLE BENCHMARK\n{'=' * 60}")
    print(f"Modus: {mode.value.upper()} (Adaptive Pausen aktiviert)")

    model = runner.select_model()
    if not model:
        sys.exit(1)

    benchmark = runner.select_benchmark()
    if not benchmark:
        sys.exit(1)

    try:
        results = runner.run_benchmark(model, benchmark)
        runner.save_results(results, result_type="local")
        runner.print_summary(results, model=model)

    except Exception as e:  # pylint: disable=broad-exception-caught  # pylint: disable=broad-exception-caught
        print(f"\n❌ Fehler beim Benchmark: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
    print(f"\n{'=' * 60}")
    print("🏁 BENCHMARK ABGESCHLOSSEN")
    print("Alle Ergebnisse wurden in den Benchmark Scores erfasst.")
    print(f"{'=' * 60}\n")
