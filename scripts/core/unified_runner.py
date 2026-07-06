#!/usr/bin/env python3
"""Unified Benchmark Runner für lokale und kommerzielle Modelle."""

import csv
import hashlib
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

import requests
from utils.adaptive_pause import AdaptivePauseCalculator, BenchmarkMode
from utils.base_runner import BaseBenchmarkRunner
from utils.benchmark_utils import append_global_run_metrics, discover_assets, load_asset_yaml
from utils.card_utils import ensure_card
from utils.constants import (
    DEFAULT_MAX_SCORE,
    HTTP_OK,
    LLAMACPP_HEALTH_CHECK_TIMEOUT,
    LLAMACPP_PROBE_TIMEOUT,
    LLAMACPP_RESET_PAUSE_FALLBACK,
    LLAMACPP_RESET_PAUSE_HEAVY,
    LLAMACPP_RESET_PAUSE_MEDIUM,
    LLAMACPP_RESET_PAUSE_OK,
    MIN_REFUSAL_CHARS,
    MODEL_TYPE_OPEN_WEIGHTS_CLOUD,
    OLLAMA_DEFAULT_BASE_URL,
    OLLAMA_UNLOAD_SETTLE_SEC,
    TIMEOUT_DEFAULT,
    TIMEOUT_OLLAMA_LIST_FAST,
    TIMEOUT_OLLAMA_WARMUP,
    TRUNCATION_THRESHOLDS,
)
from utils.language_validator import LanguageValidator
from utils.logging_config import setup_logging
from utils.model_utils import (
    _find_card,
    _safe_name,
    get_model_identity,
    get_model_version,
    probe_thinking_model,
    resolve_canonical_model_id,
)
from utils.rate_limiter import RateLimiter
from utils.scoring.exceptions import JudgeUnavailableError
from utils.scoring.judge_evaluator import evaluate_with_judge, generate_audit_log
from utils.scoring_utils import calculate_score_contributions
import contextlib

setup_logging()
logger = logging.getLogger(__name__)
_language_validator = LanguageValidator()

# Budget-/Quota-Fehlermuster — Modul-Level-Konstante (kein Rebuild pro Exception)
_BUDGET_KEYWORDS: tuple[str, ...] = (
    "quota",
    "budget",
    "billing",
    "credit",
    "insufficient_funds",
    "payment",
    "402 payment required",
    "exceeded your current quota",
    "budget limit exceeded",
)


class UnifiedBenchmarkRunner(BaseBenchmarkRunner):
    """Führt Benchmarks systemübergreifend (Lokal & API) aus."""

    def __init__(
        self,
        force: bool = False,
        audit_mode: bool = True,
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
        self._probed_models: set[str] = set()  # Verhindert Doppel-Probes in einer Session
        self.existing_commercial_benchmarks = self._load_existing_benchmarks(
            self.commercial_csv
        )
        self.existing_cloud_benchmarks = self._load_existing_benchmarks(self.cloud_csv)
        self.existing_local_benchmarks = self._load_existing_benchmarks(self.local_csv)

    def _ensure_model_card(self, model: str, provider: str) -> str:
        """
        Card-First-Hook: stellt sicher, dass eine Model Card mit Thinking-Probe-Ergebnis
        vorhanden ist, bevor der erste Benchmark-Run startet.

        Delegiert an drei private Helfer: Card-Pfad bestimmen, Probe-Felder lesen,
        Probe-Felder schreiben. Returns canonical model_id.
        """
        if model in self._probed_models:
            return model

        card_path, _safe = self._resolve_model_card_path(model)
        needs_probe, card_loaded, canonical_model = self._read_card_probe_state(
            model, card_path
        )

        if not needs_probe:
            self._probed_models.add(model)
            return canonical_model

        probe = self._run_thinking_probe_or_skip(model, provider)
        if probe is None:
            # Probe übersprungen (Budget/Quota-Fehler)
            return canonical_model

        self._write_probe_to_card(model, card_path, probe, card_loaded)
        self._probed_models.add(model)
        return canonical_model

    def _resolve_model_card_path(self, model: str) -> tuple[Path, str]:
        """Ermittelt Card-Pfad via _find_card (mit glob-Fallback) oder Safe-Name."""
        cards_dir = Path("benchmark_scores/model_cards")
        found_path = _find_card(model)
        if found_path is not None and found_path.exists():
            card_path = found_path
            logger.debug("[Card-First] Card gefunden via _find_card: %s", card_path)
        else:
            safe = _safe_name(model)
            card_path = cards_dir / f"{safe}.json"
            logger.debug("[Card-First] Card nicht gefunden, verwende Fallback-Pfad: %s", card_path)
        return card_path, ""

    def _read_card_probe_state(
        self, model: str, card_path: Path
    ) -> tuple[bool, bool, str]:
        """Lädt Card-Inhalt. Returns (needs_probe, card_loaded, canonical_model)."""
        needs_probe = False
        card_loaded = False
        canonical_model = model

        if not card_path.exists():
            needs_probe = True
            print("   ⏳ Keine Card gefunden — starte Thinking-Probe...", flush=True)
            logger.info(
                "[Card-First] Keine Card für '%s' gefunden → wird nach Probe angelegt.",
                model,
            )
            return needs_probe, card_loaded, canonical_model

        try:
            loaded: dict[str, Any] = json.loads(card_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"   ⚠️ Card konnte nicht gelesen werden: {e}", flush=True)
            logger.warning(
                "[Card-First] Card für '%s' konnte nicht gelesen werden: %s", model, e,
            )
            return True, False, model

        card_loaded = True
        canonical_model = loaded.get("model_id") or model
        # Pitfall-Diagnose 2026-06-10: Draft-Cards aus ensure_card() haben
        # ``thinking_probe_detected: null`` (explizit auf None gesetzt), nicht
        # "Feld fehlt komplett". ``not in loaded`` würde das übersehen und
        # die Probe überspringen — die Folge war: Gemma-4-12B-Modelle
        # bekamen kein 5x-Reasoning-Budget, weil Probe nie lief.
        # Korrekter Check: Wert muss truthy sein (True ODER False) — nur
        # None/undefined triggert eine Probe.
        probe_state = loaded.get("thinking_probe_detected")
        if probe_state is None:
            needs_probe = True
            print("   ⏳ Card vorhanden, aber Thinking-Probe fehlt (null) — starte Erkennung...", flush=True)
            logger.info(
                "[Card-First] Card für '%s' hat kein Probe-Feld (Wert=%r) → Probe wird nachgeholt.",
                model, probe_state,
            )
        else:
            print(
                f"   ✓ Card gefunden mit thinking_probe_detected={loaded['thinking_probe_detected']}",
                flush=True,
            )
            logger.debug(
                "[Card-First] '%s' hat vollständige Card (probe_detected=%s). Kein Probe nötig.",
                model,
                loaded["thinking_probe_detected"],
            )
        if canonical_model != model:
            logger.info(
                "[Card-First] Alias '%s' → canonical '%s' (via card glob fallback).",
                model, canonical_model,
            )
        return needs_probe, card_loaded, canonical_model

    def _run_thinking_probe_or_skip(
        self, model: str, provider: str
    ) -> Any | None:
        """Führt die Thinking-Probe aus. Returns Probe-Objekt oder None (skip)."""
        print(f"🔍 Reasoning-Erkennung für '{model}' — sende Probe-Request...", flush=True)
        try:
            probe = probe_thinking_model(model, provider, self.validator.config)
        except RuntimeError as probe_err:
            err_str = str(probe_err)
            if "429" in err_str or "usage limit" in err_str or "rate limit" in err_str.lower():
                print("   ⚠️  Wochenlimit erschöpft — Reasoning-Erkennung übersprungen, Benchmark läuft weiter.")
            elif "403" in err_str or "subscription" in err_str.lower():
                print("   ⚠️  Subscription erforderlich — Reasoning-Erkennung übersprungen, Benchmark läuft weiter.")
            else:
                print("   ⚠️  Reasoning-Erkennung fehlgeschlagen — Benchmark läuft weiter.")
            logger.warning(
                "[Card-First] ThinkingProbe für '%s' übersprungen: %s", model, probe_err,
            )
            self._probed_models.add(model)
            return None
        print(
            f"   → detected={probe.detected} (confidence={probe.confidence})"
        )
        return probe

    def _write_probe_to_card(
        self,
        model: str,
        card_path: Path,
        probe: Any,
        card_loaded: bool,
    ) -> None:
        """Schreibt Probe-Felder (Detected, Evidence, Confidence, Timestamp + CoT-Quartett) in die Card."""
        from utils.model_utils import classify_cot_marker_family

        probe_fields: dict[str, Any] = {
            "thinking_probe_detected": probe.detected,
            "thinking_probe_evidence": probe.evidence,
            "thinking_probe_confidence": probe.confidence,
            "thinking_probe_at": datetime.now(UTC).isoformat(),
        }
        # v4.7.1 CoT-Quartett: Marker-Familie + Tag-Liste nur setzen, wenn
        # tatsaechlich Tags gefunden wurden. Sonst bleiben die Felder null
        # (verhindert noise im Web-Export).
        if getattr(probe, "tags_found", None):
            probe_fields["cot_marker_family"] = classify_cot_marker_family(probe.tags_found)
            probe_fields["cot_tags_detected"] = list(probe.tags_found)

        card_path = ensure_card(model, card_path=card_path if card_loaded else None)
        card_content: dict = json.loads(card_path.read_text(encoding="utf-8"))
        card_content.update(probe_fields)
        if probe.detected:
            tags: list = card_content.get("architecture_tags") or []
            if "Thinking" not in tags:
                card_content["architecture_tags"] = [
                    "Thinking",
                ] + [t for t in tags if t != "General"]
        card_path.write_text(
            json.dumps(card_content, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.info("[Card-First] Probe-Felder in Card für '%s' eingetragen.", model)

    def _load_existing_benchmarks(
        self, csv_path: Path
    ) -> dict[tuple[str, str], dict[str, Any]]:
        existing = {}
        if self.force or not csv_path.exists():
            return existing

        try:
            with open(csv_path, encoding="utf-8") as f:
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
                                    if row[num_field] not in (None, "", "nan"):
                                        logger.warning(
                                            "Cache row %s/%s: non-numeric %s=%r coerced to 0.0",
                                            model_id, asset_id, num_field, row[num_field],
                                        )
                                    row[num_field] = 0.0

                        existing[(model_id, asset_id)] = dict(row)
        except Exception as e:
            logger.warning("Fehler beim Laden bestehender Benchmarks %s: %s", csv_path, e)
        return existing

    def _get_existing(self, provider: str) -> dict:
        """Ermittelt das passende Cache-Dictionary basierend auf dem Provider."""
        if provider == "ollama":
            return self.existing_local_benchmarks

        provider_config = self.validator.config.get("providers", {}).get("commercial", {}).get(provider, {})
        if provider_config.get("model_type") == MODEL_TYPE_OPEN_WEIGHTS_CLOUD:
            return self.existing_cloud_benchmarks

        return self.existing_commercial_benchmarks

    def _get_existing_for_model(self, provider: str, model: str) -> dict:
        """Wie _get_existing(), aber beachtet auch :cloud-Suffix bei Ollama-Proxies."""
        if provider == "ollama":
            if ":cloud" in model.lower() or model.lower().endswith("-cloud"):
                return self.existing_cloud_benchmarks
            return self.existing_local_benchmarks

        provider_config = self.validator.config.get("providers", {}).get("commercial", {}).get(provider, {})
        if provider_config.get("model_type") == MODEL_TYPE_OPEN_WEIGHTS_CLOUD:
            return self.existing_cloud_benchmarks

        return self.existing_commercial_benchmarks

    def _measure_cold_start(self, model: str) -> dict[str, Any] | None:
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
                "max_score": DEFAULT_MAX_SCORE,
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

    def _create_error_result(
        self,
        asset_id: str,
        error_message: str,
        model: str = "",
        provider: str = "",
    ) -> dict[str, Any]:
        return {
            "status": "error",
            "error_message": error_message,
            "asset_id": asset_id,
            "asset_name": asset_id,
            "model": model,
            "provider": provider,
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
        benchmark_info: dict[str, Any],
        is_local: bool,
        pause_calculator: Any | None = None,
        run_limiter: Any | None = None,
    ) -> dict[str, Any]:
        asset_data = load_asset_yaml(asset_path)
        if not asset_data:
            return self._create_error_result(
                asset_path.stem,
                "Empty/Invalid Asset File",
                model=model,
                provider=provider,
            )

        asset_id = asset_data.get("metadata", {}).get("id", asset_path.stem)
        cached = self._check_cache_for_skip(model, provider, asset_id)
        if cached is not None:
            return cached

        if not is_local and run_limiter:
            run_limiter.wait_for_slot()

        server_error = self._ensure_llamacpp_server(model, provider, asset_id)
        if server_error is not None:
            return server_error

        exec_result, test_instance = self._execute_test_with_timing(
            model, asset_path, benchmark_info, provider
        )
        if exec_result is None:
            # Re-raised endpoint conflict; pass through
            return self._create_error_result(asset_path.stem, "endpoint conflict", model=model, provider=provider)
        if test_instance is None:
            return self._create_error_result(
                asset_path.stem, "Test execution failed", model=model, provider=provider,
            )

        response = exec_result.raw_response
        exec_result, score = self._score_with_language_check(
            test_instance, exec_result, asset_data, model
        )

        result = self._build_result_envelope(
            model, provider, asset_data, exec_result, is_local
        )
        if result.get("status") == "error":
            return result

        asset_cfg = self._resolve_asset_config(benchmark_info, asset_id)
        if asset_cfg:
            # Contributions auf Basis des Regex-Scores vorberechnen (result["percentage"]).
            # Bei Hybrid-Scoring überschreibt judge_evaluator.py diese Werte mit dem
            # finalen Hybrid-Score. Vorher: calculate_score_contributions(score, asset_cfg)
            # — das verwendete exec_result.data ohne "percentage" → immer 0.0.
            calculate_score_contributions(result, asset_cfg)

        if self._is_judge_applicable(benchmark_info):
            self._apply_judge_pipeline(
                result=result,
                response=response,
                asset_data=asset_data,
                benchmark_info=benchmark_info,
                model=model,
                provider=provider,
                is_local=is_local,
                pause_calculator=pause_calculator,
            )

        if getattr(self, "audit_mode", False):
            generate_audit_log(result, exec_result, asset_data, response, score)
        return result

    # -- Phase 3A: Helfer für _process_single_test -----------------------------------

    def _check_cache_for_skip(
        self, model: str, provider: str, asset_id: str
    ) -> dict[str, Any] | None:
        """Cache-Lookup: gibt cached row zurück wenn vorhanden, sonst None."""
        if self.force:
            return None
        key = (model, asset_id)
        existing_cache = self._get_existing_for_model(provider, model)
        if key not in existing_cache:
            return None
        print(f"   ⏭️  [{asset_id}] Wird übersprungen (Cache)")
        cached = existing_cache[key]
        cached["cached"] = True
        return cached

    def _ensure_llamacpp_server(
        self, model: str, provider: str, asset_id: str
    ) -> dict[str, Any] | None:
        """Stellt sicher, dass llama.cpp/vLLM-Server läuft. Returns Error-Result oder None.

        Behandelt ``llamacpp``, ``llamacpp_spark`` und ``vllm_spark`` — alle drei
        sind OpenAI-kompatible lokale Server, deren Lifecycle über die jeweilige
        ``start_server(model)``-Methode im Provider-Client abgewickelt wird.
        """
        if provider not in ("llamacpp", "llamacpp_spark", "vllm_spark"):
            return None
        try:
            client = self.client.clients.get(provider)
            if client is None:
                logger.error("Provider '%s' nicht im LLMClient-Registry.", provider)
                return self._create_error_result(
                    asset_id,
                    f"Provider '{provider}' nicht im LLMClient-Registry",
                    model=model, provider=provider,
                )
            started = client.start_server(model)
            if not started:
                logger.error(
                    "Server (%s) konnte nicht für Modell '%s' gestartet werden.",
                    provider, model,
                )
                return self._create_error_result(
                    asset_id,
                    f"Server ({provider}) Start fehlgeschlagen für Modell '{model}' — Server-Log prüfen",
                    model=model, provider=provider,
                )
        except Exception as _e:
            logger.error("start_server für Modell '%s' fehlgeschlagen: %s", model, _e)
            return self._create_error_result(
                asset_id, f"start_server Exception: {_e}",
                model=model, provider=provider,
            )
        return None

    def _execute_test_with_timing(
        self, model: str, asset_path: Path, benchmark_info: dict[str, Any], provider: str
    ) -> tuple[Any, Any] | tuple[None, None]:
        """Führt das Test-Modul aus und misst die Zeit. Returns (exec_result, test_instance) oder (None, None) bei Endpoint-Konflikt."""
        start_time = time.time()
        try:
            test_instance, exec_result = self.execute_test_module(
                model, asset_path, benchmark_info, provider=provider,
            )
            # Heartbeat-Referenz in den Test injizieren — damit Refusal-Retries
            # (politische Compass) den Live-Heartbeat im Terminal aktualisieren können.
            # Greift nur, wenn der Test das Attribut nutzt (graceful no-op sonst).
            if test_instance is not None:
                test_instance._benchmark_runner = self
            if not getattr(exec_result, "execution_time", None):
                exec_result.execution_time = time.time() - start_time
        except Exception as e:
            if "endpoint conflict or startup failure" in str(e).lower():
                raise
            return self._create_error_result(
                asset_path.stem, str(e), model=model, provider=provider,
            ), None
        return exec_result, test_instance

    def _score_with_language_check(
        self,
        test_instance: Any,
        exec_result: Any,
        asset_data: dict[str, Any],
        model: str,
    ) -> tuple[Any, dict[str, Any]]:
        """Score-Berechnung + Language-Mismatch-Detection. Returns (exec_result, score)."""
        response = exec_result.raw_response
        exec_result = test_instance.score_response(exec_result)
        score = exec_result.data

        expected_lang = asset_data.get("metadata", {}).get("language", "")
        mismatch = _language_validator.detect_mismatch(response, expected_lang)
        if mismatch:
            de_count = mismatch["de_marker_count"]
            en_count = mismatch["en_marker_count"]
            exec_result.data["language_mismatch"] = True
            exec_result.data["detected_language"] = mismatch["detected_language"]
            exec_result.data["violations"] = exec_result.data.get("violations", []) + [
                "Wrong Language (English instead of German)"
            ]
            if isinstance(exec_result.data.get("details"), list):
                exec_result.data["details"].append(
                    "> [!WARNING]\n"
                    "> **[LANGUAGE MISMATCH]** The model responded in English, but the task requires German (`expected_language: de`). "
                    f"Language marker counts: DE={de_count}, EN={en_count}."
                )
            score = exec_result.data
            logger.warning(
                "Language mismatch detected for %s / %s: EN response on DE task",
                model, asset_data.get("metadata", {}).get("id"),
            )
        return exec_result, score

    def _build_result_envelope(
        self,
        model: str,
        provider: str,
        asset_data: dict[str, Any],
        exec_result: Any,
        is_local: bool,
    ) -> dict[str, Any]:
        """Baut das Basis-Result-Dict + Tokens + Cost + Language-Mismatch-Mapping."""
        result = self.build_base_result(model, asset_data, exec_result, provider)
        result["model_version"] = getattr(
            self, "current_model_version", get_model_version(model, provider=provider),
        )
        if exec_result.data.get("language_mismatch"):
            result["language_mismatch"] = True
            result["status"] = "language_mismatch"

        # Token usage: bevorzuge exec_result.tokens_used (z. B. tooluse: 2 LLM-Calls)
        _module_tokens: int = exec_result.tokens_used or 0
        _raw_client_tokens = getattr(self.client, "last_token_usage", 0)
        _client_tokens: int = _raw_client_tokens if isinstance(_raw_client_tokens, int) else 0
        result["tokens_used"] = (
            _module_tokens if _module_tokens > _client_tokens else _client_tokens
        )
        if not is_local:
            _module_cost: float = exec_result.cost_usd or 0.0
            _raw_client_cost = getattr(self.client, "last_request_cost", 0.0)
            _client_cost: float = (
                _raw_client_cost if isinstance(_raw_client_cost, (int, float)) else 0.0
            )
            result["cost_usd"] = _module_cost if _module_cost > _client_cost else _client_cost
        else:
            result["cost_usd"] = 0.0

        # Tooluse-spezifische Metriken als flache CSV-Spalten persistieren.
        # Duck Typing über "p1_score" in exec_result.data (nur das Tooluse-Modul setzt dieses Feld).
        # Ermöglicht ToolUseExporter._aggregate_asset_rows() P1/P2 und Timing-Daten
        # aus der main CSV zu lesen, auch ohne score_contributions.
        _tu_data = exec_result.data
        if "p1_score" in _tu_data:
            _TOOLUSE_FLAT = (
                "p1_score", "p2_score", "combined_score", "mcp_mode",
                "tool_call_valid", "tool_call_attempts", "mcp_latency_s",
                "call1_time_s", "call2_time_s", "total_time_s",
                "call1_tokens", "call2_tokens", "hallucination_flag",
            )
            for _k in _TOOLUSE_FLAT:
                if _k in _tu_data and _k not in result:
                    result[_k] = _tu_data[_k]

        return result

    def _resolve_asset_config(
        self, benchmark_info: dict[str, Any], asset_id: str
    ) -> dict[str, Any] | None:
        """Sucht die Asset-Konfiguration in benchmark_info.benchmarks."""
        benchmarks_list = benchmark_info.get("benchmarks", [])
        return next((b for b in benchmarks_list if b["id"] == asset_id), None)

    def _is_judge_applicable(self, benchmark_info: dict[str, Any]) -> bool:
        """Prüft ob der Judge für dieses Modul aktiviert ist."""
        judge_cfg_dict = self.validator.config.get("llm_judge", {})
        if not judge_cfg_dict.get("enabled", True):
            return False
        applicable = judge_cfg_dict.get("applicable_modules") or []
        return benchmark_info.get("id", "") in applicable

    def _apply_judge_pipeline(
        self,
        result: dict[str, Any],
        response: str,
        asset_data: dict[str, Any],
        benchmark_info: dict[str, Any],
        model: str,
        provider: str,
        is_local: bool,
        pause_calculator: Any | None,
    ) -> dict[str, Any]:
        """Führt die Judge-Pipeline aus: Pause, Memory-Reset, Judge-Call.

        Reasoning-Modelle (GLM-5.x, Claude Extended Thinking, o-Series, etc.) geben
        ihre Antwort teils im separaten ``reasoning``-Feld zurück statt im
        ``content``-Feld. Wenn ``content`` kurz/leer ist aber ``think_content``
        substantiell ist, wird ``think_content`` als effektive Antwort für den
        Judge verwendet — sonst würde ein valides Reasoning-Modell fälschlich
        als Safety-Refusal markiert.
        """
        think_content = result.get("think_content") or ""
        effective_response = response
        resp_too_short = len(response.strip()) < MIN_REFUSAL_CHARS
        think_substantial = len(think_content.strip()) >= MIN_REFUSAL_CHARS
        if resp_too_short and think_substantial:
            result["reasoning_only_response"] = True
            effective_response = think_content

        if len(effective_response.strip()) < MIN_REFUSAL_CHARS:
            result["judge_progress_status"] = "⚠️ Judge: skip (zu kurz/abgelehnt)"
            result["refusal_flag"] = True
            result["refusal_type"] = "content_safety"
            result["refusal_note"] = (
                f"Response too short (<{MIN_REFUSAL_CHARS} chars) — likely a safety refusal or empty API response."
            )
            return result

        self._judge_pre_pause(
            is_local, pause_calculator, result, provider, model,
        )
        self._local_memory_reset(is_local, provider, model)

        asset_id = asset_data.get("metadata", {}).get("id", "")
        asset_cfg = self._resolve_asset_config(benchmark_info, asset_id)
        judge_cfg_dict = self.validator.config.get("llm_judge", {})

        return evaluate_with_judge(
            result=result,
            response=effective_response,
            asset_data=asset_data,
            judge_cfg_dict=judge_cfg_dict,
            eval_module_id=benchmark_info.get("id", ""),
            model=model,
            asset_cfg=asset_cfg,
            benchmark_info=benchmark_info,
        )

    def _judge_pre_pause(
        self,
        is_local: bool,
        pause_calculator: Any | None,
        result: dict[str, Any],
        provider: str,
        model: str,
    ) -> None:
        """Adaptive Pause + Ollama-Unload vor dem Judge-Aufruf."""
        if is_local and pause_calculator:
            pause_calculator.wait({
                "execution_time": result.get("execution_time", 0),
                "response_length": result.get("tokens_used", 0) * 4,
            })
        if is_local and provider == "ollama":
            with contextlib.suppress(Exception):
                requests.post(
                    f"{OLLAMA_DEFAULT_BASE_URL}/api/generate",
                    json={"model": model, "keep_alive": 0},
                    timeout=TIMEOUT_OLLAMA_LIST_FAST,
                )
            time.sleep(OLLAMA_UNLOAD_SETTLE_SEC)

    def _local_memory_reset(self, is_local: bool, provider: str, model: str) -> None:
        """llama.cpp Memory-Reset (Health-Check + Probe-Chat) zwischen Tests."""
        if not (is_local and provider in ("llamacpp", "llamacpp_spark")):
            return
        try:
            base_root = self._resolve_llamacpp_base_url(provider)
            self._probe_llamacpp_server(base_root, model, current_model=model)
        except Exception as e:
            logger.debug("llama.cpp Memory Reset exception (ignored): %s", e)
            time.sleep(LLAMACPP_RESET_PAUSE_OK)

    def _resolve_llamacpp_base_url(self, provider: str) -> str:
        """Ermittelt die llama.cpp Base-URL aus der Config."""
        server_key = provider if provider in ("llamacpp", "llamacpp_spark") else "llamacpp"
        server_cfg = self.validator.config.get(
            "providers", {}
        ).get("local", {}).get(server_key, {})
        base_url_raw = server_cfg.get("base_url") or server_cfg.get(
            "server_base_url", "http://127.0.0.1:8080",
        )
        return base_url_raw.rstrip("/").removesuffix("/v1")

    def _probe_llamacpp_server(
        self, base_root: str, model: str, current_model: str = ""
    ) -> None:
        """Health-Check + Probe-Chat: passt Pausen an Server-Readiness an.

        Args:
            base_root: Base-URL des llama.cpp-Servers (ohne /v1).
            model: Legacy-Parameter (wird nicht mehr verwendet).
            current_model: Das aktuell getestete Modell — wird als Probe-Model
                gesendet. Fallback: erstes Modell aus llamacpp-Config-Block.
        """
        try:
            health = requests.get(f"{base_root}/health", timeout=LLAMACPP_HEALTH_CHECK_TIMEOUT)
            healthy = health.status_code == HTTP_OK
        except Exception:
            healthy = False

        if not healthy:
            logger.warning(
                "llama.cpp Memory Reset: Server nicht erreichbar — längere Pause (%ds)",
                LLAMACPP_RESET_PAUSE_HEAVY,
            )
            time.sleep(LLAMACPP_RESET_PAUSE_HEAVY)
            return

        chat_url = f"{base_root}/v1/chat/completions"
        # current_model wird vom Caller (z. B. _local_memory_reset) mit dem
        # aktuell laufenden Modell befüllt. Fallback: erstes Modell aus Config.
        _probe_model = (
            current_model or
            self.validator.config.get("providers", {}).get("local", {})
            .get("llamacpp", {}).get("models", [{}])[0].get("id", "")
        )
        try:
            _probe_payload = json.dumps({
                "model": _probe_model,
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 4,
                "temperature": 0.0,
            })
            _probe_resp = requests.post(
                chat_url,
                data=_probe_payload.encode("utf-8"),
                headers={"Content-Type": "application/json"},
                timeout=LLAMACPP_PROBE_TIMEOUT,
            )
            if _probe_resp.status_code != HTTP_OK:
                logger.warning(
                    "llama.cpp Memory Reset: Probe-Chat fehlgeschlagen "
                    "(Status %d) — längere Pause (%ds)",
                    _probe_resp.status_code, LLAMACPP_RESET_PAUSE_MEDIUM,
                )
                time.sleep(LLAMACPP_RESET_PAUSE_MEDIUM)
            else:
                logger.debug("llama.cpp Memory Reset: Probe-Chat OK")
                time.sleep(LLAMACPP_RESET_PAUSE_OK)
        except requests.exceptions.Timeout:
            logger.warning(
                "llama.cpp Memory Reset: Probe-Chat timeout — längere Pause (%ds)",
                LLAMACPP_RESET_PAUSE_HEAVY,
            )
            time.sleep(LLAMACPP_RESET_PAUSE_HEAVY)
        except Exception as probe_err:
            logger.debug("llama.cpp Memory Reset: Probe-Chat fehlgeschlagen (ignored): %s", probe_err)
            time.sleep(LLAMACPP_RESET_PAUSE_FALLBACK)

    def run_benchmark(
        self,
        provider: str,
        model: str,
        benchmark_info: dict[str, Any],
        num_runs: int = 1,
        assets: list[Path] | None = None,
    ) -> list[dict[str, Any]]:
        is_local = provider in self._local_provider_names()

        try:
            batch_result = self._run_batch_mode_if_applicable(
                provider, model, benchmark_info, num_runs,
            )
            if batch_result is not None:
                return batch_result

            model = self._canonicalize_and_probe(model, provider)
            self._print_run_header(provider, model, benchmark_info)
            self.current_model_version = get_model_version(model, provider=provider)

            assets = self._resolve_assets(benchmark_info, assets)
            run_id = self._generate_run_id(model, assets)
            results = self._collect_warmup_result(model, provider)

            if not assets:
                print("⚠️  Keine Tests gefunden.")
                return results

            pause_calculator, run_limiter = self._build_rate_limiters(
                provider, model, is_local,
            )

            self._run_asset_loop(
                assets=assets,
                model=model,
                provider=provider,
                benchmark_info=benchmark_info,
                is_local=is_local,
                run_id=run_id,
                pause_calculator=pause_calculator,
                run_limiter=run_limiter,
                results=results,
            )

            self._print_terminal_summary(results)
            self._record_global_metrics(model, results, benchmark_info)
            return results
        finally:
            self._cleanup_local_provider(provider)

    # -- Phase 3C: Helfer für run_benchmark -----------------------------------------

    @staticmethod
    def _local_provider_names() -> tuple[str, ...]:
        return (
            "ollama",
            "llamacpp",
            "llamacpp_spark",
            "llama_cpp",
            "llamacpp_local",
            "vllm_spark",
        )

    def _run_batch_mode_if_applicable(
        self,
        provider: str,
        model: str,
        benchmark_info: dict[str, Any],
        num_runs: int,
    ) -> list[dict[str, Any]] | None:
        """Delegiert an execute_batch_module, falls batch-Mode konfiguriert."""
        if benchmark_info.get("execution_mode") != "batch":
            return None
        # SSoT: Kanonische ID bestimmen, bevor der Batch-Modus auf den
        # model-Parameter zugreift (z. B. existing_benchmarks-Cache-Lookup).
        canonical_model = resolve_canonical_model_id(model)
        return self.execute_batch_module(
            model=canonical_model,
            benchmark_info=benchmark_info,
            provider=provider,
            num_runs=num_runs,
            force=self.force,
            existing_benchmarks=self._get_existing_for_model(provider, canonical_model),
        )

    def _canonicalize_and_probe(self, model: str, provider: str) -> str:
        """SSoT-Canonical + Card-First-Probe. Returns kanonisierte model_id."""
        original_model = model
        model = resolve_canonical_model_id(model)
        if model != original_model:
            logger.info(
                "[SSoT] model_id kanonisiert: '%s' → '%s'", original_model, model,
            )
        return self._ensure_model_card(model, provider)

    def _print_run_header(
        self, provider: str, model: str, benchmark_info: dict[str, Any]
    ) -> None:
        """Header + Identity-Print für einen Benchmark-Lauf."""
        print(
            f"\n{'=' * 60}\n📊 STARTE BENCHMARK: {benchmark_info.get('name', 'Unknown')}\n{'=' * 60}"
        )
        identity = get_model_identity(model)
        tags_str = ", ".join(identity["tags"])
        print(f"Provider: {provider}\nModell:   {model} (Tags: [{tags_str}])")

    def _resolve_assets(
        self, benchmark_info: dict[str, Any], assets: list[Path] | None
    ) -> list[Path]:
        """Assets-Discovery mit Fallback auf benchmark_info.path."""
        if assets is None:
            assets = discover_assets(benchmark_info["path"])
        print(f"Tests:    {len(assets)}\n{'=' * 60}\n")
        return assets

    def _generate_run_id(self, model: str, assets: list[Path]) -> str:
        """Deterministischer run_id (Baseline-Lock) — md5(model+tasks+timestamp)."""
        run_timestamp = str(int(time.time()))
        tasks_str = ",".join([a.name for a in assets])
        run_id_str = f"{model}_{tasks_str}_{run_timestamp}"
        return hashlib.md5(run_id_str.encode()).hexdigest()[:12]

    def _collect_warmup_result(self, model: str, provider: str) -> list[dict[str, Any]]:
        """Cold-Start Probe für Ollama, in results-Liste eingebettet."""
        results: list[dict[str, Any]] = []
        if provider != "ollama":
            return results
        warmup_result = self._measure_cold_start(model)
        if warmup_result:
            warmup_result["model_version"] = self.current_model_version
            results.append(warmup_result)
        return results

    def _build_rate_limiters(
        self, provider: str, model: str, is_local: bool
    ) -> tuple[AdaptivePauseCalculator | None, RateLimiter | None]:
        """Adaptive Pause (lokal) + Rate-Limiter (kommerziell, Free-Tier-aware)."""
        pause_calculator = (
            AdaptivePauseCalculator(model, self.mode) if is_local else None
        )
        # Free-tier OpenRouter models (model-id ends with ":free") nutzen ein
        # konservativeres Profil (18 RPM / 200 RPD).
        _limiter_key = (
            "openrouter_free"
            if (provider == "openrouter" and model.endswith(":free"))
            else provider
        )
        run_limiter = RateLimiter(_limiter_key) if not is_local else None
        return pause_calculator, run_limiter

    def _get_heartbeat_config(self) -> tuple[bool, float]:
        """Liest heartbeat-Konfiguration aus benchmark_config.yaml.

        Returns:
            (enabled, interval_seconds)
            - enabled: True wenn Heartbeat aktiv (Default: True)
            - interval_seconds: Sekunden zwischen Status-Prints (Default: 60.0)

        Robustheit:
        - Block fehlt komplett → (True, 60.0) — backwards-compatible
        - interval_seconds <= 0, nicht-numerisch oder None → Fallback 60.0
        - Fehler werden nicht geworfen, da Heartbeat ein nice-to-have ist.
        """
        cfg = self.validator.config.get("heartbeat", {}) or {}
        if not isinstance(cfg, dict):
            return True, 60.0

        enabled = bool(cfg.get("enabled", True))

        raw_interval = cfg.get("interval_seconds", 60.0)
        try:
            interval = float(raw_interval)
        except (TypeError, ValueError):
            interval = 60.0
        if interval <= 0:
            interval = 60.0

        return enabled, interval

    def _run_asset_loop(
        self,
        *,
        assets: list[Path],
        model: str,
        provider: str,
        benchmark_info: dict[str, Any],
        is_local: bool,
        run_id: str,
        pause_calculator: Any | None,
        run_limiter: Any | None,
        results: list[dict[str, Any]],
    ) -> None:
        """Iteriert über Assets, ruft _process_single_test, sammelt Results.

        Startet einen Heartbeat-Thread (Daemon), der konfigurierbar oft den
        aktuellen Fortschritt + Phase + letzte Aktivität ins Terminal printet.
        Damit sieht der Beobachter bei langen Benchmarks (z.B. 397B-Modelle mit
        Refusal-Retries), ob der Prozess noch arbeitet oder hängt.

        Konfiguration: benchmark_config.yaml → heartbeat.interval_seconds
        (Default 60s; höhere Werte schonen das Terminal bei langen Läufen).
        heartbeat.enabled=false deaktiviert den Thread komplett.
        """
        import threading

        # Heartbeat-State initialisieren (vom politischen Compass-Test via
        # self._heartbeat_* lesbar — siehe _handle_heartbeat_signal).
        self._heartbeat_stop = threading.Event()
        self._heartbeat_start = time.time()
        self._heartbeat_last_activity = time.time()
        self._heartbeat_phase = "Setup"
        self._heartbeat_q_id = ""
        self._heartbeat_retry = ""
        self._heartbeat_completed = 0
        self._heartbeat_total = len(assets)

        heartbeat_enabled, heartbeat_interval = self._get_heartbeat_config()

        def _heartbeat_loop() -> None:
            """Print alle heartbeat_interval-Sekunden Fortschritt.
            Stop-Event terminiert sofort.
            """
            while not self._heartbeat_stop.is_set():
                # wait() returnt True wenn Event gesetzt, sonst False nach Timeout
                stopped = self._heartbeat_stop.wait(timeout=heartbeat_interval)
                if stopped:
                    break
                elapsed = time.time() - self._heartbeat_start
                hours, remainder = divmod(int(elapsed), 3600)
                minutes, seconds = divmod(remainder, 60)
                last_act = int(time.time() - self._heartbeat_last_activity)
                retry_str = f" | {self._heartbeat_retry}" if self._heartbeat_retry else ""
                phase_str = f" | {self._heartbeat_phase}: {self._heartbeat_q_id}{retry_str}" if self._heartbeat_q_id else f" | {self._heartbeat_phase}"
                print(
                    f"   💓 ⏱ {hours:02d}:{minutes:02d}:{seconds:02d} elapsed | "
                    f"{self._heartbeat_completed}/{self._heartbeat_total}{phase_str} | "
                    f"Letzte Aktivität: {last_act}s her",
                    flush=True,
                )

        heartbeat_thread = threading.Thread(target=_heartbeat_loop, daemon=True)
        if heartbeat_enabled:
            heartbeat_thread.start()
        else:
            # Deaktivierter Heartbeat: Event bleibt gesetzt, damit ggf. join() im
            # finally-Block sauber durchläuft ohne dass der Thread je lief.
            self._heartbeat_stop.set()
            heartbeat_thread = None  # Sentinel: im finally prüfen

        try:
            for i, asset_path in enumerate(assets, 1):
                asset_name = asset_path.stem.replace("asset_", "").replace("_", " ").title()
                self._heartbeat_q_id = asset_name
                self._heartbeat_phase = f"Test {i}/{len(assets)}"
                self._heartbeat_retry = ""
                self._heartbeat_last_activity = time.time()
                print(
                    f"   ⏳ [{i}/{len(assets)}] {asset_name}: Test läuft...",
                    end="\r", flush=True,
                )
                try:
                    self._handle_single_asset(
                        asset_path=asset_path,
                        i=i,
                        total=len(assets),
                        asset_name=asset_name,
                        model=model,
                        provider=provider,
                        benchmark_info=benchmark_info,
                        is_local=is_local,
                        run_id=run_id,
                        pause_calculator=pause_calculator,
                        run_limiter=run_limiter,
                        results=results,
                    )
                    self._heartbeat_completed += 1
                except JudgeUnavailableError as e:
                    print(f"\n⛔ JUDGE UNAVAILABLE (API Error / Budget Limit): {e}\nBeende den Benchmark vorzeitig, um inkonsistente Scores zu vermeiden.")
                    self._save_partial_results(results, is_local)
                    sys.exit(1)
                except KeyboardInterrupt:
                    print("\n⚠️  Benchmark vom Benutzer abgebrochen.")
                    self._save_partial_results(results, is_local)
                    sys.exit(1)
                except Exception as e:
                    if "endpoint conflict or startup failure" in str(e).lower():
                        print("\n⛔ Endpoint-Konflikt erkannt. Breche Modullauf ab, um fehlerhafte 0%-Einträge zu vermeiden.")
                        self._save_partial_results(results, is_local)
                        raise
                    self._handle_asset_exception(e, i, len(assets), asset_name)
        finally:
            # Heartbeat stoppen + ggf. noch laufende Print-Zeile clearen
            self._heartbeat_stop.set()
            if heartbeat_thread is not None:
                heartbeat_thread.join(timeout=2.0)
            print(" " * 120, end="\r", flush=True)

    def _handle_heartbeat_signal(
        self, q_id: str = "", retry_info: str = "", is_retry: bool = False
    ) -> None:
        """Wird vom Test (z.B. political_compass) aufgerufen, um Refusal-Retries
        im Heartbeat sichtbar zu machen.

        Args:
            q_id: Question-ID (z.B. ``political_compass_7.3.001``)
            retry_info: Retry-Beschreibung (z.B. ``Retry 1/2 temp 0.4``)
            is_retry: True wenn gerade ein Retry läuft, False wenn Retry abgeschlossen
        """
        if q_id:
            self._heartbeat_q_id = q_id
        if retry_info:
            self._heartbeat_retry = retry_info
        self._heartbeat_last_activity = time.time()
        # Heartbeat-Phase auf "Retry-Pass" setzen, falls Retry aktiv
        if is_retry:
            self._heartbeat_phase = "Retry"
        else:
            self._heartbeat_phase = "Test"

    def _handle_single_asset(
        self,
        *,
        asset_path: Path,
        i: int,
        total: int,
        asset_name: str,
        model: str,
        provider: str,
        benchmark_info: dict[str, Any],
        is_local: bool,
        run_id: str,
        pause_calculator: Any | None,
        run_limiter: Any | None,
        results: list[dict[str, Any]],
    ) -> None:
        """Führt einen einzelnen Asset-Test aus, klassifiziert + printed das Result."""
        result = self._process_single_test(
            model=model, provider=provider, asset_path=asset_path,
            benchmark_info=benchmark_info, is_local=is_local,
            pause_calculator=pause_calculator, run_limiter=run_limiter,
        )
        result["run_id"] = run_id

        result = self._apply_response_classification(result, benchmark_info, asset_path)
        self._print_asset_status(i, total, asset_name, result)

        if result:
            results.append(result)
            # Write-Through: Jedes Ergebnis SOFORT in die CSV schreiben,
            # bevor der nächste Task startet. Verhindert Datenverlust bei
            # Crash, Kill oder Timeout zwischen Tasks.
            try:
                self.save_results([result])
            except Exception as flush_exc:  # noqa: BLE001
                logger.warning("Write-Through nach Task %s fehlgeschlagen: %s", asset_name, flush_exc)
                print(f"   ⚠️ Write-Through fehlgeschlagen ({asset_name}): {flush_exc}")

    def _apply_response_classification(
        self, result: dict[str, Any], benchmark_info: dict[str, Any], asset_path: Path
    ) -> dict[str, Any]:
        """Safety/Truncation/Verbose-Overflow → Status-Anpassungen."""
        # Safety-Block-Check: finish_reason=SAFETY → refusal_flag, nicht truncated
        if result.get("finish_reason") == "SAFETY" and result.get("status") == "success":
            result["status"] = "refusal"
            result["refusal_flag"] = True
            result["refusal_type"] = "content_safety"
            result["refusal_note"] = "Response blocked by Gemini safety filters."

        result = self._check_truncation(result, benchmark_info)
        result = self._check_verbose_overflow(result, asset_path)
        return result

    def _check_truncation(
        self, result: dict[str, Any], benchmark_info: dict[str, Any]
    ) -> dict[str, Any]:
        """Per-Modul-Truncation-Schwelle (TRUNCATION_THRESHOLDS)."""
        module_id = benchmark_info.get("id", "")
        threshold = TRUNCATION_THRESHOLDS.get(module_id)
        if not threshold or result.get("status") != "success":
            return result
        response_len = self._extract_response_length(result)
        if 0 < response_len < threshold:
            result["status"] = "truncated"
            result["truncation_note"] = (
                f"Response below {threshold} chars for {module_id}"
            )
            print(f"\n   ⚠️ Result marked as truncated (length: {response_len} < {threshold})")
        return result

    def _check_verbose_overflow(
        self, result: dict[str, Any], asset_path: Path
    ) -> dict[str, Any]:
        """Per-Asset max_expected_length Constraint."""
        _asset_data = load_asset_yaml(asset_path)
        _max_expected = _asset_data.get("constraints", {}).get("max_expected_length")
        if not _max_expected or result.get("status") != "success":
            return result
        _overflow_len = self._extract_response_length(result)
        if _overflow_len and _overflow_len > _max_expected:
            result["status"] = "verbose_outlier"
            result["truncation_note"] = (
                f"Response {_overflow_len} chars exceeds expected max {_max_expected}"
            )
            print(f"\n   ⚠️ Result marked as verbose_outlier ({_overflow_len} > {_max_expected})")
        return result

    @staticmethod
    def _extract_response_length(result: dict[str, Any]) -> int:
        """Robuster Length-Extractor: top-level, metadata, str-Konvertierung."""
        response_len = result.get("response_length")
        if response_len is None:
            response_len = result.get("metadata", {}).get("response_length", 0)
        if isinstance(response_len, str):
            try:
                return int(response_len)
            except (ValueError, TypeError):
                return 0
        return response_len

    @staticmethod
    def _print_asset_status(i: int, total: int, asset_name: str, result: dict[str, Any]) -> None:
        """Printet Status-Icon + Score-Zeile für ein einzelnes Asset.

        Status-Icons:
            ✓  — Erfolg (oder non-error Sub-Status wie language_mismatch, truncated)
            ❌ — Error (API-Fehler, Server-Crash)
            🔁 — Refusal (Retry war erfolgreich nach 1-2 Versuchen)
            ⛔ — Hard Refusal (alle Retries erschöpft, keine Antwort erhalten)
        """
        status = result.get("status", "success")
        if status == "error":
            status_icon = "❌"
        elif status == "refusal" or result.get("refusal_flag") is True:
            # Erfolgreicher Retry: Modell hat nach Refusal doch geantwortet
            status_icon = "🔁"
        elif status == "hard_refusal" or result.get("hard_refusal") is True:
            # Alle Retries erschöpft — Frage blieb unbeantwortet
            status_icon = "⛔"
        else:
            status_icon = "✓"
        token_str = f"{result.get('tokens_used', 0)} T"
        judge_str = (
            f" | {result.get('judge_progress_status', '')}"
            if result.get("judge_progress_status")
            else ""
        )
        # Optional: Retry-Counter anzeigen, wenn Retries stattgefunden haben
        retry_count = result.get("refusal_retry_count", 0)
        retry_str = f" (×{retry_count})" if retry_count and retry_count > 0 else ""
        print(" " * 80, end="\r")
        print(
            f"   {status_icon} [{i}/{total}] {asset_name}: {result.get('percentage', 0):.1f}% | {token_str} | {result.get('execution_time', 0):.1f}s{retry_str}{judge_str}"
        )

    def _handle_asset_exception(
        self, exc: Exception, i: int, total: int, asset_name: str,
    ) -> None:
        """Behandelt per-Asset-Fehler (Budget-Keyword-Detection, Exhausted-Flag)."""
        print(" " * 80, end="\r")
        print(f"   ❌ [{i}/{total}] {asset_name}: Abgebrochen - {exc}")
        if any(kw in str(exc).lower() for kw in _BUDGET_KEYWORDS):
            print("   💸 Budget-/Quota-Fehler erkannt für Provider. Setze Exhausted-Flag.")
            self.provider_quota_exhausted = True

    def _print_terminal_summary(self, results: list[dict[str, Any]]) -> None:
        """Durchschnitts-Stats (Score, T/s, Judge, Cost) als Terminal-Summary."""
        valid_results = [
            r for r in results
            if r.get("type") != "system"
            and r.get("status") != "error"
            and r.get("skip_reason") is None
        ]
        if not valid_results:
            return
        _pcts = [r.get("percentage") for r in valid_results]
        logger.debug(
            "DURCHSCHNITT DEBUG: valid_results=%d, pcts=%s",
            len(valid_results), _pcts,
        )
        avg_score = sum(
            float(p) if p is not None else 0.0 for p in _pcts
        ) / len(valid_results)
        avg_time = sum(
            r.get("execution_time", 0.0) for r in valid_results
        ) / len(valid_results)

        token_rates = [
            float(r.get("tokens_per_second", 0.0))
            for r in valid_results
            if isinstance(r.get("tokens_per_second"), (int, float))
            or (
                isinstance(r.get("tokens_per_second"), str)
                and str(r.get("tokens_per_second")).replace(".", "", 1).isdigit()
            )
        ]
        avg_tokens = sum(token_rates) / len(token_rates) if token_rates else 0.0
        judge_scores = [
            float(r.get("llm_judge_score")) for r in valid_results
            if r.get("llm_judge_score") is not None
        ]
        total_usd = sum(r.get("cost_usd", 0.0) for r in valid_results)
        avg_usd = total_usd / len(valid_results)

        summary = "\n   " + "=" * 70 + "\n"
        summary += f"   🏁 DURCHSCHNITT: {avg_score:.1f}% | {avg_tokens:.0f} T/s | {avg_time:.1f}s"
        if judge_scores:
            avg_judge = sum(judge_scores) / len(judge_scores)
            summary += f" | ⚖️ Judge: {avg_judge:.1f}/5"
        if avg_usd > 0.0:
            summary += f" | 💵 Ø ${avg_usd:.4f}"
        summary += "\n   " + "=" * 70 + "\n"
        print(summary)

    def _record_global_metrics(
        self,
        model: str,
        results: list[dict[str, Any]],
        benchmark_info: dict[str, Any],
    ) -> None:
        """Sammelt execution_times + timeout_count und ruft append_global_run_metrics."""
        if not (self.audit_mode and results):
            return
        execution_times: list[float] = []
        timeout_count = 0
        asset_ids: list[str] = []
        for res in results:
            if res.get("type") == "system":
                continue
            a_id = res.get("asset_id", "")
            if a_id:
                asset_ids.append(a_id)
            t_exe = res.get("execution_time", 0.0)
            execution_times.append(t_exe)
            if res.get("status") == "error" or t_exe > TIMEOUT_DEFAULT:
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

    def _cleanup_local_provider(self, provider: str) -> None:
        """Optionaler End-of-Run Cleanup für lokale Provider (Stop + Cache-Clear).

        Für llama.cpp-Provider (llamacpp, llamacpp_spark) wird der Cleanup
        NICHT hier ausgeführt — der Batch-Orchestrator in benchmark_auto.py
        übernimmt den Lifecycle (Start/Stop pro Modell, Cleanup am Ende des Batches).
        Hier würde ein vorzeitiger Stop den Server nach jedem einzelnen Asset-Run
        beenden und den nächsten Modul-Run sabotieren.

        Das Flag `_skip_llamacpp_cleanup` kann vom Orchestrator gesetzt werden,
        um diesen Pfad explizit zu deaktivieren.
        """
        local_provider_names = (
            "ollama",
            "llamacpp",
            "llamacpp_spark",
            "llama_cpp",
            "llamacpp_local",
            "vllm_spark",
        )
        provider_l = provider.lower()
        if provider_l not in local_provider_names:
            return

        # llama.cpp-Provider: Cleanup liegt beim Batch-Orchestrator (benchmark_auto.py),
        # nicht beim einzelnen run_benchmark()-Aufruf. Verhindert vorzeitigen Server-Stop
        # zwischen Modul-Runs innerhalb desselben Modells.
        _llamacpp_providers = ("llamacpp", "llamacpp_spark", "llama_cpp", "llamacpp_local")
        if provider_l in _llamacpp_providers:
            # HOTFIX: Environment-Variable als Fallback für Subprozess-Delegation
            _skip = getattr(self, "_skip_llamacpp_cleanup", False)
            _env_skip = os.environ.get("CRUCIBLE_SKIP_LLAMACPP_CLEANUP") == "1"
            if _skip or _env_skip:
                logger.debug(
                    "_cleanup_local_provider: llama.cpp-Cleanup übersprungen "
                    "(provider=%s, _skip_llamacpp_cleanup=True oder CRUCIBLE_SKIP_LLAMACPP_CLEANUP=1)",
                    provider,
                )
                return

        local_cfg = self.validator.config.get("providers", {}).get("local", {})
        alias_map = {
            "llama_cpp": "llamacpp",
            "llamacpp_local": "llamacpp",
            "ollama": "ollama_local",
        }
        provider_key = alias_map.get(provider_l, provider_l)
        provider_cfg = local_cfg.get(provider_key, {})

        if not provider_cfg.get("cleanup_on_exit", False):
            return

        stop_cmd = provider_cfg.get("server_stop_cmd")
        post_stop_cmd = provider_cfg.get("server_post_stop_cmd")

        print("\n🧹 End-of-Run Cleanup aktiv: stoppe lokalen Server und bereinige Cache …")
        if stop_cmd:
            try:
                subprocess.run(stop_cmd, shell=True, check=False)
            except Exception as exc:  # noqa: BLE001
                print(f"⚠️ Cleanup stop failed: {exc}")

        if post_stop_cmd:
            try:
                subprocess.run(post_stop_cmd, shell=True, check=False)
            except Exception as exc:  # noqa: BLE001
                print(f"⚠️ Cleanup post-stop failed: {exc}")

    def _save_partial_results(self, results: list[dict[str, Any]], is_local: bool):
        if results:
            print("💾 Speichere bisherige Ergebnisse...")
            self.save_results(results)
