"""
Base Benchmark Runner
Stellt gemeinsame Funktionalität für lokale und kommerzielle Runner bereit.
"""

import logging
from pathlib import Path
from typing import Any
from datetime import datetime

from utils.llm_client import LLMClient
from utils.config_validator import ConfigValidator
from utils.result_manager import ResultManager
from utils.module_loader import load_test_class
from utils.constants import QUALITY_EXCELLENT, QUALITY_GOOD, QUALITY_OK
from utils.model_utils import resolve_token_budget, get_hardware_profile, resolve_model_cfg_for

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
        benchmark_info: dict[str, Any],
        provider: str = "ollama",
    ) -> tuple[Any, BenchmarkResult]:
        """Lädt und führt ein Test-Modul aus (Shared Logic)."""
        # Pfad-Logik vereinheitlichen
        if "path" in benchmark_info:
            # z.B. benchmark_modules/code_quality/assets -> benchmark_modules/code_quality/test.py
            path = Path(benchmark_info["path"])
            module_path = path.parent / "test.py" if path.name == "assets" else path / "test.py"
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
        #
        # SSoT (ab v4.7.1): provider wird durchgereicht, damit ein aktiver
        # `thinking_override` in der Provider-Card das Token-Budget beeinflusst
        # (z.B. value:false → kein 5x-Reasoning-Multiplikator fuer Cost-Benchmarks).
        _module_key = module_path.parent.name
        _raw_budget: int | None = self.validator.config.get("token_budgets", {}).get(_module_key)
        _token_budget, _ = resolve_token_budget(
            model, _raw_budget, self.validator.config, _module_key, provider=provider
        )

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

            self._inject_client_metadata(exec_result)

        return test_instance, exec_result

    def _inject_client_metadata(self, exec_result: BenchmarkResult) -> None:
        """Überträgt relevante Client-/Response-Metadaten in das Exec-Result.

        Setzt token_limit_fallback, finish_reason, token_limit_cutoff,
        token_limit_used, tps_eval, reasoning_tokens und think_content aus
        ``self.client.last_response_metadata``, falls vorhanden.
        """
        if not hasattr(self.client, "last_response_metadata"):
            return
        meta = self.client.last_response_metadata

        # Check token_limit_fallback FIRST: a ctx_overflow (fallback=True) must prevent
        # token_limit_cutoff from being set, even if finish_reason="length".
        fb = meta.get("token_limit_fallback")
        if fb:
            exec_result.token_limit_fallback = True

        fr = meta.get("finish_reason")
        if fr:
            exec_result.finish_reason = str(fr)
            if str(fr).lower() in ["length", "max_tokens"] and not getattr(exec_result, "token_limit_fallback", False):
                exec_result.token_limit_cutoff = True

        tlu = meta.get("token_limit_used")
        if tlu is not None:
            exec_result.token_limit_used = tlu

        tps_eval = meta.get("tps_eval")
        if tps_eval is not None:
            exec_result.tps_eval = tps_eval

        rt = meta.get("reasoning_tokens")
        if rt is not None:
            exec_result.reasoning_tokens = rt

        tc = meta.get("think_content")
        if tc is not None:
            exec_result.think_content = tc

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def build_base_result(
        self,
        model: str,
        asset_data: dict[str, Any],
        exec_result: BenchmarkResult,  # Updated type hint
        provider: str,
    ) -> dict[str, Any]:
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

        # Thinking-Modus aus model_cfg ableiten (vLLM dual-profile / llama.cpp / n/a)
        thinking_mode = self._resolve_thinking_mode(model, provider)

        # Build dict from BenchmarkResult object + Scoring
        result = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": exec_result.status,
            "provider": provider,
            "hardware_profile": get_hardware_profile(self.validator.config, provider),
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
            "reasoning_tokens": getattr(exec_result, "reasoning_tokens", None),
            "token_limit_cutoff": getattr(exec_result, "token_limit_cutoff", False),
            "token_limit_fallback": getattr(exec_result, "token_limit_fallback", False),
            "token_limit_used": getattr(exec_result, "token_limit_used", None),
            "thought_tag_compliance": getattr(exec_result, "thought_tag_compliance", None),
            "think_content": getattr(exec_result, "think_content", None),
            "thinking_mode": thinking_mode,
        }

        # Add category scores
        for cat, val in score.get("category_scores", {}).items():
            result[cat] = f"{val['achieved']}/{val['max']}"

        return result

    def _resolve_thinking_mode(self, model: str, provider: str) -> str:
        """Leitet den Thinking-Modus aus der model_cfg ab.

        Returns:
            "Thinking" — vLLM dual-profile thinking oder llama.cpp enable_thinking=true
            "Standard" — vLLM dual-profile standard oder llama.cpp enable_thinking=false
            "n/a" — keine Thinking-Konfiguration (Cloud/Commercial ohne Toggle)
        """
        try:
            model_cfg = resolve_model_cfg_for(model, self.validator.config)
            if not model_cfg:
                return "n/a"
            # vLLM dual-profile: card_model_id vorhanden → Thinking-Profil
            if "card_model_id" in model_cfg:
                return "Thinking"
            # vLLM dual-profile: chat_template_kwargs.enable_thinking → Standard/Thinking
            ctk = model_cfg.get("chat_template_kwargs")
            if isinstance(ctk, dict) and "enable_thinking" in ctk:
                return "Thinking" if ctk["enable_thinking"] else "Standard"
            # llama.cpp: enable_thinking Flag
            if "enable_thinking" in model_cfg:
                return "Thinking" if model_cfg["enable_thinking"] else "Standard"
        except Exception:  # pylint: disable=broad-except
            pass
        return "n/a"

    def save_results(self, results: list, result_type: str | None = None) -> None:
        """Wird von den Kind-Klassen verwendet, um per ResultManager zu speichern."""
        if not results:
            return

        path = self.result_manager.save_results(results, result_type=result_type)
        if path:
            logger.info(f"\n💾 Ergebnisse gespeichert: {path}")
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
            logger.info(f"\n{'=' * 60}\n📈 BENCHMARK ZUSAMMENFASSUNG\n{'=' * 60}")
            logger.error(f"Modell: {model}\n❌ Alle {len(results)} Tests fehlgeschlagen!")
            return

        scored_results = [
            r for r in scoring_candidates
            if not str(r.get("asset_id", "")).startswith("political_compass")
        ]

        if not scored_results:
            if scoring_candidates:
                avg_time = sum(r.get("execution_time", 0) for r in scoring_candidates) / len(scoring_candidates)
                logger.info("\n✅ Benchmark abgeschlossen für Modul: Political Compass")
                logger.info(f"   Modell: {model}")
                logger.info(f"   Dauer:  {avg_time:.1f}s")
            elif probe_result:
                logger.warning("\n⚠️ Nur System Probe ausgeführt.")
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

        logger.info(f"\n✅ Modul abgeschlossen: {model}")
        logger.info(f"Tests: {len(scoring_candidates)} ({len(scoring_candidates)} ✅, {len(failed)} ❌)")
        logger.info("\n📊 Durchschnitt (erfolgreiche Tests des Moduls):")
        logger.info(f"   Dein Modell: {avg_score:.2f}/{avg_max:.0f} ({avg_pct:.2f}%) {quality}")
        logger.info(f"   Avg Speed:   {avg_time:.1f}s (Execution)")
        # Commercial costs
        total_cost = sum(safe_float(r.get("cost_usd")) for r in results)
        if total_cost > 0:
            logger.info(f"   Modul Kosten: ${total_cost:.4f}")
        if probe_result:
            load_time = safe_float(probe_result.get("load_time", 0))
            logger.info(f"   Cold Start:  {load_time:.2f}s (Initial Load)")
        self._print_reference_comparison(scored_results)
        self._print_best_worst(scored_results)
        self._print_tiered_analysis(scored_results)

        if failed:
            logger.error("\n❌ Fehlgeschlagen:")
            for r in failed:
                logger.info(f"   {r.get('asset_name', 'Unknown')[:40]}: {r.get('error_message', 'No details')}")
        logger.info(f"{'=' * 60}")
    def _print_reference_comparison(self, results: list):
        if not results or results[0].get("reference_score", 0) <= 0:
            return
        avg_ref = sum(r.get("reference_score", 0) for r in results) / len(results)
        avg_diff = sum(r.get("score_difference", 0) for r in results) / len(results)

        logger.info(f"   Referenz:    {avg_ref:.2f}/100")
        if avg_diff > 0:
            logger.info(f"   🎯 Differenz: +{avg_diff:.2f} (besser!)")
        elif avg_diff < 0:
            logger.info(f"   📉 Differenz: {avg_diff:.2f} (Gap)")
        else:
            logger.info("   ⚖️  Differenz: ±0")
    def _print_best_worst(self, results: list):
        if not results:
            return
        sorted_res = sorted(results, key=lambda x: x.get("percentage", 0), reverse=True)
        logger.info("\n🏆 Beste Tests:")
        for r in sorted_res[:3]:
            q = self.get_quality_badge(r.get("percentage", 0))
            d = r.get("score_difference", 0)
            diff_str = f" ({d:+.2f})" if d != 0 else ""
            logger.info(f"   {r.get('asset_name', 'Unknown')[:35]:<35}: {r.get('percentage', 0):.2f}% {q}{diff_str}")
        logger.warning("\n⚠️  Schwächste Tests:")
        for r in sorted_res[-3:]:
            q = self.get_quality_badge(r.get("percentage", 0))
            d = r.get("score_difference", 0)
            diff_str = f" ({d:+.2f})" if d != 0 else ""
            logger.info(f"   {r.get('asset_name', 'Unknown')[:35]:<35}: {r.get('percentage', 0):.2f}% {q}{diff_str}")
    def _print_tiered_analysis(self, results: list):
        reasoning_res = [r for r in results if str(r.get("details", {}).get("asset_id", "")).startswith("reasoning_")]
        if not reasoning_res:
            return
        logger.info(f"\n🧠 REASONING ANALYSIS (Tiered)\n{'-' * 60}")
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

        logger.info(f"   Tier 1 (Operational): {t1_avg:.2f}%")
        logger.info(f"   Tier 2 (Deep Logic):  {t2_avg:.2f}%")
        logger.info(f"   Profile: {profile}\n{'-' * 60}")
    def execute_batch_module(
        self,
        model: str,
        benchmark_info: dict,
        provider: str,
        num_runs: int = 1,
        force: bool = False,
        existing_benchmarks: dict | None = None
    ) -> list:
        """Führt Batch-Module (z.B. Political Compass) zentral aus."""
        # SSoT für Batch-Module: Skip-Logik ausschließlich über das modul-spezifische
        # Leaderboard (z.B. political_compass_leaderboard.csv), NICHT über die 3-CSVs.
        #
        # Hintergrund: Der vorherige Cache-Hit auf `existing_benchmarks` hat
        # `(model, batch_asset_id)` aus cloud/local/commercial_models_benchmark.csv
        # verwendet. Dieser Eintrag wird zwar vom UnifiedBenchmarkRunner.save_results()
        # geschrieben, ABER die PC-spezifische `save_leaderboard_csv()` wird nur
        # in `PoliticalCompassHandler.handle_results()` aufgerufen — und die wurde
        # durch den early-return hier umgangen. Folge: PC-Daten in pc_results.csv
        # vorhanden, aber kein Leaderboard-Eintrag → "Pending" im Hauptboard.
        #
        # Der Fallback-Check unten prüft das autarke PC-Leaderboard und ist die
        # einzige verlässliche Quelle der Wahrheit für Batch-Module.
        batch_asset_id = str(benchmark_info.get("id", "batch_module"))

        cached_result = self._check_batch_cache_skip(
            model, batch_asset_id, benchmark_info, existing_benchmarks, force,
        )
        if cached_result is not None:
            return cached_result

        if self._check_pc_leaderboard_skip(model, benchmark_info, force):
            return []

        test = self._load_batch_test(benchmark_info, model, provider)
        if test is None:
            return []

        return self._run_batch_test(test, model, benchmark_info, provider, num_runs, batch_asset_id)

    def _check_batch_cache_skip(
        self,
        model: str,
        batch_asset_id: str,
        benchmark_info: dict,
        existing_benchmarks: dict | None,
        force: bool,
    ) -> list | None:
        """Prüft den 3-CSV-Cache auf einen vorhandenen Batch-Eintrag.

        Returns:
            Liste mit Kopie des Cache-Eintrags bei Skip (nicht-PC-Module),
            sonst None — fällt zur PC-Leaderboard-Prüfung durch.
        """
        from utils.scoring.political_compass_handler import PoliticalCompassHandler

        if not existing_benchmarks or force:
            return None

        cached_res = existing_benchmarks.get((model, batch_asset_id))
        if cached_res is None:
            return None

        if not PoliticalCompassHandler.is_political_compass(benchmark_info):
            # Standardpfad für nicht-PC-Batch-Module: 3-CSV-Cache reicht als Beweis.
            logger.warning(
                f"⏩ Überspringe {benchmark_info.get('name', '')} "
                "(Batch-Modus; Bereits im Cache vorhanden)"
            )
            return [cached_res.copy()]

        # PC: Cache vorhanden, aber Leaderboard-Check unten ist maßgeblich.
        logger.debug(
            "PC-Cache-Treffer in 3-CSVs für %s — prüfe pc_leaderboard.csv als SSoT.",
            model,
        )
        return None

    def _check_pc_leaderboard_skip(self, model: str, benchmark_info: dict, force: bool) -> bool:
        """Prüft das autarke PC-Leaderboard (SSoT für Political-Compass-Cache)."""
        from pathlib import Path
        from utils.scoring.political_compass_handler import PoliticalCompassHandler

        if force or not PoliticalCompassHandler.is_political_compass(benchmark_info):
            return False

        # Fallback-Check: political_compass_leaderboard.csv direkt prüfen.
        # Die Standard-CSVs können nach einem Reset leer sein, während PC-Ergebnisse
        # autark im Leaderboard fortbestehen. Verhindert teure Re-Runs via `make political-compass`.
        import csv as _csv
        import re as _re_pc

        pc_leaderboard = Path("benchmark_scores/political_compass_leaderboard.csv")
        if not pc_leaderboard.exists():
            return False

        try:
            # save_leaderboard_csv() strips OpenRouter date suffixes:
            # -YYYYMMDD (8-digit) and -MMDD with valid months 01-12 (e.g. -0127).
            # Version suffixes like -2503 / -2411 are intentionally NOT stripped.
            # Normalize identically so the lookup matches dated config aliases.
            model_normalized = _re_pc.sub(r"-\d{8}$", "", model)
            model_normalized = _re_pc.sub(r"-(0[1-9]|1[0-2])\d{2}$", "", model_normalized)
            with pc_leaderboard.open("r", encoding="utf-8") as _f:
                pc_models = {row.get("model") for row in _csv.DictReader(_f)}
            if model in pc_models or model_normalized in pc_models:
                logger.warning(
                    f"⏩ Überspringe {benchmark_info.get('name', '')} "
                    f"(PC-Leaderboard; {model} bereits bewertet)"
                )
                return True
        except (OSError, _csv.Error):
            pass  # Bei Lesefehler: sicher durchlaufen und normal ausführen
        return False

    def _load_batch_test(self, benchmark_info: dict, model: str, provider: str):
        """Lädt die Batch-Test-Klasse und bereitet sie vor.

        Returns:
            Test-Instanz oder None bei Setup-Fehler.
        """
        from pathlib import Path
        from utils.module_loader import load_test_class

        module_path = Path(str(benchmark_info.get("module_path", "")))
        test_file = module_path / "test.py"
        test_class_name = str(benchmark_info.get("test_class", ""))

        if not test_class_name:
            import logging
            logging.getLogger(__name__).error(
                "Keine gültige Test-Klasse für %s definiert.", benchmark_info.get("name")
            )
            return None

        try:
            test_class_type = load_test_class(test_file, test_class_name)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(
                "Failed to load batch module %s: %s", benchmark_info.get("name"), e
            )
            return None

        logger.info(
            f"🛠️  Initialisiere Batch-Test: {benchmark_info.get('name')} ({provider}:{model})"
        )
        test = test_class_type()

        assets_dir = module_path / "assets"
        if not assets_dir.exists():
            logger.error(f"❌ Assets directory not found: {assets_dir}")
            return None

        if hasattr(test, "load_questions"):
            test.load_questions(str(assets_dir))

        if hasattr(test, "questions") and not test.questions:
            logger.error("❌ Keine Fragen geladen!")
            return None

        return test

    def _run_batch_test(
        self,
        test: Any,
        model: str,
        benchmark_info: dict,
        provider: str,
        num_runs: int,
        batch_asset_id: str,
    ) -> list:
        """Führt Batch-Test aus, prüft Fehler-Flags und baut das std_result."""
        import json

        min_runs = benchmark_info.get("min_runs", 1)
        test.num_runs = max(num_runs, min_runs)

        # Execution
        result_wrapper = test.execute(model=model, llm_client=self.client, provider=provider)

        # Propagate quota/budget exhaustion detected inside the module
        if getattr(test, "_quota_exhausted", False):
            logger.error("   💸 Budget-/Quota-Fehler in Batch-Modul erkannt. Provider wird als erschöpft markiert.")
            self.provider_quota_exhausted = True
            return []

        # Systematic failure: model refused/failed all questions in a block → skip this model
        if getattr(test, "_systematic_failure", False):
            logger.error(f"   ⚠️  Systematischer API-Fehler für {model} — Modell antwortet nicht. Überspringe.")
            return []

        try:
            report = json.loads(result_wrapper.raw_response)
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"❌ Batch Execution Failed: Invalid JSON response ({e})")
            return []

        return self._finalize_batch_result(
            test, result_wrapper, report, model, benchmark_info, provider, batch_asset_id,
        )

    def _finalize_batch_result(
        self,
        test: Any,
        result_wrapper: Any,
        report: dict,
        model: str,
        benchmark_info: dict,
        provider: str,
        batch_asset_id: str,
    ) -> list:
        """Verarbeitet Report (PC-Handler oder Summary-Log) und baut std_result."""
        from datetime import datetime
        from utils.model_utils import get_model_version
        from utils.scoring.political_compass_handler import PoliticalCompassHandler

        model_version = get_model_version(model, provider=provider, client=self.client)

        if PoliticalCompassHandler.is_political_compass(benchmark_info):
            PoliticalCompassHandler.handle_results(
                model=model,
                report=report,
                model_version=model_version,
                test_instance=test,
                audit_mode=getattr(self, "audit_mode", True),
                provider_type=provider
            )
        else:
            logger.info(f"\n📊 {benchmark_info.get('name', 'Batch Module')} Summary:")
            logger.info(f"Modell: {model}")
            logger.info(f"Score: {report.get('score', report.get('total_score', 0.0)):.2f}/100")
            logger.info(f"Erfolgsrate: {report.get('success_rate', 'N/A')}")
            if "badge" in report:
                logger.info(f"Badge: {report['badge']}\n")
        std_result = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": report.get("status", "success"),
            "provider": provider,
            "hardware_profile": get_hardware_profile(self.validator.config, provider),
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
