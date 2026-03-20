#!/usr/bin/env python3
"""Benchmark Runner für kommerzielle API-basierte Modelle."""

from utils.scoring.judge_evaluator import evaluate_with_judge, generate_audit_log
import sys
import logging
import json
import csv
import argparse
import traceback
import time
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from schemas.result import BenchmarkResult

# Suppress verbose HTTP logging
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# pylint: disable=wrong-import-position, import-error
from utils.base_runner import BaseBenchmarkRunner  # noqa: E402
from utils.module_loader import load_test_class  # noqa: E402
from utils.benchmark_utils import (
    select_from_list,
    discover_assets,
    load_asset_yaml,
)  # noqa: E402
from utils.model_utils import get_model_version  # noqa: E402
from utils.module_registry import load_active_benchmarks  # noqa: E402
from utils.scoring_utils import (
    calculate_score_contributions,
)  # noqa: E402
from utils.rate_limiter import RateLimiter  # noqa: E402

logger = logging.getLogger(__name__)

class CommercialBenchmarkRunner(BaseBenchmarkRunner):
    """Benchmark Runner für kommerzielle API-basierte Modelle."""

    benchmark_categories: Dict[str, Any] = {}

    def __init__(
        self, force: bool = False, audit_mode: bool = False
    ):
        """Initialisiert Runner.

        Args:

            force: Wenn True, werden existierende Golden Standards überschrieben
            audit_mode: Wenn True, wird pro Durchlauf ein Audit-Log (Prompt, Antwort, Judge) gespeichert.
        """
        super().__init__()
        self.force = force
        self.audit_mode = audit_mode
        self._load_categories()
        self.existing_benchmarks = self._load_existing_benchmarks()

    def _load_existing_benchmarks(self) -> Dict[Tuple[str, str], Dict[str, Any]]:
        """Loads processed assets with data (SSOT Source)."""
        cache = {}
        # Check both Commercial and Local Csvs to be sure
        # pylint: disable=protected-access
        csv_files = [
            self.result_manager._get_csv_path("commercial"),
            self.result_manager._get_csv_path("local"),
        ]
        # pylint: enable=protected-access

        for p in csv_files:
            if p.exists():
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            # Key: (Model, AssetID)
                            m = row.get("model")
                            a = row.get("asset_id")
                            if m and a:
                                cache[(m, a)] = row
                except (OSError, csv.Error):
                    pass
        return cache

    def _load_categories(self):
        """Loads benchmark categories from config (Hydrated)."""
        self.benchmark_categories = load_active_benchmarks(self.validator.config)

    def get_available_providers(self) -> Dict[str, dict]:
        """Holt aktivierte kommerzielle Provider aus Config."""
        return self.validator.get_enabled_commercial_providers()

    def select_model(self) -> Optional[Tuple[str, str]]:
        """Interaktive Modell-Auswahl für Test Mode."""
        providers = self.get_available_providers()
        model_list = []

        for p_key, p_conf in providers.items():
            p_name = p_conf.get("name", p_key)
            for model in p_conf.get("models", []):
                m_id = model.get("id")
                m_name = model.get("name", m_id)
                desc = model.get("description", "")
                model_list.append((p_key, m_id, p_name, m_name, desc))

        selected = select_from_list(
            model_list,
            lambda item: f"[{item[2]}] {item[3]}"
            + (f" - {item[4]}" if item[4] else ""),
            prompt="Wähle Modell",
            title="🌐 VERFÜGBARE MODELLE",
        )

        if selected:
            # pylint: disable=unbalanced-tuple-unpacking
            p_key, m_id, p_name, m_name, _ = selected
            print(f"✓ Ausgewählt: {p_name} - {m_name}\n")
            return (p_key, m_id)

        return None

    def select_benchmark(self) -> Optional[Dict[str, Any]]:
        """Interaktive Benchmark-Auswahl."""
        categories = list(self.benchmark_categories.items())

        # Add "All Modules" option
        all_option = (
            "all",
            {
                "name": "Alle Module ausführen",
                "description": "Führt alle verfügbaren Benchmarks nacheinander aus",
            },
        )
        options = categories + [all_option]

        selected = select_from_list(
            options,
            lambda item: (item[1]["name"], item[1]["description"]),
            prompt="Wähle Benchmark",
            title="📊 VERFÜGBARE BENCHMARKS",
        )
        if selected:
            key, info = selected
            print(f"✓ Ausgewählt: {info['name']}\n")
            return {"key": key, **info}
        return None

    @staticmethod
    def _get_quality_badge(percentage: float) -> str:
        """Deprecated: Use self.get_quality_badge instead."""
        return BaseBenchmarkRunner.get_quality_badge(percentage)

    # pylint: disable=too-many-arguments, too-many-locals, too-many-positional-arguments
    def _recover_from_json(
        self,
        json_path: Path,
        asset_path: Path,
        benchmark_info: Dict[str, Any],
        provider: str,
        model: str,
    ) -> Optional[Dict[str, Any]]:
        """Recovers a result from a cached JSON file."""
        try:
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)

            # Re-calculate score
            module_path = Path(benchmark_info["path"]).parent / "test.py"
            test_cls_name = benchmark_info.get("test_class", "CodeQualityTest")
            test_cls = load_test_class(module_path, test_cls_name)
            test_inst = test_cls(asset_path)

            dummy_result = BenchmarkResult(
                raw_response=data.get("response", ""),
                execution_time=data.get("execution_time", 0.0),
            )
            dummy_result = test_inst.score_response(dummy_result)
            score = dummy_result.data
            asset_id = data.get("id", asset_path.stem)

            result = {
                "timestamp": data.get(
                    "timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ),
                "status": score.get("status", "success"),
                "provider": provider,
                "model": model,
                "asset_id": asset_id,
                "asset_name": asset_path.stem,
                "total_score": score["total_score"],
                "max_score": score["max_score"],
                "percentage": round(
                    (score["total_score"] / score["max_score"] * 100), 1
                ),
                "execution_time": data.get("execution_time", 0.0),
                "response_length": len(data.get("response", "")),
                "tier": score.get("tier", "Tier 1"),
            }

            for cat, val in score.get("category_scores", {}).items():
                result[cat] = f"{val['achieved']}/{val['max']}"

            return result

        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"   ⚠️ Fehler beim Wiederherstellen aus JSON: {e}")
            return None

    # pylint: disable=unused-argument
    def _process_single_asset(
        self,
        asset_path: Path,
        provider: str,
        model: str,
        benchmark_info: Dict[str, Any],
        index: int = 1,
        total_count: int = 1,
        limiter: Optional[RateLimiter] = None,
    ) -> Optional[Dict[str, Any]]:
        """Processes a single asset."""
        # pylint: enable=unused-argument
        asset_data = load_asset_yaml(asset_path)
        if not asset_data:
            print(f"⚠️  Skipping empty asset: {asset_path.name}")
            return None

        asset_id = asset_data.get("metadata", {}).get("id", asset_path.stem)
        asset_name = asset_data.get("metadata", {}).get("name") or asset_data.get(
            "metadata", {}
        ).get("topic", asset_id)

        # 1. SSOT Check / Golden Mode Data Reuse
        # If result exists in ANY benchmark CSV (Commercial/Local), use it immediately!
        # Do not run a new request unless specific force/missing scenario.

        cached_row = self.existing_benchmarks.get((model, asset_id))

        if not self.force and cached_row:
            # Skip already processed tests (SSOT Behavior)
            return None

        # print(f"▶️  Teste: {asset_name}...")
        # Optional: Print simple status if long running
        print(f"[{index}/{total_count}] Running: {asset_name}...", end="\r", flush=True)

        # Rate Limit Logic
        if limiter:
            limiter.wait_for_slot()

        # Execute Test using BaseRunner logic
        try:
            start_time = time.time()
            test_inst, exec_result = self.execute_test_module(
                model=model,
                asset_path=asset_path,
                benchmark_info=benchmark_info,
                provider=provider,
            )
            # Use inner execution time if available (excludes potential retry delays)
            if not exec_result.execution_time:
                exec_result.execution_time = time.time() - start_time
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"\n❌ Fehler bei Ausführung ({asset_name}): {e}"); traceback.print_exc(); traceback.print_exc()
            return None

        response = exec_result.raw_response
        exec_result = test_inst.score_response(exec_result)
        score = exec_result.data

        # Build Standardized Result
        result = self.build_base_result(model, asset_data, exec_result, provider)

        # ADDED: Granular Score Contribution
        benchmarks_list = benchmark_info.get("benchmarks", [])
        asset_cfg = next(
            (b for b in benchmarks_list if b["id"] == result["asset_id"]), None
        )

        # Calculate initial score contributions
        result = calculate_score_contributions(result, asset_cfg)

        # ---------------------------------------------------------------------
        # Add Cost Tracking (Must happen BEFORE fingerprinting to avoid overwrite)
        # ---------------------------------------------------------------------
        cost_val = 0.0
        token_str = "0 T"
        if hasattr(self.client, "last_request_cost"):
            cost_val = self.client.last_request_cost
            result["cost_usd"] = f"{cost_val:.6f}"
        else:
            result["cost_usd"] = "0.000000"

        if hasattr(self.client, "last_token_usage"):
            t_count = self.client.last_token_usage
            result["tokens_used"] = t_count  # Save to CSV
            if t_count > 1000:
                token_str = f"{t_count / 1000:.1f}k T"
            else:
                token_str = f"{t_count} T"

        # Add canonical version string from model mapping.
        version = get_model_version(
            model_name=model,
            provider=provider,
            client=self.client if hasattr(self, "client") else None,
        )

        result["model_version"] = version

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
                result = evaluate_with_judge(
                    result=result,
                    response=response,
                    asset_data=asset_data,
                    judge_cfg_dict=judge_cfg_dict,
                    eval_module_id=eval_module_id,
                    model=model,
                    asset_cfg=asset_cfg,
                    benchmark_info=benchmark_info,
                    provider=provider
                )

        # ---------------------------------------------------------------------

        # Print Output
        badge = self.get_quality_badge(result["percentage"])

        # Clear the "Running..." line by overwriting with full line
        # [1/5] codequality001 | WCAG Audit ✓ Score: 88 | Cost: $0.0047 | Time: 12.3s
        time_val = exec_result.execution_time or 0.0
        judge_status = result.get("judge_progress_status", "")
        judge_str = f" | {judge_status}" if judge_status else ""
        print(
            f"[{index}/{total_count}] {asset_id:<15} | {asset_name[:20]:<20} {badge} "
            f"Score: {result['percentage']:>6.2f} | Cost: ${cost_val:.4f} | "
            f"{token_str:>7} | Time: {time_val:.1f}s{judge_str}"
        )

        # Save Golden Standard JSON if needed
            # Logik entfernt, die bei mode="test" automatisch speichert.
            # Rationale: "100%" should be static until manual update.

        # Debug Auto-Save Logic (Ported from Local Runner)
        if result["percentage"] < 30:
            save_debug_response(
                result["model"],
                result["asset_id"],
                response,
                f"{result['total_score']}/{result['max_score']} ({result['percentage']}%)",
                score.get("reasoning", "No explanation provided"),
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

    def run_benchmark(
        self,
        provider: str,
        model: str,
        benchmark_info: Dict[str, Any],
        num_runs: int = 1,
        assets: Optional[List[Path]] = None,
    ) -> List[Dict[str, Any]]:
        """Main benchmark execution loop.

        Args:
            provider: Provider Key
            model: Model ID
            benchmark_info: Modul Info
            num_runs: Number of runs (for average, if applicable)
            assets: Optional list of assets to run (overrides discovery)
        """

        # Dispatch Batch Mode
        if benchmark_info.get("execution_mode") == "batch":
            return self.execute_batch_module(
                model=model,
                benchmark_info=benchmark_info,
                provider=provider,
                num_runs=num_runs,
                force=self.force,
                existing_benchmarks=self.existing_benchmarks
            )

        # Check Golden Standard Status

        print(
            f"\n{'=' * 60}\n📊 STARTE BENCHMARK: {benchmark_info['name']}\n{'=' * 60}"
        )
        print(f"Provider: {provider}\nModell:   {model}")

        if not assets:
            assets = discover_assets(benchmark_info["path"])

        print(f"Tests:    {len(assets)}\n{'=' * 60}\n")

        # Initialize Rate Limiter
        run_limiter = RateLimiter(provider)

        results = []
        total_assets = len(assets)
        for i, asset_path in enumerate(assets, 1):
            res = self._process_single_asset(
                asset_path,
                provider,
                model,
                benchmark_info,
                index=i,
                total_count=total_assets,
                limiter=run_limiter,
            )
            if res:
                results.append(res)

        return results


def main():
    """CLI Entry Point."""
    parser = argparse.ArgumentParser(description="Commercial Benchmark Runner")
    parser.add_argument(
        "--auto", action="store_true", help="Run automatically without interaction"
    )
    parser.add_argument(
        "--force", action="store_true", help="Force re-run of existing benchmark tests"
    )
    args = parser.parse_args()

    print(f"\n{'=' * 60}\n🚀 KOMMERZIELLE MODELLE BENCHMARK\n{'=' * 60}")

    runner = CommercialBenchmarkRunner()

    runner = CommercialBenchmarkRunner()

    # 1. Select Model
    result = runner.select_model()

    if not result:
        return

    provider, model_id = result

    # 3. Select Benchmark (or Auto)
    if args.auto:
        print("\n🚀 Starte automatischen Run für alle Module...")
        for cat_key, cat_info in runner.benchmark_categories.items():
            # Skip Political Compass in Golden Standard (Bias != Benchmark)

            results = runner.run_benchmark(provider, model_id, cat_info)
            runner.save_results(results, result_type="commercial")
            runner.print_summary(results, model=model_id)
        return

    benchmark_info = runner.select_benchmark()
    if not benchmark_info:
        return

    # Handle "All Modules" selection
    if benchmark_info.get("key") == "all":
        print("\n🚀 Starte Sequenz für ALLE Module...")
        error_count = 0
        for _, cat_info in runner.benchmark_categories.items():
            try:
                print(f"\n👉 Modul: {cat_info['name']}")
                results = runner.run_benchmark(provider, model_id, cat_info)
                runner.save_results(results, result_type="commercial")
                runner.print_summary(results, model=model_id)
            except Exception as e:  # pylint: disable=broad-exception-caught
                print(f"❌ Fehler im Modul '{cat_info['name']}': {e}")
                traceback.print_exc()
                error_count += 1

        if error_count > 0:
            print(f"\n⚠️  Fertig mit {error_count} Fehlern.")
        else:
            print("\n✅ Alle Module erfolgreich abgeschlossen.")
        return

    try:
        results = runner.run_benchmark(provider, model_id, benchmark_info)
        runner.save_results(results, result_type="commercial")
        runner.print_summary(results, model=model_id)
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"\n❌ Fatal Error: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
