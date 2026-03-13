#!/usr/bin/env python3
"""Benchmark Runner für kommerzielle API-basierte Modelle."""

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
    format_political_compass_data,
    prepare_pc_csv_row,
    save_debug_response,
    save_audit_log,
)  # noqa: E402
from utils.fingerprinting import ModelFingerprinter  # noqa: E402
from utils.model_utils import get_model_version  # noqa: E402
from utils.llm_client import LLMClient  # noqa: E402
from utils.module_registry import load_active_benchmarks  # noqa: E402
from utils.scoring_utils import (
    calculate_score_contributions,
    calculate_hybrid_score,
)  # noqa: E402
from utils.rate_limiter import RateLimiter  # noqa: E402

# Declare ResultManager with proper type annotation
# pylint: disable=invalid-name
ResultManager: Optional[Any] = None  # noqa: E402
try:
    from benchmark_modules.political_compass.core.io_manager import ResultManager
except ImportError:
    pass
# pylint: enable=wrong-import-position, import-error,invalid-name

logger = logging.getLogger(__name__)


class CommercialBenchmarkRunner(BaseBenchmarkRunner):
    """Benchmark Runner für kommerzielle API-basierte Modelle."""

    benchmark_categories: Dict[str, Any] = {}

    def __init__(
        self, mode: str = "test", force: bool = False, audit_mode: bool = False
    ):
        """Initialisiert Runner.

        Args:
            mode: 'golden_standard' oder 'test'
            force: Wenn True, werden existierende Golden Standards überschrieben
            audit_mode: Wenn True, wird pro Durchlauf ein Audit-Log (Prompt, Antwort, Judge) gespeichert.
        """
        super().__init__()
        self.mode = mode
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

    def select_mode(self) -> Optional[str]:
        """Wähle Benchmark-Modus."""
        print(f"\n{'=' * 60}")
        print("🎯 BENCHMARK-MODUS")
        print(f"{'=' * 60}")
        print("  1. Golden Standard generieren (Referenz-Benchmark)")
        print(f"     → Speichert in: {self.validator.get_golden_standard_csv()}")
        print("\n  2. Kommerzielle Modelle testen")
        print("     → Speichert in: commercial_models_benchmark.csv")
        print(f"{'=' * 60}")

        while True:
            try:
                choice = input("\nWähle Modus (1-2): ").strip()
                if choice == "1":
                    print("✓ Golden Standard Mode\n")
                    return "golden_standard"
                if choice == "2":
                    print("✓ Test Mode\n")
                    return "test"
                print("❌ Bitte 1 oder 2 eingeben")
            except KeyboardInterrupt:
                print("\n\n❌ Abgebrochen")
                return None

    def select_golden_standard_model(self) -> Optional[Tuple[str, str]]:
        """Holt das Golden Standard Modell aus Config."""
        info = self.validator.get_golden_standard_info()
        if not info:
            print("❌ Kein Golden Standard in Config definiert")
            return None

        provider_key, model_id, provider_config = info
        print(f"\n{'=' * 60}\n🏆 GOLDEN STANDARD MODELL\n{'=' * 60}")
        print(f"Provider: {provider_config.get('name', provider_key)}")
        print(f"Modell:   {model_id}\n{'=' * 60}\n")

        return (provider_key, model_id)

    def select_test_model(self) -> Optional[Tuple[str, str]]:
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

            score = test_inst.score_response(data.get("response", ""))
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
        is_golden_model: bool,
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
            if self.mode == "golden_standard":
                # User Requirement: "Fehlt der golden Standard, soll er dort nachsehen."
                # REUSE existing data for Golden Standard generation (don't re-run/pay).

                # Convert CSV strings to proper types for ResultManager
                try:
                    res = dict(cached_row)
                    res["total_score"] = float(res.get("total_score", 0))
                    res["max_score"] = float(res.get("max_score", 100))
                    res["percentage"] = float(res.get("percentage", 0))
                    res["execution_time"] = float(res.get("execution_time", 0))

                    # Print "Cached" status
                    badge = self.get_quality_badge(res["percentage"])
                    print(
                        f"[{index}/{total_count}] {asset_id:<15} | "
                        f"{asset_name[:20]:<20} {badge} "
                        f"Score: {res['percentage']:>6.2f} | "
                        f"Cost:   Cached | Time: {res['execution_time']:.1f}s"
                    )
                    return res
                except ValueError:
                    pass  # Malformed CSV row, fallback to re-run

            else:
                # Test Mode: Skip already processed tests (SSOT Behavior)
                return None

        # 2. JSON Cache (Golden Standard) - DISABLED
        # User Feedback: "Fehlt der golden Standard, soll er dort nachsehen [CSV].
        # Fehlen Werte ... soll ein benchmark ... angestößen werden."
        # recovering from JSON caused outdated version numbers/metadata in the leaderboard.

        # json_path = Path(f"golden_standards/{provider}/{asset_id}.json")
        # if is_golden_model and json_path.exists():
        #     if self.mode == "golden_standard" and not self.force:
        #         res = self._recover_from_json(
        #             json_path, asset_path, benchmark_info, provider, model
        #         )
        #         if res:
        #             ... return res

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
            print(f"\n❌ Fehler bei Ausführung ({asset_name}): {e}")
            return None

        response = exec_result.raw_response
        score = test_inst.score_response(response)

        # Build Standardized Result
        result = self.build_base_result(model, asset_data, score, exec_result, provider)

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

        # Add Version/Fingerprint if available from API
        # meta = exec_result.meta

        # Use Global SSOT (Dual Version format) from Fingerprinting Utility
        # We pass self.client if available to allow behavioral hashing
        version = ModelFingerprinter.get_unified_version(
            provider=provider,
            model_name=model,
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
                # pylint: disable=import-outside-toplevel
                from utils.scoring.llm_judge.judge_config import LLMJudgeConfig
                from utils.scoring.llm_judge.judge_runner import JudgeRunner
                # pylint: enable=import-outside-toplevel

                try:
                    judge_config = LLMJudgeConfig.from_dict(judge_cfg_dict)
                    # Apply optional per-module override
                    if "llm_judge_model" in benchmark_info:
                        judge_config.module_judge_model = benchmark_info[
                            "llm_judge_model"
                        ]

                    runner = JudgeRunner(judge_config)

                    raw_prompt = asset_data.get(
                        "prompt", asset_data.get("instruction", "")
                    )
                    golden = asset_data.get("golden_standard", "")
                    if isinstance(golden, dict):
                        golden = golden.get("text", "")
                    golden = str(golden)

                    judge_res = runner.score(
                        task_prompt=raw_prompt,
                        model_response=response,
                        golden_standard=golden,
                        module_id=eval_module_id,
                        rubric_override=asset_data.get("scoring", {}).get("rubric"),
                        tested_model_id=model,
                        tested_model_provider=provider,
                        response_time_ms=result.get("execution_time", 0) * 1000.0,
                    )

                    # Merge fields
                    result["llm_judge_score"] = judge_res.score
                    result["llm_judge_reasoning"] = judge_res.reasoning
                    result["llm_judge_latency_ms"] = judge_res.judge_latency_ms
                    result["llm_judge_provider_used"] = judge_res.judge_provider_used
                    result["llm_judge_model_used"] = judge_res.judge_model_used
                    result["llm_judge_parse_success"] = judge_res.parse_success
                    # Add sub-scores
                    result["judge_task_compliance"] = judge_res.judge_task_compliance
                    result["judge_output_quality"] = judge_res.judge_output_quality
                    result["judge_standard_adherence"] = judge_res.judge_standard_adherence

                    if judge_res.parse_success and judge_res.score is not None:
                        judge_scale = judge_config.scoring.scale
                        judge_pct = (judge_res.score / judge_scale) * 100

                        # Hybrid Score berechnen
                        regex_pct = result.get("percentage", 0.0)
                        hybrid_score = calculate_hybrid_score(
                            regex_score=regex_pct,
                            judge_score=judge_pct,
                            asset_config=asset_cfg,
                            module_config=benchmark_info,
                            judge_enabled=judge_config.enabled,
                        )

                        result["total_score"] = hybrid_score
                        result["percentage"] = hybrid_score
                        result["scoring_method"] = "hybrid"
                        result["judge_progress_status"] = (
                            f"⚖️ Judge: {judge_res.score}/{judge_scale} (Hybrid)"
                        )

                        # RECALCULATE contributions based on the new Hybrid score
                        result = calculate_score_contributions(result, asset_cfg)
                    else:
                        result["judge_progress_status"] = "❌ Judge: failed"

                except Exception as e:  # pylint: disable=broad-exception-caught
                    import traceback; traceback.print_exc(); logging.error("LLM Judge execution failed: %s", e)
                    result["judge_progress_status"] = "❌ Judge: failed"
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
        # MODIFIED v2.1: Only save if explicitly in golden_standard mode!
        # This prevents auto-updating the reference when just testing the reference model.
        if self.mode == "golden_standard":
            self._save_golden_json(
                provider, asset_id, response, exec_result.execution_time
            )
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
            rp_fallback = asset_data.get(
                "prompt", asset_data.get("instruction", "No prompt found")
            )
            rp = getattr(exec_result, "evaluated_prompt", "") or rp_fallback

            if result.get("scoring_method") in ["llm_judge", "hybrid"]:
                judge_provider = result.get("llm_judge_provider_used", "unknown")
                judge_model = result.get("llm_judge_model_used", "unknown")
                judge_info = f"*(Evaluated using {judge_provider} / {judge_model})*"

                # Fetch module-level category scores that are logged to CSV
                cat_section = ""
                cat_scores = score.get("category_scores", {})
                if cat_scores:
                    cat_section = "\n\n**Category Scores (Rule-based / CSV):**\n"
                    for cat_name, cat_vals in cat_scores.items():
                        cat_section += f"- **{cat_name}:** {cat_vals.get('achieved', 0)} / {cat_vals.get('max', 0)}\n"
                    cat_section += f"\n**Rule-based Total Score:** {score.get('total_score', 0)} / {score.get('max_score', 0)}"

                # Also capture any detail/reasoning arrays generated by the regex scorer
                details_section = ""
                if "details" in score and score["details"]:
                    details_section = "\n\n**Rule-based Evaluation Details:**\n"
                    details_data = score["details"]
                    if isinstance(details_data, list):
                        details_section += "\n".join([f"- {d}" for d in details_data])
                    else:
                        details_section += str(details_data)

                # Capture Sub-Scores if present
                subscore_section = ""
                if result.get("judge_task_compliance") is not None:
                    subscore_section = (
                        "\n\n**Judge Sub-Scores:**\n"
                        "| Dimension | Score |\n"
                        "|---|---|\n"
                        f"| Task Compliance | {result.get('judge_task_compliance')}/5 |\n"
                        f"| Output Quality | {result.get('judge_output_quality')}/5 |\n"
                        f"| Standard Adherence | {result.get('judge_standard_adherence')}/5 |"
                    )

                if result.get("scoring_method") == "hybrid":
                    judge_resp = f"{judge_info}\n\n**Hybrid Score:** {result.get('percentage', 'N/A')}%\n\n**LLM Judge Score (Raw):** {result.get('llm_judge_score', 'N/A')}\n\n**LLM Judge Reasoning:**\n{result.get('llm_judge_reasoning', 'No reasoning provided.')}{subscore_section}{cat_section}{details_section}"
                else:
                    judge_resp = f"{judge_info}\n\n**LLM Judge Score:** {result.get('llm_judge_score', 'N/A')}\n\n**LLM Judge Reasoning:**\n{result.get('llm_judge_reasoning', 'No reasoning provided.')}{subscore_section}{cat_section}{details_section}"
            else:
                judge_resp = f"**Regex / Rule Scorer ({result.get('scoring_method', 'unknown')}):**\n\n**Score:** {result.get('total_score', 0)} / {result.get('max_score', 0)}\n\n**Details:**\n```json\n{json.dumps(score, indent=2, ensure_ascii=False)}\n```"

            save_audit_log(
                model=result["model"],
                asset_id=result["asset_id"],
                prompt=rp,
                response=response,
                judge_response=judge_resp,
            )

        return result

    @staticmethod
    def _save_golden_json(
        provider: str, asset_id: str, response: str, execution_time: float
    ):
        """Saves the full response as JSON."""
        output_dir = Path(f"golden_standards/{provider}")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{asset_id}.json"

        data = {
            "id": asset_id,
            "provider": provider,
            "timestamp": datetime.now().isoformat(),
            "execution_time": execution_time,
            "response": response,
        }
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print("   💾 JSON gespeichert.")
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"   ⚠️  JSON Fehler: {e}")

    def _append_to_golden_csv(self, result: Dict[str, Any]):
        """Appends result to golden CSV."""
        self.result_manager.save_results([result], result_type="golden")
        print("   💾 Auch in Golden Standard CSV gespeichert.")

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

        # Dispatch Batch Mode (e.g. Political Compass) via Config
        if benchmark_info.get("execution_mode") == "batch":
            batch_asset_id = str(benchmark_info.get("id", "batch_module"))
            cached_res = self.existing_benchmarks.get((model, batch_asset_id))
            if not self.force and cached_res:
                print(
                    f"⏩ Überspringe {benchmark_info['name']} (Batch-Modus; Bereits im Cache vorhanden)"
                )
                return [cached_res.copy()]

            # Dynamic Loading
            module_path = Path(str(benchmark_info.get("module_path", "")))
            test_file = module_path / "test.py"
            test_class_name = str(benchmark_info.get("test_class", ""))

            try:
                test_class = load_test_class(test_file, test_class_name)
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error(
                    "Failed to load batch module %s: %s", benchmark_info["name"], e
                )
                return []

            # TODO: Generic ResultManager for batch modules
            # For now, we assume Political Compass structure for batch mode
            # Ideally, the TestClass should handle IO or return a standard object
            # Imports moved to top-level

            print(
                f"🛠️  Initialisiere Batch-Test: {benchmark_info['name']} ({provider}:{model})"
            )
            test = test_class()

            # Load assets dynamically from module path
            assets_dir = module_path / "assets"
            if not assets_dir.exists():
                print(f"❌ Assets directory not found: {assets_dir}")
                return []

            if hasattr(test, "load_questions"):
                test.load_questions(str(assets_dir))

            if hasattr(test, "questions") and not test.questions:
                print("❌ Keine Fragen geladen!")
                return []

            # Apply runs config
            min_runs = benchmark_info.get("min_runs", 1)
            test.num_runs = max(num_runs, min_runs)

            client = LLMClient(config=self.validator.config)

            # Execution
            result_wrapper = test.execute(
                model=model, llm_client=client, provider=provider
            )

            # Reporting
            try:
                report = json.loads(result_wrapper.raw_response)
            except (json.JSONDecodeError, TypeError) as e:
                print(f"❌ Batch Execution Failed: Invalid JSON response ({e})")
                return []

            is_political_compass = (
                benchmark_info.get("id", "")
                in ["political_compass", "political_compass_v3"]
                or benchmark_info.get("name", "") == "Political Compass"
            )

            if is_political_compass and ResultManager:
                try:
                    ResultManager.print_summary(report)
                    ResultManager.save_json(report, Path("outputs/runs"))
                except Exception as e:  # pylint: disable=broad-exception-caught
                    print(f"⚠️ Political Compass Reporting Error: {e}")

                # Save to shared CSV for Leaderboard
                try:
                    pc_csv = Path("benchmark_scores/political_compass_results.csv")
                    pc_csv.parent.mkdir(exist_ok=True, parents=True)

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

                    # Read logic for existing file to append/update
                    pc_rows = []
                    if pc_csv.exists():
                        with open(pc_csv, "r", encoding="utf-8") as f:
                            # Handle potential schema mismatch on read
                            reader = csv.DictReader(f)
                            pc_rows = list(reader)
                            # If file on disk has more columns than we know, update known fieldnames
                            if reader.fieldnames:
                                for col in reader.fieldnames:
                                    if col not in fieldnames:
                                        fieldnames.append(col)

                    # Remove old entry for this model if exists
                    pc_rows = [r for r in pc_rows if r.get("model") != model]

                    # Construct Data Object
                    data_object = format_political_compass_data(report)

                    # Resolve Version using SSOT (Single Source of Truth)
                    # We pass the client to ensure behavioral hashing is consistent with other runs.
                    version = get_model_version(model, provider, client=client)

                    new_row = prepare_pc_csv_row(
                        model, report, data_object, model_version=version
                    )
                    new_row["timestamp"] = datetime.now().isoformat()
                    pc_rows.append(new_row)

                    with open(pc_csv, "w", encoding="utf-8", newline="") as f:
                        writer = csv.DictWriter(
                            f, fieldnames=fieldnames, extrasaction="ignore"
                        )
                        writer.writeheader()
                        writer.writerows(pc_rows)
                except Exception as e:  # pylint: disable=broad-exception-caught
                    print(f"⚠️ Political Compass CSV Error: {e}")

            version = get_model_version(model, provider, client=client)

            # Create Standard Result for CSV
            std_result = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": report.get("status", "success"),
                "provider": provider,
                "model": model,
                "model_version": version,
                "asset_id": benchmark_info.get("id", "batch_module"),
                "asset_name": benchmark_info.get("name", "Batch Module"),
                "total_score": report.get("total_score", report.get("score", 0.0)),
                "max_score": 100,
                "percentage": report.get("total_score", report.get("score", 0.0)),
                "execution_time": round(result_wrapper.execution_time or 0, 1),
                "response_length": 0,
                "tier": report.get("tier", "N/A"),
                "cost_usd": result_wrapper.cost_usd,
                "tokens": result_wrapper.tokens_used,
            }
            return [std_result]

        # Check Golden Standard Status
        golden_info = self.validator.get_golden_standard_info()
        is_golden_model = False
        if golden_info:
            g_provider, g_model, _ = golden_info
            if provider == g_provider and model == g_model:
                is_golden_model = True

        print(
            f"\n{'=' * 60}\n📊 STARTE BENCHMARK: {benchmark_info['name']}\n{'=' * 60}"
        )
        print(f"Provider: {provider}\nModell:   {model}\nModus:    {self.mode}")
        if is_golden_model:
            print("ℹ️  Dies ist das Golden Standard Modell.")

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
                is_golden_model,
                index=i,
                total_count=total_assets,
                limiter=run_limiter,
            )
            if res:
                results.append(res)

        return results

    def save_results(self, results: List[Dict[str, Any]]):
        """Saves results to CSV."""
        if not results:
            return

        target = "commercial"
        if self.mode == "golden_standard":
            target = "golden"
            # Also save to commercial for record keeping
            self.result_manager.save_results(results, result_type="commercial")

        path = self.result_manager.save_results(results, result_type=target)
        if path:
            print(f"\n💾 Ergebnisse gespeichert: {path}")

    def print_summary(self, results: List[Dict[str, Any]]):
        """Prints benchmark summary."""
        if not results:
            return

        total_score = sum(r["total_score"] for r in results)
        max_possible = sum(r["max_score"] for r in results)
        avg_pct = (total_score / max_possible * 100) if max_possible > 0 else 0

        # Calculate Costs & Time
        def safe_float(val):
            try:
                return float(val) if val not in (None, "") else 0.0
            except ValueError:
                return 0.0

        total_cost = sum(safe_float(r.get("cost_usd")) for r in results)
        avg_time = (
            sum(safe_float(r.get("execution_time")) for r in results) / len(results)
            if results
            else 0
        )

        # Get Remaining Budget
        provider = results[0]["provider"] if results else "mistral"
        remaining = self.client.cost_tracker.get_remaining_budget(provider)
        rem_str = f"${remaining:.2f}" if remaining is not None else "N/A"

        print(f"{'─' * 66}")
        # Module Total: $0.0471 | Avg Time: 13.2s | Remaining Budget: $19.95
        print(
            f"Module Total: ${total_cost:.4f} | Avg Time: {avg_time:.1f}s | Remaining Budget: {rem_str}"
        )

        # Keep Score Summary
        badge = self._get_quality_badge(avg_pct)
        print(
            f"Overall Quality: {avg_pct:.2f}% {badge} ({total_score}/{max_possible} Pts)"
        )

        # Check for Golden Standard Breach (Only in Test Mode)
        if self.mode != "golden_standard":
            try:
                csv_path = Path("benchmark_scores/golden_standard_benchmark.csv")
                if csv_path.exists():
                    with open(csv_path, encoding="utf-8") as f:
                        reader = csv.DictReader(f)
                        # Map asset_id to percentage
                        golden_map = {
                            row.get("asset_id"): float(row.get("percentage", 0.0))
                            for row in reader
                        }

                    current_assets = [r["asset_id"] for r in results]
                    matching_golden_scores = [
                        golden_map[aid] for aid in current_assets if aid in golden_map
                    ]

                    if matching_golden_scores:
                        golden_avg = sum(matching_golden_scores) / len(
                            matching_golden_scores
                        )
                        # Consider it surpassed if slightly more than 0 due to float precision,
                        # but show message only if meaningful difference (e.g. >= 0.01%)
                        if avg_pct > golden_avg:
                            diff = avg_pct - golden_avg
                            # Only warn if difference is significant enough to show up in .2f format
                            if diff >= 0.005:
                                print(f"\n{'=' * 66}")
                                print(
                                    f"⚠️  ACHTUNG: GOLDEN STANDARD ÜBERTROFFEN! (+{diff:.2f}%)"
                                )
                                print(f"{'=' * 66}")
                                print(
                                    "Dieses Modell schneidet BESSER ab als die aktuelle Referenz."
                                )
                                print("Bitte prüfen: Ist der Golden Standard veraltet?")
                                print(
                                    "Handlungsempfehlung: `make generate-golden` (falls das Ergebnis validiert ist)."
                                )
            except Exception:  # pylint: disable=broad-exception-caught
                pass

        print(f"{'=' * 66}\n")


def main():
    """CLI Entry Point."""
    parser = argparse.ArgumentParser(description="Commercial Benchmark Runner")
    parser.add_argument(
        "--mode", choices=["golden_standard", "test"], help="Benchmark mode"
    )
    parser.add_argument(
        "--auto", action="store_true", help="Run automatically without interaction"
    )
    parser.add_argument(
        "--force", action="store_true", help="Force overwrite existing Golden Standards"
    )
    args = parser.parse_args()

    print(f"\n{'=' * 60}\n🚀 KOMMERZIELLE MODELLE BENCHMARK\n{'=' * 60}")

    runner = CommercialBenchmarkRunner()

    # 1. Select Mode
    mode = args.mode or runner.select_mode()
    if not mode:
        return
    runner = CommercialBenchmarkRunner(mode=mode, force=args.force)

    # 2. Select Model
    if mode == "golden_standard":
        result = runner.select_golden_standard_model()
    else:
        result = runner.select_test_model()

    if not result:
        return

    provider, model_id = result

    # 3. Select Benchmark (or Auto)
    if args.auto:
        print("\n🚀 Starte automatischen Golden Standard Run für alle Module...")
        for cat_key, cat_info in runner.benchmark_categories.items():
            # Skip Political Compass in Golden Standard (Bias != Benchmark)
            if mode == "golden_standard" and cat_key == "political_compass":
                print(
                    f"⏩ Überspringe {cat_info['name']} im Golden Standard Modus (Bias-Benchmark)"
                )
                continue

            results = runner.run_benchmark(provider, model_id, cat_info)
            runner.save_results(results)
            runner.print_summary(results)
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
                runner.save_results(results)
                runner.print_summary(results)
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
        runner.save_results(results)
        runner.print_summary(results)
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"\n❌ Fatal Error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
