#!/usr/bin/env python3
"""Benchmark Runner für lokale Ollama-Modelle."""

import argparse
import csv
import json
import logging
import os
import subprocess
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
    ollama = None

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# pylint: disable=wrong-import-position, import-error, duplicate-code
from utils.base_runner import BaseBenchmarkRunner
from utils.benchmark_ui import TerminalUI
from utils.benchmark_utils import (
    discover_assets,
    format_pc_run_data,
    load_asset_yaml,
    save_debug_response,
)
from utils.llm_client import LLMClient
from utils.logging_config import setup_logging

from utils.model_utils import (
    get_model_version,
    get_ollama_models_info,
    is_reasoning_model
)
from utils.fingerprinting import ModelFingerprinter
from utils.module_loader import load_test_class
from utils.module_registry import load_active_benchmarks
from utils.scoring_utils import calculate_score_contributions
from utils.adaptive_pause import AdaptivePauseCalculator, BenchmarkMode

# Setup Logging centrally
setup_logging()

# Optional: Tightly coupled for now, should be decoupled later
# pylint: disable=invalid-name
RESULT_MANAGER = None
try:
    from benchmark_modules.political_compass.core.io_manager import ResultManager as RM

    RESULT_MANAGER = RM
except ImportError:
    pass
# pylint: enable=invalid-name

# pylint: enable=wrong-import-position, import-error

logger = logging.getLogger(__name__)


class LocalBenchmarkRunner(BaseBenchmarkRunner):
    """Benchmark Runner für lokale Ollama-Modelle."""

    # Benchmark Constants
    TIER_SCORE_HIGH = 80
    TIER_SCORE_LOW = 50
    TOKEN_K_FACTOR = 1000

    def __init__(self, debug_responses: bool = False, mode: BenchmarkMode = BenchmarkMode.PRODUCTION):
        """Initialisiert Runner."""
        super().__init__()
        # If mode is passed explicitly, use it. Otherwise fall back to Env Var if set.
        env_mode = os.getenv("CRUCIBLE_BM_MODE")
        if env_mode == "DEV":
            self.mode = BenchmarkMode.DEV
        else:
            self.mode = mode
            
        self.commercial_csv = self.validator.get_golden_standard_csv()
        self.debug_responses = (
            debug_responses or os.getenv("CRUCIBLE_DEBUG", "false").lower() == "true"
        )
        
        # Cache for Cold Start measurements to prevent redundant unloads
        self.warmup_cache = set()

        # Load modules from config (Hydrated via Registry)
        self.benchmark_categories = load_active_benchmarks(self.validator.config)

    @staticmethod
    def get_ollama_models() -> List[str]:
        """Holt verfügbare Ollama-Modelle via SSOT Utility."""
        infos = get_ollama_models_info()
        # Extract names from the SSOT-provided dicts
        return [m["name"] for m in infos]

    def load_commercial_references(self) -> Dict[str, Dict[str, Any]]:
        """Lädt kommerzielle Referenzwerte aus CSV."""
        if not self.commercial_csv.exists():
            return {}

        references = {}
        try:
            with open(self.commercial_csv, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    asset_id = row.get("asset_id", "")
                    model = row.get("model", "")
                    if asset_id and model:
                        references[asset_id] = {
                            "model": model,
                            "provider": row.get("provider", ""),
                            "score": float(row.get("total_score", 0)),
                            "percentage": float(row.get("percentage", 0)),
                        }
        except (OSError, ValueError) as e:
            logger.warning("Fehler beim Laden der Referenzen: %s", e)

        return references

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
                except Exception as e:
                    logger.debug("Could not force unload model: %s", e)
            else:
                logger.debug("Ollama library not available for force unload")

            # 2. Send Probe (now guarantees a reload with new config)
            # Note: For Reasoning models (e.g. DeepSeek-R1), the response might be in 'thinking' only
            try:
                response = self.client.query(
                    model=model,
                    prompt="Ping",
                    max_tokens=50,  # Increased for Reasoning models (was: 2)
                    temperature=0.0
                )
                # If query succeeded, response will be a string (even if empty)
            except Exception as probe_error:
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
                "reasoning_contribution": 0
            }

        except Exception as e:
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

    def _compare_golden(
        self, asset_data: Dict[str, Any], response: str, test_instance: Any
    ) -> Dict[str, Any]:
        """Compares response with golden standard."""
        asset_id = asset_data.get("metadata", {}).get("id", "unknown")
        golden_config = asset_data.get("golden_standard", {})
        provider = golden_config.get("generate_with", [{}])[0].get(
            "provider", "mistral"
        )
        golden_path = Path(f"golden_standards/{provider}/{asset_id}.json")
        return test_instance.compare_to_golden_standard(response, golden_path)

    def _process_single_test(
        self,
        model: str,
        asset_path: Path,
        commercial_refs: Dict[str, Dict[str, Any]],
        benchmark_info: Dict[str, Any],
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
        score = test_instance.score_response(response)

        # Comparisons
        comparison = self._compare_golden(asset_data, response, test_instance)
        asset_id = asset_data.get("metadata", {}).get("id", asset_path.stem)
        ref = commercial_refs.get(asset_id, {})

        # Build Result
        result = self._build_result_dict(
            model=model,
            asset_data=asset_data,
            score=score,
            exec_result=exec_result,
            _ref=ref,
            comparison=comparison,
            response_preview=response,
        )

        # Calculates granular score contribution if configured
        benchmarks_list = benchmark_info.get("benchmarks", [])
        asset_id = result["asset_id"]
        # Find config for this asset
        asset_cfg = next((b for b in benchmarks_list if b["id"] == asset_id), None)

        result = calculate_score_contributions(result, asset_cfg)

        return result

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def _build_result_dict(
        self,
        model: str,
        asset_data: Dict[str, Any],
        score: Dict[str, Any],
        exec_result: BenchmarkResult,
        _ref: Dict[str, Any],
        comparison: Dict[str, Any],
        response_preview: str,
    ) -> Dict[str, Any]:
        """Helper to construct the result dictionary."""
        # Use base runner implementation
        result = self.build_base_result(model, asset_data, score, exec_result, "ollama")

        # Add Model Version (ID)
        # Use cached global unified version if available
        if hasattr(self, "current_model_version") and self.current_model_version:
            result["model_version"] = self.current_model_version
        else:
            # Fallback (should not happen in standard runs)
            result["model_version"] = ModelFingerprinter.get_unified_version(
                provider="ollama", model_name=model
            )

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
                "golden_similarity": round(comparison.get("similarity", 0) * 100, 1),
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
                score.get("reasoning", "No explanation provided"),
            )

        return result

    def _setup_benchmark_resources(self) -> tuple[Dict[str, Dict[str, Any]], bool]:
        """Loads and validates validation/reference resources."""
        is_valid, message = self.validator.validate_golden_standard()
        print(
            f"\n{'=' * 60}\n🔍 GOLDEN STANDARD VALIDIERUNG\n{'=' * 60}\n{message}\n{'=' * 60}"
        )

        commercial_refs = self.load_commercial_references()
        if commercial_refs:
            print(f"\n📌 Golden Standard Scores geladen: {len(commercial_refs)} Assets")
            first_asset = list(commercial_refs.values())[0]
            print(f"   Referenz: {first_asset['model']} ({first_asset['provider']})")
        elif is_valid:
            print("\n⚠️  Golden Standard CSV noch nicht vorhanden.")
        else:
            print("\n⚠️  Golden Standard nicht verfügbar.")

        return commercial_refs, is_valid

    def _update_political_compass_csv(
        self, model: str, report: Dict[str, Any], _model_version: str = "unknown"
    ) -> None:
        """
        Aktualisiert die Leaderboard-CSV für Batch-Tests (Append-Only).
        Uses the Standard V2 Schema defined in political_compass/core/io_manager.py
        to ensure compatibility with other tools.
        """
        pc_csv = Path("benchmark_scores/political_compass_results.csv")
        pc_csv.parent.mkdir(exist_ok=True, parents=True)

        # Standard V2 Schema (Aligned with Commercial Runner)
        fieldnames = [
            "model",
            "model_version",
            "run_id",
            "x_coordinate",
            "y_coordinate",
            "x_label",
            "y_label",
            "metrics_json",
            "timestamp",
        ]

        file_exists = pc_csv.exists() and pc_csv.stat().st_size > 0

        rows_to_write = []

        # Calculate execution time from statistics if available
        # exec_time = 0.0 hiding unused variable warning if removed completely
        if "statistics" in report:
            _ = report["statistics"].get("execution_time", 0.0)

        timestamp_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")

        # 1. Archive individual runs
        if "individual_runs" in report:
            for i, run in enumerate(report["individual_runs"], 1):
                run_formatted = format_pc_run_data(run, include_extremism=False)

                rows_to_write.append(
                    {
                        "model": model,
                        "model_version": _model_version,
                        "run_id": f"RUN_{run.get('id', i)}",
                        "x_coordinate": run.get("x", 0.0),
                        "y_coordinate": run.get("y", 0.0),
                        "x_label": run.get("x_label", ""),
                        "y_label": run.get("y_label", ""),
                        "metrics_json": json.dumps(run_formatted, ensure_ascii=False),
                        "timestamp": timestamp_str,
                    }
                )

        # 2. Archive Average / Total Result
        avg_formatted = format_pc_run_data(
            {
                "x": report["coordinates"]["x"],
                "y": report["coordinates"]["y"],
                "x_label": report["archetype"]["x_label"],
                "y_label": report["archetype"]["y_label"],
                "extremism": report.get("extremism", {}),
                "sigma": report.get("sigma", {}),
                "module_stats": report.get("statistics", {}).get("module_stats", {}),
            },
            include_extremism=True,
        )

        rows_to_write.append(
            {
                "model": model,
                "model_version": _model_version,
                "run_id": "AVG",
                "x_coordinate": report["coordinates"]["x"],
                "y_coordinate": report["coordinates"]["y"],
                "x_label": report.get("archetype", {}).get("x_label", ""),
                "y_label": report.get("archetype", {}).get("y_label", ""),
                "metrics_json": json.dumps(avg_formatted, ensure_ascii=False),
                "timestamp": timestamp_str,
            }
        )

        try:
            with open(pc_csv, "a", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
                if not file_exists:
                    writer.writeheader()
                writer.writerows(rows_to_write)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Fehler beim Schreiben der CSV: %s", e)

    def _create_standard_result_from_batch(
        self,
        model: str,
        report: Dict[str, Any],
        result_wrapper: BenchmarkResult,
        model_version: str = "unknown",
    ) -> Dict[str, Any]:
        """Erstellt ein Standard-Resultat aus einem Batch-Report."""
        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": report.get("status", "success"),
            "provider": "ollama",
            "model": model,
            "model_version": model_version,
            "asset_id": "political_compass_v3",
            "asset_name": "Political Compass",
            "total_score": report["total_score"],
            "max_score": 100,
            "percentage": report["total_score"],
            "execution_time": round(result_wrapper.execution_time or 0, 1),
            "response_length": 0,
            "tier": report.get("tier", "N/A"),
            "cost_usd": report.get("statistics", {}).get("total_cost", 0.0),
            "tokens": report.get("statistics", {}).get("total_tokens", 0),
            "tokens_used": report.get("statistics", {}).get("total_tokens", 0),
        }

    def _run_batch_benchmark(
        self, model: str, benchmark_info: Dict[str, Any], num_runs: int
    ) -> List[Dict[str, Any]]:
        """Führt Batch-Module (z.B. Political Compass) aus."""
        module_path = Path(benchmark_info.get("module_path", ""))
        test_file = module_path / "test.py"
        test_class_name = benchmark_info.get("test_class")

        if not test_class_name or not isinstance(test_class_name, str):
            logger.error(
                "Keine gültige Test-Klasse für %s definiert.", benchmark_info["name"]
            )
            return []

        try:
            test_class_type = load_test_class(test_file, test_class_name)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(
                "Failed to load batch module %s: %s", benchmark_info["name"], e
            )
            return []

        # pylint: disable=fixme
        # TODO: Generic ResultManager for batch modules
        print(f"🛠️  Initialisiere Batch-Test: {benchmark_info['name']} ({model})")
        test = test_class_type()

        assets_dir = module_path / "assets"
        if not assets_dir.exists():
            print(f"❌ Assets directory not found: {assets_dir}")
            return []

        if hasattr(test, "load_questions"):
            test.load_questions(str(assets_dir))

        if hasattr(test, "questions") and not test.questions:
            print("❌ Keine Fragen geladen!")
            return []

        min_runs = benchmark_info.get("min_runs", 1)
        test.num_runs = max(num_runs, min_runs)

        client = LLMClient(config=self.validator.config)

        # Execution
        result_wrapper = test.execute(model=model, llm_client=client, provider="ollama")

        # Reporting
        report = json.loads(result_wrapper.raw_response)

        # Get Model Version
        model_version = get_model_version(model, provider="ollama")

        if RESULT_MANAGER:
            RESULT_MANAGER.print_summary(report)
            output_dir = Path("outputs/runs")
            RESULT_MANAGER.save_json(report, output_dir)
            
            # Auto-Trigger Bias Analysis (if Political Compass)
            if benchmark_info.get("id", "") == "political_compass_v3":
                 try:
                     print("📊 Updating Bias Sensitivity Report...")
                     subprocess.run(
                        [sys.executable, "scripts/analysis/update_bias_report.py"], 
                        check=False,
                        capture_output=False
                    )
                 except Exception as e:
                     logger.warning("Could not update bias report: %s", e)

        self._update_political_compass_csv(model, report, _model_version=model_version)

        return [
            self._create_standard_result_from_batch(
                model, report, result_wrapper, model_version=model_version
            )
        ]

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
        # Get unified version (Format: {local_digest}-nohash)
        # We assume local execution doesn't do rigorous behavioral hashing yet for speed.
        # But we adhere to the global format.
        self.current_model_version = ModelFingerprinter.get_unified_version(
            provider="ollama",
            model_name=model
        )
        # ------------------
        
        commercial_refs, _ = self._setup_benchmark_resources()

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
            return results # Return results (might contain warmup) instead of empty list

        print(
            f"\n{'=' * 60}\n📊 Starte Benchmark: {benchmark_info['name']}\n{'=' * 60}"
        )
        print(f"Modell: {model}\nTests: {len(assets)}\n{'=' * 60}\n")

        # Initialize Adaptive Pause Calculator
        pause_calculator = AdaptivePauseCalculator(model_name=model, mode=self.mode)

        results = []
        print("Fortschritt:")

        previous_test_stats = None

        for i, asset_path in enumerate(assets, 1):
            # ADAPTIVE PAUSE
            pause_calculator.wait(previous_test_stats)

            asset_name = asset_path.stem.replace("asset_", "").replace("_", " ").title()
            print(
                f"   ⏳ [{i}/{len(assets)}] {asset_name}: Test läuft...",
                end="\r",
                flush=True,
            )

            try:
                result = self._process_single_test(
                    model, asset_path, commercial_refs, benchmark_info
                )
                
                # Update stats for next iteration
                previous_test_stats = {
                    'execution_time': result.get('execution_time', 0),
                    'response_length': result.get('tokens_used', 0) * 4  # Estimate chars from tokens
                }

                results.append(result)
                self._print_result_status(i, len(assets), asset_name, result)
            except Exception as e:  # pylint: disable=broad-exception-caught
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
            return self._run_batch_benchmark(model, benchmark_info, num_runs)

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
            f"   ✓ [{idx}/{total}] {name:<25}: {result['percentage']:>5.1f}% {quality} "
        )

        if result.get("reference_score", 0) > 0:
            diff = result["score_difference"]
            sym = "+" if diff > 0 else ""
            # e.g. | vs Ref: +2.0 🟢 | 1.2k T | 12.3s
            icon = "🟢" if diff >= 0 else "🔴"
            print(
                f"{base_msg}| vs Ref: {sym}{diff:.1f} {icon} | {token_str:>7} | {result['execution_time']:>5.1f}s"
            )
        else:
            print(f"{base_msg}| {token_str:>7} | {result['execution_time']:>5.1f}s")

    def save_results(self, results: List[Dict[str, Any]]) -> None:
        """Speichert Ergebnisse in CSV via ResultManager."""
        self.result_manager.save_results(results, result_type="local")

    def print_summary(self, results: List[Dict[str, Any]], model: str) -> None:
        """Druckt Zusammenfassung."""
        if not results:
            return

        successful = [r for r in results if r.get("status") != "error"]
        failed = [r for r in results if r.get("status") == "error"]

        # Separate Probe Result from Scoring
        probe_result = next((r for r in successful if r.get("asset_id") == "system_warmup_probe"), None)
        # Filter probe out of scoring results
        scoring_candidates = [r for r in successful if r.get("asset_id") != "system_warmup_probe"]

        if not scoring_candidates and not probe_result:
            print(f"\n{'=' * 60}\n📈 BENCHMARK ZUSAMMENFASSUNG\n{'=' * 60}")
            print(f"Modell: {model}\n❌ Alle {len(results)} Tests fehlgeschlagen!")
            return

        # Calculate averages (excluding Political Compass if it's the only test)
        # Filter out political compass for average score calculation because it's qualitative
        scored_results = [
            r
            for r in scoring_candidates
            if not str(r.get("asset_id", "")).startswith("political_compass")
        ]

        if not scored_results:
             # If only Political Compass (or just Probe?) ran
            if scoring_candidates: # If we have actual tests (e.g. Political Compass)
                avg_time = sum(r["execution_time"] for r in scoring_candidates) / len(scoring_candidates)
                print("\n✅ Benchmark abgeschlossen für Modul: Political Compass")
                print(f"   Modell: {model}")
                print(f"   Dauer:  {avg_time:.1f}s")
                
                # Print specific PC info instead of score
                for r in scoring_candidates:
                    if "tier" in r:
                        print(f"   Resultat: {r['tier']}")
            elif probe_result:
                # Only Probe ran (unlikely, but safe)
                print(f"\n⚠️ Nur System Probe ausgeführt.")
            
            return

        avg_score = sum(r["total_score"] for r in scored_results) / len(scored_results)
        avg_max = sum(r["max_score"] for r in scored_results) / len(scored_results)
        avg_pct = sum(r["percentage"] for r in scored_results) / len(scored_results)
        avg_time = sum(r["execution_time"] for r in successful if r.get("asset_id") != "system_warmup_probe") / len(scored_results)

        quality = self.get_quality_badge(avg_pct)

        print(f"\n✅ Modul abgeschlossen: {model}")
        print(f"Tests: {len(scoring_candidates)} ({len(scoring_candidates)} ✅, {len(failed)} ❌)")
        print("\n📊 Durchschnitt (erfolgreiche Tests des Moduls):")
        print(
            f"   Dein Modell: {avg_score:.1f}/{avg_max:.0f} ({avg_pct:.1f}%) {quality}"
        )
        print(f"   Avg Speed:   {avg_time:.1f}s (Execution)")
        
        if probe_result:
            load_time = probe_result.get("load_time", 0)
            print(f"   Cold Start:  {load_time:.2f}s (Initial Load)")

        self._print_reference_comparison(successful)
        self._print_best_worst(successful)
        self._print_tiered_analysis(successful)

        if failed:
            print("\n❌ Fehlgeschlagen:")
            for r in failed:
                print(f"   {r['asset_name'][:40]}: {r.get('error_message')}")
        print(f"{'=' * 60}")

    def _print_reference_comparison(self, results: List[Dict[str, Any]]):
        """Prints comparison to commercial reference."""
        if not results or results[0].get("reference_score", 0) <= 0:
            return

        avg_ref = sum(r.get("reference_score", 0) for r in results) / len(results)
        avg_diff = sum(r.get("score_difference", 0) for r in results) / len(results)

        print(f"   Referenz:    {avg_ref:.1f}/100")
        if avg_diff > 0:
            print(f"   🎯 Differenz: +{avg_diff:.1f} (besser!)")
            print(f"\n   {'=' * 60}")
            print(
                f"   ⚠️  ACHTUNG: GOLDEN STANDARD ÜBERTROFFEN! (Ratio: {100 + avg_diff:.1f}%)"
            )
            print(f"   {'=' * 60}")
            print("   Dieses Modell übertrifft die kommerzielle Referenz.")
            print(
                "   Bitte Ergebnisse prüfen (und ggf. Golden Standard aktualisieren)."
            )
        elif avg_diff < 0:
            print(f"   📉 Differenz: {avg_diff:.1f} (Gap)")
        else:
            print("   ⚖️  Differenz: ±0")

    def _print_best_worst(self, results: List[Dict[str, Any]]):
        """Prints best and worst performing tests."""
        if not results:
            return

        sorted_res = sorted(results, key=lambda x: x["percentage"], reverse=True)

        print("\n🏆 Beste Tests:")
        for r in sorted_res[:3]:
            q = self.get_quality_badge(r["percentage"])
            d = r.get("score_difference", 0)
            diff_str = f" ({d:+.1f})" if d != 0 else ""
            print(f"   {r['asset_name'][:35]:<35}: {r['percentage']}% {q}{diff_str}")

        print("\n⚠️  Schwächste Tests:")
        for r in sorted_res[-3:]:
            q = self.get_quality_badge(r["percentage"])
            d = r.get("score_difference", 0)
            diff_str = f" ({d:+.1f})" if d != 0 else ""
            print(f"   {r['asset_name'][:35]:<35}: {r['percentage']}% {q}{diff_str}")

    def _print_tiered_analysis(self, results: List[Dict[str, Any]]):
        """Prints Tiered Reasoning Analysis if applicable."""
        reasoning_res = [
            r
            for r in results
            if r.get("details", {}).get("asset_id", "").startswith("reasoning_")
        ]
        if not reasoning_res:
            return

        print(f"\n🧠 REASONING ANALYSIS (Tiered)\n{'-' * 60}")
        t1_scores = [
            r["total_score"]
            for r in reasoning_res
            if "Tier 1" in r.get("details", {}).get("tier", "Tier 1")
        ]
        t2_scores = [
            r["total_score"]
            for r in reasoning_res
            if "Tier 2" in r.get("details", {}).get("tier", "")
        ]

        t1_avg = sum(t1_scores) / len(t1_scores) if t1_scores else 0
        t2_avg = sum(t2_scores) / len(t2_scores) if t2_scores else 0

        profile = "🤖  Balanced"
        if t2_avg > self.TIER_SCORE_HIGH:
            profile = "🧠  Deep Thinker (Complex Logic Expert)"
        elif t1_avg >= self.TIER_SCORE_HIGH:
            profile = "🏎️  Daily Driver (Fast & Reliable)"
        elif t1_avg < self.TIER_SCORE_LOW:
            profile = "⚠️  Needs Improvement"

        print(f"   Tier 1 (Operational): {t1_avg:.1f}%")
        print(f"   Tier 2 (Deep Logic):  {t2_avg:.1f}%")
        print(f"   Profile: {profile}\n{'-' * 60}")




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
        runner.save_results(results)
        runner.print_summary(results, model)

    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"\n❌ Fehler beim Benchmark: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
    print(f"\n{'=' * 60}")
    print("🏁 BENCHMARK ABGESCHLOSSEN")
    print("Alle Ergebnisse wurden in den Benchmark Scores erfasst.")
    print(f"{'=' * 60}\n")
