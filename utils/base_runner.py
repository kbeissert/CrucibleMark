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

        # Inject module token-budget as max_tokens API cap (fair comparability across providers)
        # Use module_path.parent.name (e.g. "code_quality") not benchmark_info["path"].name
        # which would be "assets" when path = "benchmark_modules/code_quality/assets"
        _module_key = module_path.parent.name
        _token_budget: int | None = self.validator.config.get("token_budgets", {}).get(_module_key)

        # exec_result is now a BenchmarkResult object
        # _module_key wird mitübergeben damit openai.py das Reasoning-Budget per Modul nachschlagen kann
        if _token_budget is not None:
            exec_result = test_instance.execute(model, self.client, provider=provider, max_tokens=_token_budget, _module_key=_module_key)
        else:
            exec_result = test_instance.execute(model, self.client, provider=provider)

        # Inject finish_reason if available
        if hasattr(self.client, "last_response_metadata"):
            # Check token_limit_fallback FIRST: a ctx_overflow (fallback=True) must prevent
            # token_limit_cutoff from being set, even if finish_reason="length".
            fb = self.client.last_response_metadata.get("token_limit_fallback")
            if fb:
                exec_result.token_limit_fallback = True

            fr = self.client.last_response_metadata.get("finish_reason")
            if fr:
                exec_result.finish_reason = str(fr)
                # Only mark as budget cutoff when NOT a ctx overflow (fallback already set above)
                if str(fr).lower() in ["length", "max_tokens"] and not getattr(exec_result, "token_limit_fallback", False):
                    exec_result.token_limit_cutoff = True

            tlu = self.client.last_response_metadata.get("token_limit_used")
            if tlu is not None:
                exec_result.token_limit_used = tlu

            tps_eval = self.client.last_response_metadata.get("tps_eval")
            if tps_eval is not None:
                exec_result.tps_eval = tps_eval

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

        # Native eval speed: eval_count / eval_duration from Ollama response (excludes prefill).
        # Remains None when not available (cloud proxy, non-Ollama providers).
        tps_eval = getattr(exec_result, "tps_eval", None)

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
            "tier": getattr(exec_result, "tier", score.get("tier", "Tier 1 (Undefined)")),
            # Use object attributes
            "execution_time": round(exec_result.execution_time, 4),
            "tokens_used": getattr(exec_result, "tokens_used", 0),
            "tokens_per_second": tps,
            "tps_eval": tps_eval,
            "load_time": round(getattr(exec_result, "load_time", 0.0), 4),
            "response_length": len(exec_result.raw_response),
            "finish_reason": getattr(exec_result, "finish_reason", None),
            "token_limit_cutoff": getattr(exec_result, "token_limit_cutoff", False),
            "token_limit_fallback": getattr(exec_result, "token_limit_fallback", False),
            "token_limit_used": getattr(exec_result, "token_limit_used", None),
            "thought_tag_compliance": getattr(exec_result, "thought_tag_compliance", None),
        }

        # Add category scores
        for cat, val in score.get("category_scores", {}).items():
            result[cat] = f"{val['achieved']}/{val['max']}"

        return result

    def save_results(self, results: list, result_type: str = None) -> None:
        """Wird von den Kind-Klassen verwendet, um per ResultManager zu speichern."""
        if not results:
            return

        path = self.result_manager.save_results(results, result_type=result_type)
        if path:
            print(f"\n💾 Ergebnisse gespeichert: {path}")

    def print_summary(self, results: list, model: str) -> None:
        """Einheitliche Zusammenfassungs-Ausgabe."""
        if not results:
            return

        successful = [r for r in results if r.get("status") != "error"]
        failed = [r for r in results if r.get("status") == "error"]

        # Separate Probe Result from Scoring
        probe_result = next(
            (r for r in successful if r.get("asset_id") in ("system_warmup_probe", "warmup_probe")), None
        )
        scoring_candidates = [
            r for r in successful if r.get("asset_id") not in ("system_warmup_probe", "warmup_probe")
        ]

        if not scoring_candidates and not probe_result:
            print(f"\n{'=' * 60}\n📈 BENCHMARK ZUSAMMENFASSUNG\n{'=' * 60}")
            print(f"Modell: {model}\n❌ Alle {len(results)} Tests fehlgeschlagen!")
            return

        scored_results = [
            r for r in scoring_candidates
            if not str(r.get("asset_id", "")).startswith("political_compass")
        ]

        if not scored_results:
            if scoring_candidates:
                avg_time = sum(r.get("execution_time", 0) for r in scoring_candidates) / len(scoring_candidates)
                print("\n✅ Benchmark abgeschlossen für Modul: Political Compass")
                print(f"   Modell: {model}")
                print(f"   Dauer:  {avg_time:.1f}s")
            elif probe_result:
                print("\n⚠️ Nur System Probe ausgeführt.")
            return

        def safe_float(val):
            try:
                return float(val) if val not in (None, "") else 0.0
            except ValueError:
                return 0.0

        avg_score = sum(safe_float(r.get("total_score", 0)) for r in scored_results) / len(scored_results)
        avg_max = sum(safe_float(r.get("max_score", 0)) for r in scored_results) / len(scored_results)
        avg_pct = sum(safe_float(r.get("percentage", 0)) for r in scored_results) / len(scored_results)

        valid_times = [safe_float(r.get("execution_time")) for r in scoring_candidates]
        avg_time = sum(valid_times) / len(valid_times) if valid_times else 0

        quality = self.get_quality_badge(avg_pct)

        print(f"\n✅ Modul abgeschlossen: {model}")
        print(f"Tests: {len(scoring_candidates)} ({len(scoring_candidates)} ✅, {len(failed)} ❌)")
        print("\n📊 Durchschnitt (erfolgreiche Tests des Moduls):")
        print(f"   Dein Modell: {avg_score:.2f}/{avg_max:.0f} ({avg_pct:.2f}%) {quality}")
        print(f"   Avg Speed:   {avg_time:.1f}s (Execution)")

        # Commercial costs
        total_cost = sum(safe_float(r.get("cost_usd")) for r in results)
        if total_cost > 0:
            print(f"   Modul Kosten: ${total_cost:.4f}")
            provider = results[0].get("provider", "unknown")
            if hasattr(self.client, "cost_tracker"):
                remaining = self.client.cost_tracker.get_remaining_budget(provider)
                if remaining is not None:
                    print(f"   Remaining Budget: ${remaining:.2f}")

        if probe_result:
            load_time = safe_float(probe_result.get("load_time", 0))
            print(f"   Cold Start:  {load_time:.2f}s (Initial Load)")

        self._print_reference_comparison(scored_results)
        self._print_best_worst(scored_results)
        self._print_tiered_analysis(scored_results)

        if failed:
            print("\n❌ Fehlgeschlagen:")
            for r in failed:
                print(f"   {r.get('asset_name', 'Unknown')[:40]}: {r.get('error_message', 'No details')}")
        print(f"{'=' * 60}")

    def _print_reference_comparison(self, results: list):
        if not results or results[0].get("reference_score", 0) <= 0:
            return
        avg_ref = sum(r.get("reference_score", 0) for r in results) / len(results)
        avg_diff = sum(r.get("score_difference", 0) for r in results) / len(results)

        print(f"   Referenz:    {avg_ref:.2f}/100")
        if avg_diff > 0:
            print(f"   🎯 Differenz: +{avg_diff:.2f} (besser!)")
        elif avg_diff < 0:
            print(f"   📉 Differenz: {avg_diff:.2f} (Gap)")
        else:
            print("   ⚖️  Differenz: ±0")

    def _print_best_worst(self, results: list):
        if not results:
            return
        sorted_res = sorted(results, key=lambda x: x.get("percentage", 0), reverse=True)
        print("\n🏆 Beste Tests:")
        for r in sorted_res[:3]:
            q = self.get_quality_badge(r.get("percentage", 0))
            d = r.get("score_difference", 0)
            diff_str = f" ({d:+.2f})" if d != 0 else ""
            print(f"   {r.get('asset_name', 'Unknown')[:35]:<35}: {r.get('percentage', 0):.2f}% {q}{diff_str}")

        print("\n⚠️  Schwächste Tests:")
        for r in sorted_res[-3:]:
            q = self.get_quality_badge(r.get("percentage", 0))
            d = r.get("score_difference", 0)
            diff_str = f" ({d:+.2f})" if d != 0 else ""
            print(f"   {r.get('asset_name', 'Unknown')[:35]:<35}: {r.get('percentage', 0):.2f}% {q}{diff_str}")

    def _print_tiered_analysis(self, results: list):
        reasoning_res = [r for r in results if str(r.get("details", {}).get("asset_id", "")).startswith("reasoning_")]
        if not reasoning_res:
            return
        print(f"\n🧠 REASONING ANALYSIS (Tiered)\n{'-' * 60}")
        t1_scores = [r.get("total_score", 0) for r in reasoning_res if "Tier 1" in str(r.get("details", {}).get("tier", "Tier 1"))]
        t2_scores = [r.get("total_score", 0) for r in reasoning_res if "Tier 2" in str(r.get("details", {}).get("tier", ""))]

        t1_avg = sum(t1_scores) / len(t1_scores) if t1_scores else 0
        t2_avg = sum(t2_scores) / len(t2_scores) if t2_scores else 0

        # We don't have self.TIER_SCORE_HIGH, set some constants
        profile = "🤖  Balanced"
        if t2_avg > 80:
            profile = "🧠  Deep Thinker (Complex Logic Expert)"
        elif t1_avg >= 80:
            profile = "🏎️  Daily Driver (Fast & Reliable)"
        elif t1_avg < 60:
            profile = "⚠️  Needs Improvement"

        print(f"   Tier 1 (Operational): {t1_avg:.2f}%")
        print(f"   Tier 2 (Deep Logic):  {t2_avg:.2f}%")
        print(f"   Profile: {profile}\n{'-' * 60}")

    def execute_batch_module(
        self,
        model: str,
        benchmark_info: dict,
        provider: str,
        num_runs: int = 1,
        force: bool = False,
        existing_benchmarks: dict = None
    ) -> list:
        """Führt Batch-Module (z.B. Political Compass) zentral aus."""
        import json
        from datetime import datetime
        from pathlib import Path
        from utils.module_loader import load_test_class
        from utils.model_utils import get_model_version
        from utils.scoring.political_compass_handler import PoliticalCompassHandler

        batch_asset_id = str(benchmark_info.get("id", "batch_module"))
        if existing_benchmarks and not force:
            cached_res = existing_benchmarks.get((model, batch_asset_id))
            if cached_res:
                print(f"⏩ Überspringe {benchmark_info.get('name', '')} (Batch-Modus; Bereits im Cache vorhanden)")
                return [cached_res.copy()]

        # Fallback-Check: political_compass_leaderboard.csv direkt prüfen.
        # Die Standard-CSVs können nach einem Reset leer sein, während PC-Ergebnisse
        # autark im Leaderboard fortbestehen. Verhindert teure Re-Runs via `make political-compass`.
        if not force and PoliticalCompassHandler.is_political_compass(benchmark_info):
            import csv as _csv
            pc_leaderboard = Path("benchmark_scores/political_compass_leaderboard.csv")
            if pc_leaderboard.exists():
                try:
                    with pc_leaderboard.open("r", encoding="utf-8") as _f:
                        if any(row.get("model") == model for row in _csv.DictReader(_f)):
                            print(
                                f"⏩ Überspringe {benchmark_info.get('name', '')} "
                                f"(PC-Leaderboard; {model} bereits bewertet)"
                            )
                            return []
                except (OSError, _csv.Error):
                    pass  # Bei Lesefehler: sicher durchlaufen und normal ausführen

        module_path = Path(str(benchmark_info.get("module_path", "")))
        test_file = module_path / "test.py"
        test_class_name = str(benchmark_info.get("test_class", ""))

        if not test_class_name:
            import logging
            logging.getLogger(__name__).error("Keine gültige Test-Klasse für %s definiert.", benchmark_info.get("name"))
            return []

        try:
            test_class_type = load_test_class(test_file, test_class_name)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error("Failed to load batch module %s: %s", benchmark_info.get("name"), e)
            return []

        print(f"🛠️  Initialisiere Batch-Test: {benchmark_info.get('name')} ({provider}:{model})")
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

        # Execution
        result_wrapper = test.execute(model=model, llm_client=self.client, provider=provider)

        # Propagate quota/budget exhaustion detected inside the module
        if getattr(test, "_quota_exhausted", False):
            print(f"   💸 Budget-/Quota-Fehler in Batch-Modul erkannt. Provider wird als erschöpft markiert.")
            self.provider_quota_exhausted = True
            return []

        try:
            report = json.loads(result_wrapper.raw_response)
        except (json.JSONDecodeError, TypeError) as e:
            print(f"❌ Batch Execution Failed: Invalid JSON response ({e})")
            return []

        model_version = get_model_version(model, provider=provider, client=self.client)

        if PoliticalCompassHandler.is_political_compass(benchmark_info):
            PoliticalCompassHandler.handle_results(
                model=model,
                report=report,
                model_version=model_version,
                test_instance=test,
                audit_mode=getattr(self, "audit_mode", False),
                provider_type=provider
            )
        else:
            print(f"\n📊 {benchmark_info.get('name', 'Batch Module')} Summary:")
            print(f"Modell: {model}")
            print(f"Score: {report.get('score', report.get('total_score', 0.0)):.2f}/100")
            print(f"Erfolgsrate: {report.get('success_rate', 'N/A')}")
            if "badge" in report:
                print(f"Badge: {report['badge']}\n")

        std_result = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": report.get("status", "success"),
            "provider": provider,
            "model": model,
            "model_version": model_version,
            "asset_id": batch_asset_id,
            "asset_name": benchmark_info.get("name", "Batch Module"),
            "total_score": report.get("total_score", report.get("score", 0.0)),
            "max_score": 100,
            "percentage": report.get("total_score", report.get("score", 0.0)),
            "execution_time": round(result_wrapper.execution_time or 0, 1),
            "response_length": getattr(result_wrapper, "response_length", 0) or 0,
            "tier": report.get("tier", "N/A"),
            "cost_usd": getattr(result_wrapper, "cost_usd", "0.000000"),
            "tokens": getattr(result_wrapper, "tokens_used", 0)
        }
        return [std_result]
