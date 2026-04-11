#!/usr/bin/env python3
"""Unified Benchmark Runner für lokale und kommerzielle Modelle."""

import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from utils.constants import (
    OLLAMA_DEFAULT_BASE_URL,
    MODEL_TYPE_OPEN_WEIGHTS_CLOUD,
    TIMEOUT_OLLAMA_LIST_FAST,
    TIMEOUT_OLLAMA_WARMUP,
)


class CostLimitExceededError(Exception):
    """Raised when the cost limit is exceeded."""


from utils.base_runner import BaseBenchmarkRunner
from utils.benchmark_utils import discover_assets, load_asset_yaml
from utils.logging_config import setup_logging
from utils.model_utils import get_model_version, get_model_identity
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
                "local_models_csv", "benchmark_scores/local_models_benchmark.csv"
            )
        )
        self.cloud_csv = Path(
            self.validator.config.get("output", {}).get(
                "cloud_models_csv", "benchmark_scores/cloud_models_benchmark.csv"
            )
        )
        self.commercial_csv = Path(
            self.validator.config.get("output", {}).get(
                "commercial_csv", "benchmark_scores/commercial_models_benchmark.csv"
            )
        )

        # Cache und Laufzeit-Daten
        self.warmup_cache: set[str] = set()
        # Gesetzt wenn ein Budget-/Quota-Fehler während eines Moduls erkannt wurde
        self.provider_quota_exhausted: bool = False
        self.existing_commercial_benchmarks = self._load_existing_benchmarks(
            self.commercial_csv
        )
        self.existing_cloud_benchmarks = self._load_existing_benchmarks(self.cloud_csv)
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
                    # Count completed tests regardless of status variant
                    # (language_mismatch, verbose_outlier, truncated are valid completions)
                    if status == "error":
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

    def _get_existing(self, provider: str) -> Dict:
        """Ermittelt das passende Cache-Dictionary basierend auf dem Provider."""
        if provider == "ollama":
            return self.existing_local_benchmarks

        provider_config = self.validator.config.get("providers", {}).get("commercial", {}).get(provider, {})
        if provider_config.get("model_type") == MODEL_TYPE_OPEN_WEIGHTS_CLOUD:
            return self.existing_cloud_benchmarks

        return self.existing_commercial_benchmarks

    def _get_existing_for_model(self, provider: str, model: str) -> Dict:
        """Wie _get_existing(), aber beachtet auch :cloud-Suffix bei Ollama-Proxies."""
        if provider == "ollama":
            if ":cloud" in model.lower() or model.lower().endswith("-cloud"):
                return self.existing_cloud_benchmarks
            return self.existing_local_benchmarks

        provider_config = self.validator.config.get("providers", {}).get("commercial", {}).get(provider, {})
        if provider_config.get("model_type") == MODEL_TYPE_OPEN_WEIGHTS_CLOUD:
            return self.existing_cloud_benchmarks

        return self.existing_commercial_benchmarks

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
                timeout=TIMEOUT_OLLAMA_WARMUP,
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

        # Skip logic: überspringen wenn bereits im Cache (respektiert --force)
        if not self.force:
            key = (model, asset_id)
            existing_cache = self._get_existing_for_model(provider, model)
            if key in existing_cache:
                print(f"   ⏭️  [{asset_id}] Wird übersprungen (Cache)")
                cached = existing_cache[key]
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

        # Language Mismatch Detection (heuristisch – kein externer Dependency)
        expected_lang = asset_data.get("metadata", {}).get("language", "")
        if expected_lang and len(response.split()) > 50:
            words_lower = response.lower().split()
            de_markers = {"der", "die", "das", "und", "ist", "für", "nicht", "sie",
                          "mit", "ein", "auf", "bei", "von", "zu", "im", "den",
                          "des", "dem", "sich", "auch", "eine", "einer", "einem"}
            en_markers = {"the", "and", "for", "with", "is", "are", "that", "this",
                          "have", "been", "from", "will", "your", "you", "our",
                          "their", "which", "also", "not", "all"}
            de_count = sum(1 for w in words_lower if w in de_markers)
            en_count = sum(1 for w in words_lower if w in en_markers)
            detected_en = en_count > de_count * 2 and en_count > 8

            if expected_lang == "de" and detected_en:
                exec_result.data["language_mismatch"] = True
                exec_result.data["detected_language"] = "en"
                exec_result.data["violations"] = exec_result.data.get("violations", []) + ["Wrong Language (English instead of German)"]
                if isinstance(exec_result.data.get("details"), list):
                    exec_result.data["details"].append(
                        "> [!WARNING]\n"
                        "> **[LANGUAGE MISMATCH]** The model responded in English, but the task requires German (`expected_language: de`). "
                        f"Language marker counts: DE={de_count}, EN={en_count}."
                    )
                score = exec_result.data
                logger.warning("Language mismatch detected for %s / %s: EN response on DE task", model, asset_data.get("metadata", {}).get("id"))

        # Build base result
        result = self.build_base_result(model, asset_data, exec_result, provider)
        result["model_version"] = getattr(
            self, "current_model_version", get_model_version(model, provider=provider)
        )
        if exec_result.data.get("language_mismatch"):
            result["language_mismatch"] = True
            result["status"] = "language_mismatch"

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
                            timeout=TIMEOUT_OLLAMA_LIST_FAST,
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
                existing_benchmarks=self._get_existing(provider),
            )

        # Standard Run Loop
        print(
            f"\n{'=' * 60}\n📊 STARTE BENCHMARK: {benchmark_info.get('name', 'Unknown')}\n{'=' * 60}"
        )
        identity = get_model_identity(model)
        display_name = identity["display_name"]
        tags_str = ", ".join(identity["tags"])
        print(f"Provider: {provider}\nModell:   {model} (Tags: [{tags_str}])")

        self.current_model_version = get_model_version(model, provider=provider)

        warmup_result = None
        if is_local:
            warmup_result = self._measure_cold_start(model)
            if warmup_result:
                warmup_result["model_version"] = self.current_model_version

        if not assets:
            assets = discover_assets(benchmark_info["path"])

        print(f"Tests:    {len(assets)}\n{'=' * 60}\n")

        # Generate a unique run_id for this benchmark pass (Fix 4: Baseline-Lock)
        import hashlib
        import time
        run_timestamp = str(int(time.time()))
        tasks_str = ",".join([a.name for a in assets])
        run_id_str = f"{model}_{tasks_str}_{run_timestamp}"
        run_id = hashlib.md5(run_id_str.encode()).hexdigest()[:12]

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
                # Assign run_id to link all results of this run (Fix 4: Baseline-Lock)
                result["run_id"] = run_id

                # Fix 2 (Truncation Detection): Konfigurierbare Schwellenwerte pro Modul
                TRUNCATION_THRESHOLDS = {
                    "documentation_quality": 1500,
                    "ux_writing": 800,
                }
                module_id = benchmark_info.get("id", "")
                threshold = TRUNCATION_THRESHOLDS.get(module_id)
                if threshold:
                    response_len = result.get("response_length")
                    if response_len is None:
                        response_len = result.get("metadata", {}).get("response_length", 0)
                    if isinstance(response_len, str):
                        try:
                            response_len = int(response_len)
                        except (ValueError, TypeError):
                            response_len = 0
                    if response_len and response_len > 0 and response_len < threshold and result.get("status") == "success":
                        result["status"] = "truncated"
                        result["truncation_note"] = f"Response below {threshold} chars for {module_id}"
                        print(f"\n   ⚠️ Result marked as truncated (length: {response_len} < {threshold})")

                # Verbose-Overflow-Check (per-Asset max_expected_length constraint)
                _asset_data = load_asset_yaml(asset_path)
                _max_expected = _asset_data.get("constraints", {}).get("max_expected_length")
                if _max_expected and result.get("status") == "success":
                    _overflow_len = result.get("response_length")
                    if _overflow_len is None:
                        _overflow_len = result.get("metadata", {}).get("response_length", 0)
                    if isinstance(_overflow_len, str):
                        try:
                            _overflow_len = int(_overflow_len)
                        except (ValueError, TypeError):
                            _overflow_len = 0
                    if _overflow_len and _overflow_len > _max_expected:
                        result["status"] = "verbose_outlier"
                        result["truncation_note"] = f"Response {_overflow_len} chars exceeds expected max {_max_expected}"
                        print(f"\n   ⚠️ Result marked as verbose_outlier ({_overflow_len} > {_max_expected})")

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

                if result:
                    results.append(result)

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
                # Budget-/Quota-Fehler erkennen und Flag setzen
                _BUDGET_KEYWORDS = [
                    "quota", "budget", "billing", "credit", "insufficient_funds",
                    "payment", "402 payment required", "exceeded your current quota",
                    "budget limit exceeded",
                ]
                if any(kw in str(e).lower() for kw in _BUDGET_KEYWORDS):
                    print(f"   💸 Budget-/Quota-Fehler erkannt für Provider. Setze Exhausted-Flag.")
                    self.provider_quota_exhausted = True

        # Global audit metrics
        # ---------------------------------------------------------
        # Terminal Summary Generation
        # ---------------------------------------------------------
        valid_results = [r for r in results if r.get("type") != "system" and r.get("status") != "error" and r.get("skip_reason") is None]
        if valid_results:
            # DEBUG: Temporär zur Diagnose des DURCHSCHNITT-Bugs
            _pcts = [r.get("percentage") for r in valid_results]
            logger.debug("DURCHSCHNITT DEBUG: valid_results=%d, pcts=%s", len(valid_results), _pcts)
            avg_score = sum(float(p) if p is not None else 0.0 for p in _pcts) / len(valid_results)
            avg_time = sum(r.get("execution_time", 0.0) for r in valid_results) / len(valid_results)

            token_rates = [
                float(r.get("tokens_per_second", 0.0))
                for r in valid_results
                if isinstance(r.get("tokens_per_second"), (int, float)) or (isinstance(r.get("tokens_per_second"), str) and str(r.get("tokens_per_second")).replace('.','',1).isdigit())
            ]
            avg_tokens = sum(token_rates) / len(token_rates) if token_rates else 0.0

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
            self.save_results(results)
