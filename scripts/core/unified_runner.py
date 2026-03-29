#!/usr/bin/env python3
"""Unified Benchmark Runner für lokale und kommerzielle Modelle."""

import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from utils.constants import OLLAMA_DEFAULT_BASE_URL


class CostLimitExceededError(Exception):
    """Raised when the cost limit is exceeded."""


from utils.base_runner import BaseBenchmarkRunner
from utils.benchmark_utils import discover_assets, load_asset_yaml
from utils.logging_config import setup_logging
from utils.model_utils import get_model_version
from utils.scoring.judge_evaluator import evaluate_with_judge, generate_audit_log
from utils.scoring.exceptions import JudgeUnavailableError
from utils.adaptive_pause import AdaptivePauseCalculator, BenchmarkMode
from utils.rate_limiter import RateLimiter
from utils.scoring_utils import calculate_score_contributions

setup_logging()
logger = logging.getLogger(__name__)


class UnifiedBenchmarkRunner(BaseBenchmarkRunner):
    """Führt Benchmarks systemübergre এশিয়ার (Lokal & API) aus."""

    def __init__(
        self,
        force: bool = False,
        audit_mode: bool = False,
        mode: BenchmarkMode = BenchmarkMode.PRODUCTION,
    ):
        super().__init__()
        self.force = force
        self.audit_mode = audit_mode
        self.mode = mode

        # Load output configurations
        self.local_csv = Path(
            self.validator.config.get("output", {}).get(
                "local_csv", "benchmark_scores/local_models_benchmark.csv"
            )
        )
        self.commercial_csv = Path(
            self.validator.config.get("output", {}).get(
                "commercial_csv", "benchmark_scores/commercial_models_benchmark.csv"
            )
        )

        # Cache und Laufzeit-Daten
        self.warmup_cache: set[str] = set()
        self.existing_commercial_benchmarks = self._load_existing_benchmarks(
            self.commercial_csv
        )
        self.existing_local_benchmarks = self._load_existing_benchmarks(self.local_csv)

    def _load_existing_benchmarks(
        self, csv_path: Path
    ) -> Dict[Tuple[str, str], Dict[str, Any]]:
        existing = {}
        if self.force or not csv_path.exists():
            return existing

        import csv

        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    status = str(row.get("status", "success")).lower()
                    if status != "success":
                        continue

                    model_id = str(row.get("model", ""))
                    asset_id = str(row.get("asset_id", ""))
                    if model_id and asset_id:
                        # Convert numeric fields to support formatting
                        for num_field in ["percentage", "execution_time", "total_score", "max_score", "tokens_used", "cost_usd", "golden_similarity"]:
                            if num_field in row:
                                try:
                                    row[num_field] = float(row[num_field])
                                except (ValueError, TypeError):
                                    row[num_field] = 0.0

                        existing[(model_id, asset_id)] = dict(row)
        except Exception as e:
            logger.warning(f"Fehler beim Laden bestehender Benchmarks {csv_path}: {e}")
        return existing

    def _get_existing(self, is_local: bool) -> Dict:
        return (
            self.existing_local_benchmarks
            if is_local
            else self.existing_commercial_benchmarks
        )

    def _measure_cold_start(self, model: str) -> Optional[Dict[str, Any]]:
        if model in self.warmup_cache:
            return None

        print("\n" + "=" * 60)
        print("❄️  COLD START PROBE (Ignoriert für Scoring)")
        print("Initialisiere Ollama-Modell in den VRAM...")
        print("=" * 60)

        start_time = time.time()
        try:
            requests.post(
                f"{OLLAMA_DEFAULT_BASE_URL}/api/generate",
                json={"model": model, "prompt": "Hi", "stream": False},
                timeout=120,
            )
            ex_time = time.time() - start_time
            print(f"✓ Warmup abgeschlossen in {ex_time:.1f}s\n")
            self.warmup_cache.add(model)

            return {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "success",
                "provider": "ollama",
                "model": model,
                "asset_id": "system_warmup_probe",
                "asset_name": "Cold Start Probe",
                "type": "system",
                "total_score": 0,
                "percentage": 0,
                "max_score": 100,  # Fixed max_score
                "tier": "System",
                "execution_time": round(ex_time, 1),
                "golden_similarity": 0,
                "tokens_used": 0,
                "cost_usd": 0.0,
                "raw_response": "SYSTEM_WARMUP",
            }
        except Exception as e:
            logger.warning(f"Warmup fehlgeschlagen: {e}")
            return None

    def _create_error_result(self, asset_id: str, error_message: str) -> Dict[str, Any]:
        return {
            "status": "error",
            "error_message": error_message,
            "asset_id": asset_id,
            "asset_name": asset_id,
            "percentage": 0,
            "tier": "Tier 1",
            "execution_time": 0,
            "total_score": 0,
            "max_score": 0,
        }

    def _process_single_test(
        self,
        model: str,
        provider: str,
        asset_path: Path,
        benchmark_info: Dict[str, Any],
        is_local: bool,
        pause_calculator: Optional[Any] = None,
        run_limiter: Optional[Any] = None,
    ) -> Dict[str, Any]:
        asset_data = load_asset_yaml(asset_path)
        if not asset_data:
            return self._create_error_result(
                asset_path.stem, "Empty/Invalid Asset File"
            )

        asset_id = asset_data.get("metadata", {}).get("id", asset_path.stem)

        # Skip logic for commercial
        if not is_local and not self.force:
            key = (model, asset_id)
            if key in self.existing_commercial_benchmarks:
                print(f"   ⏭️  [{asset_id}] Wird übersprungen (Cache)")
                cached = self.existing_commercial_benchmarks[key]
                cached["cached"] = True
                return cached

        if not is_local and run_limiter:
            run_limiter.wait_for_slot()

        start_time = time.time()
        try:
            test_instance, exec_result = self.execute_test_module(
                model, asset_path, benchmark_info, provider=provider
            )
            if not getattr(exec_result, "execution_time", None):
                exec_result.execution_time = time.time() - start_time
        except Exception as e:
            return self._create_error_result(asset_path.stem, str(e))

        response = exec_result.raw_response
        exec_result = test_instance.score_response(exec_result)
        score = exec_result.data

        # Build base result
        result = self.build_base_result(model, asset_data, exec_result, provider)
        result["model_version"] = getattr(
            self, "current_model_version", get_model_version(model, provider=provider)
        )

        # Token usage & Cost
        if hasattr(self.client, "last_token_usage"):
            result["tokens_used"] = self.client.last_token_usage
            if not is_local and hasattr(self.client, "last_cost_usd"):
                result["cost_usd"] = getattr(self.client, "last_cost_usd", 0.0)
            else:
                result["cost_usd"] = 0.0
        else:
            result["tokens_used"] = exec_result.tokens_used or 0
            result["cost_usd"] = 0.0

        if is_local:
            result["golden_similarity"] = 0.0

        if result.get("status") == "error":
            return result

        # Calculates granular score contribution if configured
        benchmarks_list = benchmark_info.get("benchmarks", [])
        # Find config for this asset
        asset_cfg = next((b for b in benchmarks_list if b["id"] == asset_id), None)

        # Calculate initial score contributions (based on Regex) for tracking/debug
        if asset_cfg:
            initial_contribs = calculate_score_contributions(score, asset_cfg)
            result["score_contributions"] = initial_contribs

        # Judge Feedback
        judge_cfg_dict = self.validator.config.get("llm_judge", {})
        if judge_cfg_dict.get("enabled", True) and benchmark_info.get("id", "") in (
            judge_cfg_dict.get("applicable_modules") or []
        ):
            if len(response.strip()) < 15:
                result["judge_progress_status"] = "⚠️ Judge: skip (zu kurz/abgelehnt)"
            else:
                if is_local and pause_calculator:
                    pause_calculator.wait(
                        {
                            "execution_time": result.get("execution_time", 0),
                            "response_length": result.get("tokens_used", 0) * 4,
                        }
                    )

                # Unload local model before judge to free VRAM
                if is_local:
                    try:
                        requests.post(
                            f"{OLLAMA_DEFAULT_BASE_URL}/api/generate",
                            json={"model": model, "keep_alive": 0},
                            timeout=5,
                        )
                    except Exception:
                        pass
                    time.sleep(0.5)

                benchmarks_list = benchmark_info.get("benchmarks", [])
                asset_cfg = next(
                    (b for b in benchmarks_list if b["id"] == asset_id), None
                )

                result = evaluate_with_judge(
                    result=result,
                    response=response,
                    asset_data=asset_data,
                    judge_cfg_dict=judge_cfg_dict,
                    eval_module_id=benchmark_info.get("id", ""),
                    model=model,
                    asset_cfg=asset_cfg,
                    benchmark_info=benchmark_info,
                )

        if getattr(self, "audit_mode", False):
            generate_audit_log(result, exec_result, asset_data, response, score)

        return result

    def run_benchmark(
        self,
        provider: str,
        model: str,
        benchmark_info: Dict[str, Any],
        num_runs: int = 1,
        assets: Optional[List[Path]] = None,
    ) -> List[Dict[str, Any]]:
        is_local = provider == "ollama"

        if benchmark_info.get("execution_mode") == "batch":
            return self.execute_batch_module(
                model=model,
                benchmark_info=benchmark_info,
                provider=provider,
                num_runs=num_runs,
                force=self.force,
                existing_benchmarks=self._get_existing(is_local),
            )

        # Standard Run Loop
        print(
            f"\n{'=' * 60}\n📊 STARTE BENCHMARK: {benchmark_info.get('name', 'Unknown')}\n{'=' * 60}"
        )
        print(f"Provider: {provider}\nModell:   {model}")

        self.current_model_version = get_model_version(model, provider=provider)

        warmup_result = None
        if is_local:
            warmup_result = self._measure_cold_start(model)
            if warmup_result:
                warmup_result["model_version"] = self.current_model_version

        if not assets:
            assets = discover_assets(benchmark_info["path"])

        print(f"Tests:    {len(assets)}\n{'=' * 60}\n")

        results = []
        if warmup_result:
            results.append(warmup_result)

        if not assets:
            print("⚠️  Keine Tests gefunden.")
            return results

        pause_calculator = (
            AdaptivePauseCalculator(model, self.mode) if is_local else None
        )
        run_limiter = RateLimiter(provider) if not is_local else None

        for i, asset_path in enumerate(assets, 1):
            asset_name = asset_path.stem.replace("asset_", "").replace("_", " ").title()
            print(
                f"   ⏳ [{i}/{len(assets)}] {asset_name}: Test läuft...",
                end="\r",
                flush=True,
            )

            try:
                result = self._process_single_test(
                    model=model,
                    provider=provider,
                    asset_path=asset_path,
                    benchmark_info=benchmark_info,
                    is_local=is_local,
                    pause_calculator=pause_calculator,
                    run_limiter=run_limiter,
                )
                results.append(result)

                # Print Status
                status_icon = "❌" if result.get("status") == "error" else "✓"
                token_str = f"{result.get('tokens_used', 0)} T"
                judge_str = (
                    f" | {result.get('judge_progress_status', '')}"
                    if result.get("judge_progress_status")
                    else ""
                )

                print(" " * 80, end="\r")
                print(
                    f"   {status_icon} [{i}/{len(assets)}] {asset_name}: {result.get('percentage', 0):.1f}% | {token_str} | {result.get('execution_time', 0):.1f}s{judge_str}"
                )

            except CostLimitExceededError as e:
                print(f"\n❌ KOSTENLIMIT ERREICHT: {e}")
                self._save_partial_results(results, is_local)
                sys.exit(1)
            except JudgeUnavailableError as e:
                print(f"\n⛔ JUDGE UNAVAILABLE (API Error / Budget Limit): {e}\nBeende den Benchmark vorzeitig, um inkonsistente Scores zu vermeiden.")
                self._save_partial_results(results, is_local)
                sys.exit(1)
            except KeyboardInterrupt:
                print("\n⚠️  Benchmark vom Benutzer abgebrochen.")
                self._save_partial_results(results, is_local)
                sys.exit(1)
            except Exception as e:
                print(" " * 80, end="\r")
                print(f"   ❌ [{i}/{len(assets)}] {asset_name}: Abgebrochen - {str(e)}")

        # Global audit metrics
        # ---------------------------------------------------------
        # Terminal Summary Generation
        # ---------------------------------------------------------
        valid_results = [r for r in results if r.get("type") != "system" and r.get("status") != "error" and r.get("skip_reason") is None]
        if valid_results:
            avg_score = sum(r.get("semantic_score", r.get("accuracy_score", 0.0)) for r in valid_results) / len(valid_results)
            avg_time = sum(r.get("execution_time", 0.0) for r in valid_results) / len(valid_results)
            avg_tokens = sum(r.get("tokens_per_second", 0.0) for r in valid_results) / len(valid_results)
            judge_scores = [r.get("judge_score") for r in valid_results if r.get("judge_score") is not None]

            # The theoretical cost is generated dynamically per request from CostTracker (SSOT)
            total_usd = sum(r.get("cost_usd", 0.0) for r in valid_results)
            avg_usd = total_usd / len(valid_results)

            summary = "\n   " + "="*70 + "\n"
            summary += f"   🏁 DURCHSCHNITT: {avg_score:.1f}% | {avg_tokens:.0f} T/s | {avg_time:.1f}s"

            if judge_scores:
                avg_judge = sum(judge_scores) / len(judge_scores)
                summary += f" | ⚖️ Judge: {avg_judge:.1f}/5"

            if avg_usd > 0.0:
                summary += f" | 💵 Ø ${avg_usd:.4f}"

            summary += "\n   " + "="*70 + "\n"
            print(summary)


        if self.audit_mode and results:
            from utils.benchmark_utils import append_global_run_metrics

            execution_times: List[float] = []
            timeout_count: int = 0
            asset_ids = []
            for res in results:
                if res.get("type") == "system":
                    continue
                a_id = res.get("asset_id", "")
                if a_id:
                    asset_ids.append(a_id)
                t_exe = res.get("execution_time", 0.0)
                execution_times.append(t_exe)
                if res.get("status") == "error" or t_exe > 120.0:
                    timeout_count += 1
            if asset_ids:
                append_global_run_metrics(
                    model,
                    asset_ids,
                    execution_times,
                    timeout_count,
                    len(asset_ids),
                    benchmark_info.get("name", "Unknown"),
                )

        return results

    def _save_partial_results(self, results: List[Dict[str, Any]], is_local: bool):
        if results:
            print("💾 Speichere bisherige Ergebnisse...")
            self.save_results(results, "local" if is_local else "commercial")
