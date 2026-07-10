#!/usr/bin/env python3
"""
🤖 CRUCIBLE AUTOMATIC BENCHMARK 🤖
===================================
Führt ALLE aktivierten Benchmarks für ALLE verfügbaren Modelle (Lokal & Kommerziell) aus.
Füllt automatisch fehlende Benchmarks auf (Auto-Fill).

Usage:
    python scripts/benchmark_auto.py
"""

import argparse
import sys
import os
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any

# Pfad setup — MUSS vor den `from utils...` Imports stehen!
# Python 3.14+ verändert das sys.path-Verhalten für `python script.py` —
# ohne absolutes Path-Vorab-Setting schlagen relative Package-Imports fehl.
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Third-party imports
# pylint: disable=import-error, wrong-import-position
from utils.constants import TIMEOUT_OLLAMA_LIST_FAST  # noqa: E402

try:
    from dotenv import load_dotenv
except ImportError:
    # pylint: disable=unused-argument
    def load_dotenv(*args, **kwargs) -> bool:
        return False


# pylint: enable=import-error

# Load environment variables
load_dotenv()

# (Pfad-Setup wurde bereits vor den Imports erledigt — siehe oben.)

# Local imports
# pylint: disable=import-error, wrong-import-position
from scripts.core.unified_runner import UnifiedBenchmarkRunner  # noqa: E402
from utils.config_validator import ConfigValidator  # noqa: E402
from utils.model_utils import (  # noqa: E402
    is_model_suitable_for_benchmark,
    get_ollama_models_info,
)

# Gemeinsame llama.cpp-Batch-Orchestrierung
from scripts.core.runner_contract import update_leaderboard  # noqa: E402
from scripts.core.llamacpp_batch import (  # noqa: E402
    get_enabled_llamacpp_providers,
    get_existing_results,
    get_startable_assets,
    is_llamacpp_provider,
    set_llamacpp_provider_context,
    stop_llamacpp_provider_server,
    run_llamacpp_provider_cleanup,
)
from scripts.core.vllm_batch import (  # noqa: E402
    get_enabled_vllm_providers,
    is_vllm_provider,
    set_vllm_provider_context,
    stop_vllm_provider_server,
    run_vllm_provider_cleanup,
    vllm_model_session,
    VllmSessionError,
)

# Konstante für "Modell kann keine Tools" (getestet und fehlgeschlagen)
SUPPORT_TOOL_USE_NOT_APPLICABLE = "not_applicable"
from utils.llm_client import LLMClient  # noqa: E402
from utils.module_registry import get_active_modules  # noqa: E402
from utils.provider_health import filter_testable_cards  # noqa: E402, F401

# Subprocess-Wrapper (Sektion E Refactoring) — Re-Export für Backward-Compat
# mit Tests, die `patch.object(benchmark_auto, "_xxx")` nutzen.
from scripts.core.delegate_runner import (  # noqa: E402, F401
    read_json_summary as _read_json_summary,
    run_delegate_for_model as _run_delegate_for_model,
    run_score_delegate_for_model as _run_score_delegate_for_model,
    dispatch_tooluse_subprocess as _dispatch_tooluse_subprocess,
)
from scripts.core.lifecycle_hooks import (  # noqa: E402, F401
    collect_untested_tooluse_cards as _collect_untested_tooluse_cards,
    load_cards_for_models as _load_cards_for_models,
    write_unreachable_report as _write_unreachable_report,
    filter_untested_with_caches as _filter_untested_with_caches,
    print_untested_summary as _print_untested_summary,
    run_untested_tooluse_models as _run_untested_tooluse_models,
    run_tooluse_backlog_phase as _run_tooluse_backlog_phase,
)

# pylint: enable=import-error, wrong-import-position

# Logging Setup
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("auto_benchmark")

SCORE_EXCLUDED_MODULES = {"tooluse", "political_compass"}

# CARD_DIR bleibt hier definiert (Tests patchen benchmark_auto.CARD_DIR),
# wird aber von lifecycle_hooks.py per deferred Import gelesen.
CARD_DIR = Path("benchmark_scores/model_cards")


def check_ollama_status() -> bool:
    """Prüft, ob der Ollama-Service läuft."""
    ollama_path = shutil.which("ollama")
    if not ollama_path:
        print("❌ FEHLER: 'ollama' Befehl nicht im PATH gefunden.")
        return False

    try:
        # Pingen mit 'list'
        subprocess.run(
            [ollama_path, "list"], capture_output=True, check=True, timeout=TIMEOUT_OLLAMA_LIST_FAST
        )
        return True
    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        FileNotFoundError,
    ):
        print("❌ FEHLER: Ollama Service antwortet nicht.")
        print(
            "   Bitte starten Sie Ollama ('ollama serve') in einem separaten Terminal.\n"
        )
        return False


def get_all_modules(validator: ConfigValidator) -> list[dict[str, Any]]:
    """Extrahiert alle aktivierten Module aus der Config (SSOT)."""
    modules = []
    active = get_active_modules(validator.config)

    for key, mod, internal in active:
        metadata = internal.get("metadata", {})
        execution = internal.get("execution", {})
        modules.append(
            {
                "id": key,
                "key": key,
                "name": metadata.get("name", mod.get("name", key)),
                "path": f"{mod['path']}/assets",
                "module_path": mod["path"],  # Wichtig für Module Loader
                "test_class": execution.get(
                    "test_class", mod.get("test_class", "CodeQualityTest")
                ),
                "description": metadata.get("description", mod.get("description", "")),
                "execution_mode": execution.get(
                    "execution_mode", mod.get("execution_mode", "standard")
                ),
                "min_runs": execution.get("min_runs", mod.get("min_runs", 1)),
                "requires_mcp": execution.get("requires_mcp", False),
                "skip_if_card_false": execution.get("skip_if_card_false"),
                "delegate_script": execution.get("delegate_script"),
                "delegate_extra_args": execution.get("delegate_extra_args", []) or [],
            }
        )
    return modules


# Entfernt Phase 2: get_startable_assets (130 LOC Duplikat) → verwendet get_startable_assets aus llamacpp_batch.py


def _is_score_module(module: dict[str, Any]) -> bool:
    """Returns True when the module belongs to the score-worker scope (modules 1-7)."""
    return module.get("key") not in SCORE_EXCLUDED_MODULES


def _extract_config_model_ids(models_cfg: Any) -> list[str]:
    """Extracts model ids from provider config entries."""
    model_ids: list[str] = []
    for entry in models_cfg or []:
        if isinstance(entry, dict):
            mid = entry.get("id")
            if isinstance(mid, str) and mid:
                model_ids.append(mid)
        elif isinstance(entry, str) and entry:
            model_ids.append(entry)
    return model_ids


# Entfernt: _get_enabled_local_llamacpp_providers → verwendet get_enabled_llamacpp_providers aus llamacpp_batch.py
# Entfernt: _set_llamacpp_provider_context → verwendet set_llamacpp_provider_context aus llamacpp_batch.py
# Entfernt: _is_llamacpp_provider → verwendet is_llamacpp_provider aus llamacpp_batch.py
# Entfernt: _stop_enabled_local_llamacpp_servers → verwendet stop_llamacpp_provider_server aus llamacpp_batch.py


def _is_local_server_provider(provider_key: str) -> bool:
    """True für lokale OpenAI-kompatible Server (llama.cpp + vLLM).

    Wird in ``_run_module_for_model`` genutzt, um zu entscheiden, ob ein
    Score-Modul in-process ausgeführt werden muss (wg. Server-State) bzw.
    das Cleanup-Flag an Delegate-Scripts weitergereicht wird.

    Vereinigungsmenge von ``is_llamacpp_provider`` (M4 + Spark llama.cpp)
    und ``is_vllm_provider`` (vllm_spark).
    """
    return is_llamacpp_provider(provider_key) or is_vllm_provider(provider_key)


def _run_single_llamacpp_provider_batch(
    provider_key: str,
    provider_cfg: dict[str, Any],
    modules: list[dict[str, Any]],
    validator: ConfigValidator,
    force: bool,
    audit_mode: bool,
    mcp_mode: str,
) -> None:
    """Runs the configured model list for one local llama.cpp provider.

    Der Batch-Orchestrator übernimmt den vollständigen Server-Lifecycle:
    - Prophylaktischer Stop des eigenen Providers vor dem ersten Modell
    - Start/Stop des Servers pro Modell via lcpp_client
    - Cleanup (stop_cmd + post_stop_cmd) am Ende des Batches

    Das `_skip_llamacpp_cleanup`-Flag auf dem Runner verhindert, dass
    `_cleanup_local_provider()` in `run_benchmark()` den Server nach
    jedem einzelnen Asset-Run vorzeitig stoppt.
    """
    model_ids = _extract_config_model_ids(provider_cfg.get("models", []))
    if not model_ids:
        print(f"⚠️  Keine Modelle für '{provider_key}' konfiguriert.")
        return

    csv_path = Path(
        validator.config.get("output", {}).get("local_models_csv", "benchmark_scores/local_models_benchmark.csv")
    )
    existing_tests = get_existing_results(csv_path, force=force)
    runner, lcpp_client = _setup_llamacpp_runner_and_client(
        provider_key, force, audit_mode,
    )
    if lcpp_client is None:
        return

    provider_label = provider_cfg.get("name", provider_key)
    print(f"\n🖥️  [1b/2] LOKALE MODELLE (LLAMA.CPP: {provider_label})")
    print(f"{'=' * 40}")
    print(f"Konfigurierte Modelle: {len(model_ids)}")
    print(f"Liste: {', '.join(model_ids)}\n")
    print(f"Ignoriere bereits vorhandene Ergebnisse in: {csv_path}\n")

    # Nur den eigenen Provider stoppen (nicht alle llama.cpp-Provider)
    stop_llamacpp_provider_server(validator.config, provider_key=provider_key)

    interrupted = False
    try:
        for i, model_id in enumerate(model_ids, 1):
            print(f"\n➡️  MOD [{provider_key} {i}/{len(model_ids)}]: {model_id}")
            if not _has_open_tests(modules, model_id, existing_tests):
                print("   ✓ Alle Benchmarks bereits vorhanden — überspringe Modell.")
                continue
            if not lcpp_client.start_server(model_id):
                print(f"   ❌ Server für '{model_id}' konnte nicht gestartet werden — überspringe.")
                continue
            _run_llamacpp_model_modules(
                runner=runner, model_id=model_id, modules=modules,
                existing_tests=existing_tests, force=force, audit_mode=audit_mode,
                mcp_mode=mcp_mode, provider_key=provider_key,
            )
    except KeyboardInterrupt:
        print("\n⛔  Abbruch durch Benutzer.")
        interrupted = True
    finally:
        print("\n   🛑 Stoppe llama.cpp Server...")
        lcpp_client.stop_server()
        # End-of-Batch Cleanup (post_stop_cmd, Cache-Bereinigung) für diesen Provider
        run_llamacpp_provider_cleanup(provider_key, provider_cfg)
        if interrupted:
            sys.exit(1)


# -- Phase 3H: Helfer für _run_single_llamacpp_provider_batch --------------------

def _setup_llamacpp_runner_and_client(
    provider_key: str, force: bool, audit_mode: bool,
) -> tuple[UnifiedBenchmarkRunner, Any]:
    """Erstellt Runner + LlamaCppClient mit aktivierten Skip-Cleanup-Flags."""
    runner = UnifiedBenchmarkRunner(force=force, audit_mode=audit_mode)
    # Cleanup-Kontrolle liegt beim Batch-Orchestrator, nicht beim einzelnen run_benchmark().
    runner._skip_llamacpp_cleanup = True  # type: ignore[attr-defined]

    lcpp_client = runner.client.clients.get(provider_key)
    if lcpp_client is None:
        print(f"❌ LlamaCppClient '{provider_key}' nicht im Client-Registry gefunden.")
        return runner, None
    # Flag auch auf Client setzen, damit query() den Client nicht zurücksetzt
    lcpp_client._skip_llamacpp_cleanup = True  # type: ignore[attr-defined]
    set_llamacpp_provider_context(lcpp_client, provider_key)
    return runner, lcpp_client


def _has_open_tests(
    modules: list[dict[str, Any]],
    model_id: str,
    existing_tests: set[tuple[str, str]],
) -> bool:
    """Prüft, ob mindestens ein Modul für das Modell noch offene Assets hat."""
    return any(
        get_startable_assets(module, model_id, existing_tests) for module in modules
    )


def _run_llamacpp_model_modules(
    *,
    runner: UnifiedBenchmarkRunner,
    model_id: str,
    modules: list[dict[str, Any]],
    existing_tests: set[tuple[str, str]],
    force: bool,
    audit_mode: bool,
    mcp_mode: str,
    provider_key: str,
) -> None:
    """Iteriert über Module für ein llama.cpp-Modell, bricht bei echtem Fehler ab."""
    for module in modules:
        assets_todo = get_startable_assets(module, model_id, existing_tests)
        status = _run_module_for_model(
            runner, model_id, module, existing_tests,
            force=force, audit=audit_mode, mcp_mode=mcp_mode, provider=provider_key,
        )
        if status == "failed" and assets_todo:
            # ECHTER Fehler bei offenen Assets (Leaderboard-Skip zählt nicht).
            print(
                f"   ⚠️  Modul '{module.get('key', 'unknown')}' für '{model_id}' fehlgeschlagen "
                "(mit offenen Assets). Restliche Module für dieses Modell werden übersprungen."
            )
            break
        # "ran" oder "skipped" → weiter


# -- vLLM-Batch (Phase 48): spiegelbildlich zu _run_single_llamacpp_provider_batch -
# Gleiche Helper-Konventionen (_setup, _has_open_tests, _run_<provider>_model_modules),
# aber vllm-spezifische Provider-Discovery (api_type=vllm) und Lifecycle.


def _setup_vllm_runner_and_client(
    provider_key: str, force: bool, audit_mode: bool,
) -> tuple[UnifiedBenchmarkRunner, Any]:
    """Erstellt Runner + VllmClient mit aktivierten Skip-Cleanup-Flags.

    Spiegelbild zu ``_setup_llamacpp_runner_and_client``. Setzt zwei Flags:

    - ``runner._skip_llamacpp_cleanup``: Runner-seitig. ``_cleanup_local_provider``
      prüft dieses Flag heute nur für llama.cpp-Provider (nicht für vllm_spark);
      vllm_spark wird dort über ``cleanup_on_exit``-Config gesteuert (aktuell
      unset → Early-Return). Das Flag bleibt als Forward-Looking-Compat gesetzt.
    - ``vllm_client._skip_vllm_cleanup``: Client-seitig. Verhindert, dass
      ``VllmBaseClient.query()`` nach jedem Request den HTTP-Client zurücksetzt
      (``_client = None``) — hält die Connection-Pool während des Batches alive.
      Existiert seit vllm_base.py:984 (``getattr(self, "_skip_vllm_cleanup", False)``).
    """
    runner = UnifiedBenchmarkRunner(force=force, audit_mode=audit_mode)
    # Cleanup-Kontrolle liegt beim Batch-Orchestrator, nicht beim einzelnen run_benchmark().
    runner._skip_llamacpp_cleanup = True  # type: ignore[attr-defined]

    vllm_client = runner.client.clients.get(provider_key)
    if vllm_client is None:
        print(f"❌ VllmClient '{provider_key}' nicht im Client-Registry gefunden.")
        return runner, None
    # Client-seitiges Skip-Flag: verhindert Connection-Reset pro Query.
    vllm_client._skip_vllm_cleanup = True  # type: ignore[attr-defined]
    set_vllm_provider_context(vllm_client, provider_key)
    return runner, vllm_client


def _run_vllm_model_modules(
    *,
    runner: UnifiedBenchmarkRunner,
    model_id: str,
    modules: list[dict[str, Any]],
    existing_tests: set[tuple[str, str]],
    force: bool,
    audit_mode: bool,
    mcp_mode: str,
    provider_key: str,
) -> None:
    """Iteriert über Module für ein vLLM-Modell, bricht bei echtem Fehler ab.

    ``_run_module_for_model`` returns ``"skipped"`` wenn keine offenen Assets
    vorhanden sind — ``"failed"`` impliziert also zwingend offene Assets.
    Ein separater ``get_startable_assets``-Aufruf hier ist redundant (die
    asset-Ermittlung läuft in ``_run_module_for_model`` selbst).
    """
    for module in modules:
        status = _run_module_for_model(
            runner, model_id, module, existing_tests,
            force=force, audit=audit_mode, mcp_mode=mcp_mode, provider=provider_key,
        )
        if status == "failed":
            print(
                f"   ⚠️  Modul '{module.get('key', 'unknown')}' für '{model_id}' fehlgeschlagen "
                "(mit offenen Assets). Restliche Module für dieses Modell werden übersprungen."
            )
            break


def _run_single_vllm_provider_batch(
    provider_key: str,
    provider_cfg: dict[str, Any],
    modules: list[dict[str, Any]],
    validator: ConfigValidator,
    force: bool,
    audit_mode: bool,
    mcp_mode: str,
) -> None:
    """Batch-Run für einen aktivierten lokalen vLLM-Provider.

    Vollständig analog zu ``_run_single_llamacpp_provider_batch`` —
    Server-Lifecycle (prophylaktischer Stop → Start/Stop pro Modell →
    End-of-Batch Cleanup) wird vom Orchestrator übernommen, nicht vom
    einzelnen ``run_benchmark()``-Aufruf.

    vLLM-Constraint (siehe CLAUDE.md): ``vllm-start`` ist nicht idempotent
    → kein ``swap_model()``, immer ``stop_server()`` + ``start_server()``
    zwischen Modellen. Realisiert via ``vllm_model_session``-Contextmanager
    pro Modell in der Schleife.
    """
    model_ids = _extract_config_model_ids(provider_cfg.get("models", []))
    if not model_ids:
        print(f"⚠️  Keine Modelle für '{provider_key}' konfiguriert.")
        return

    csv_path = Path(
        validator.config.get("output", {}).get(
            "local_models_csv", "benchmark_scores/local_models_benchmark.csv"
        )
    )
    existing_tests = get_existing_results(csv_path, force=force)
    runner, vllm_client = _setup_vllm_runner_and_client(
        provider_key, force, audit_mode,
    )
    if vllm_client is None:
        return

    provider_label = provider_cfg.get("name", provider_key)
    print(f"\n🖥️  [1c/2] LOKALE MODELLE (VLLM: {provider_label})")
    print(f"{'=' * 40}")
    print(f"Konfigurierte Modelle: {len(model_ids)}")
    print(f"Liste: {', '.join(model_ids)}\n")
    print(f"Ignoriere bereits vorhandene Ergebnisse in: {csv_path}\n")

    # Nur den eigenen Provider stoppen (nicht alle vLLM-Provider)
    stop_vllm_provider_server(validator.config, provider_key=provider_key)

    interrupted = False
    try:
        for i, model_id in enumerate(model_ids, 1):
            print(f"\n➡️  MOD [{provider_key} {i}/{len(model_ids)}]: {model_id}")
            if not _has_open_tests(modules, model_id, existing_tests):
                print("   ✓ Alle Benchmarks bereits vorhanden — überspringe Modell.")
                continue
            # Pro-Modell-Session: start → yield → stop. Garantiert Stop
            # zwischen Modellen (vllm-start ist nicht idempotent).
            try:
                with vllm_model_session(runner, provider_key, model_id):
                    _run_vllm_model_modules(
                        runner=runner, model_id=model_id, modules=modules,
                        existing_tests=existing_tests, force=force, audit_mode=audit_mode,
                        mcp_mode=mcp_mode, provider_key=provider_key,
                    )
            except VllmSessionError as exc:
                print(f"   ❌ {exc} — überspringe Modell.")
                continue
    except KeyboardInterrupt:
        print("\n⛔  Abbruch durch Benutzer.")
        interrupted = True
    finally:
        # End-of-Batch Cleanup (post_stop_cmd, Cache-Bereinigung).
        # Server-Stop pro Modell übernimmt vllm_model_session.
        run_vllm_provider_cleanup(provider_key, provider_cfg)
        if interrupted:
            sys.exit(1)


def _run_module_for_model(
    runner: UnifiedBenchmarkRunner,
    model: str,
    module: dict[str, Any],
    existing_tests: set[tuple[str, str]],
    force: bool = False,
    audit: bool = True,
    mcp_mode: str = "live",
    provider: str = "ollama",
) -> str:
    """Führt ein einzelnes Modul für ein einzelnes Modell aus.

    Wenn das Modul einen `delegate_script`-Key definiert, wird die Ausführung
    vollständig an dieses Fachscript delegiert (SSOT für Lifecycle-Logik).

    Returns:
        "ran"     — Modul wurde ausgeführt und Ergebnisse gespeichert.
        "skipped" — Modul wurde absichtlich übersprungen (Leaderboard-Cache,
                    keine Assets in der Detail-CSV, oder n/a via Card-Flag).
                    Kein Fehler — Score gilt als vorhanden.
        "failed"  — Modul-Ausführung ist fehlgeschlagen (Subprozess-Fehler,
                    Exception, oder leere Ergebnisse nach echtem Run).

    Die Differenzierung "skipped" vs. "failed" ist kritisch (Phase 21):
    Nur ein fehlgeschlagenes Modul mit offenen Assets rechtfertigt den
    Loop-Abbruch im Caller. Ein Leaderboard-Skip ist eine gültige
    Erfolgsmeldung (Score existiert bereits) und darf den Loop NICHT
    abbrechen — sonst wird der llama.cpp-Server fälschlich gestoppt.
    """
    module_key = module.get("key")

    # Autoritative Per-Asset-Pruefung: get_startable_assets() liest die
    # Detail-CSVs und ermittelt welche Assets fehlen. Ein Leaderboard-Score
    # ist ein Aggregat aus partiellen Daten und KEIN Beweis fuer Per-Asset-
    # Vollstaendigkeit (v4.10.12: Leaderboard-Cache-Check entfernt — er hat
    # Modelle mit fehlenden Assets uebersprungen, weil das Leaderboard einen
    # Score aus unvollstaendigen Daten hatte).
    assets_todo = get_startable_assets(
        module=module, model=model, existing_tests=existing_tests
    )

    if not assets_todo:
        msg = f"   ✓ Bench: {module['name']} (Alle Tests bereits vorhanden)"
        if module.get("key") == "political_compass":
            msg += " [Batch-Mode Skip]"
        print(msg)
        return "skipped"

    print(f"   📊 Bench: {module['name']} ({len(assets_todo)} neue Tests) ...")

    if _is_score_module(module) and not _is_local_server_provider(provider):
        # For local llama.cpp / vLLM providers we must stay in-process to preserve the
        # server ownership/context of the already started model server.
        ok = _run_score_delegate_for_model(module, model, force=force, audit=audit)
        return "ran" if ok else "failed"

    if module.get("delegate_script"):
        # Für lokale Server-Provider (llama.cpp + vLLM): Cleanup-Flag an Delegate weitergeben
        _skip_cleanup = _is_local_server_provider(provider)
        ok = _run_delegate_for_model(
            module, model, force=force, audit=audit, mcp_mode=mcp_mode,
            skip_llamacpp_cleanup=_skip_cleanup,
        )
        return "ran" if ok else "failed"

    try:
        results = runner.run_benchmark(provider=provider, model=model, benchmark_info=module, assets=assets_todo)
        if results:
            runner.save_results(results)
            # Leaderboard-Update nach jedem Modul (Design-Constraint:
            # "am Ende eines jeden Moduls eine Aktualisierung des Leaderboards").
            # Pfad 1 (Score-Delegate) und Pfad 2 (Delegate-Script) rufen
            # update_leaderboard() in ihren Sub-Workern auf. Pfad 3 (in-process
            # für llama.cpp) muss das selbst tun (v4.10.12).
            update_leaderboard(ROOT_DIR)
            return "ran"
        # Run wurde versucht, hat aber keine Ergebnisse produziert
        return "failed"
    except KeyboardInterrupt:
        print("\n⛔  Abbruch durch Benutzer.")
        sys.exit(1)
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"   ❌ Fehler: {e}")
        return "failed"


def run_llamacpp_batch(
    modules: list[dict[str, Any]],
    validator: ConfigValidator,
    force: bool = False,
    audit_mode: bool = False,
    mcp_mode: str = "live",
) -> None:
    """Batch-Run für alle aktivierten lokalen llama.cpp-Provider aus der Config (SSOT)."""
    enabled_llamacpp = get_enabled_llamacpp_providers(validator.config)
    if not enabled_llamacpp:
        print("⏭️  Kein aktivierter lokaler llama.cpp-Provider in der Config — überspringe.")
        return

    for provider_key, provider_cfg in enabled_llamacpp:
        _run_single_llamacpp_provider_batch(
            provider_key=provider_key,
            provider_cfg=provider_cfg,
            modules=modules,
            validator=validator,
            force=force,
            audit_mode=audit_mode,
            mcp_mode=mcp_mode,
        )


def run_vllm_batch(
    modules: list[dict[str, Any]],
    validator: ConfigValidator,
    force: bool = False,
    audit_mode: bool = False,
    mcp_mode: str = "live",
) -> None:
    """Batch-Run für alle aktivierten lokalen vLLM-Provider aus der Config (SSOT)."""
    enabled_vllm = get_enabled_vllm_providers(validator.config)
    if not enabled_vllm:
        print("⏭️  Kein aktivierter lokaler vLLM-Provider in der Config — überspringe.")
        return

    for provider_key, provider_cfg in enabled_vllm:
        _run_single_vllm_provider_batch(
            provider_key=provider_key,
            provider_cfg=provider_cfg,
            modules=modules,
            validator=validator,
            force=force,
            audit_mode=audit_mode,
            mcp_mode=mcp_mode,
        )


def run_local_batch(
    modules: list[dict[str, Any]],
    validator: ConfigValidator,
    force: bool = False,
    audit_mode: bool = False,
    mcp_mode: str = "live",
) -> None:
    # pylint: disable=unused-argument
    ollama_cfg = validator.config.get("providers", {}).get("local", {}).get("ollama_local", {})
    if not _is_ollama_batch_runnable(ollama_cfg):
        return

    print("\n🤖  [1/2] LOKALE MODELLE (OLLAMA)")
    print(f"{'=' * 40}")
    if not check_ollama_status():
        print("⏭️  Überspringe lokale Benchmarks, da Ollama nicht läuft.")
        return

    csv_path = Path(validator.config.get("output", {}).get("local_models_csv", "benchmark_scores/local_models_benchmark.csv"))
    existing_tests = get_existing_results(csv_path, force=force)
    suitable_models = _resolve_suitable_local_models(ollama_cfg)
    if not suitable_models:
        print("⚠️  Keine geeigneten lokalen Modelle gefunden.")
        return

    print(f"Gefundene Modelle: {len(suitable_models)}")
    print(f"Liste: {', '.join(suitable_models)}\n")
    print(f"Ignoriere bereits vorhandene Ergebnisse in: {csv_path}\n")

    runner = UnifiedBenchmarkRunner(force=force, audit_mode=audit_mode)
    try:
        for i, model in enumerate(suitable_models, 1):
            print(f"\n➡️  MOD [Lokal {i}/{len(suitable_models)}]: {model}")
            if not _has_open_tests(modules, model, existing_tests):
                print("   ✓ Alle Benchmarks bereits vorhanden — überspringe Modell.")
                continue
            _run_ollama_model_modules(
                runner, model, modules, existing_tests, force, audit_mode, mcp_mode,
            )
    except KeyboardInterrupt:
        print("\n⛔  Abbruch durch Benutzer.")
        sys.exit(1)


# -- Phase 3F: Helfer für run_local_batch -----------------------------------------

def _is_ollama_batch_runnable(ollama_cfg: dict[str, Any]) -> bool:
    """Prüft Enabled-Flag + Binary-Verfügbarkeit. Printet Skip-Hinweise."""
    if not ollama_cfg.get("enabled", False):
        print("⏭️  Ollama local Provider deaktiviert — überspringe.")
        return False
    if not shutil.which("ollama"):
        print("⏭️  Überspringe lokale Benchmarks: 'ollama' Binary nicht im PATH.")
        return False
    return True


def _resolve_suitable_local_models(ollama_cfg: dict[str, Any]) -> list[str]:
    """Löst suitable_models auf (config vs auto-discover), filtert by benchmark-suitability."""
    configured_model_ids = _extract_config_model_ids(ollama_cfg.get("models", []))
    auto_discover = bool(ollama_cfg.get("auto_discover", True))

    if configured_model_ids and not auto_discover:
        return [m for m in configured_model_ids if is_model_suitable_for_benchmark(m)]

    try:
        all_models = [m["name"] for m in get_ollama_models_info()]
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"❌ Fehler beim Laden der Modell-Liste: {e}")
        return []

    return [m for m in all_models if is_model_suitable_for_benchmark(m)]


def _run_ollama_model_modules(
    runner: UnifiedBenchmarkRunner,
    model: str,
    modules: list[dict[str, Any]],
    existing_tests: set[tuple[str, str]],
    force: bool,
    audit_mode: bool,
    mcp_mode: str,
) -> None:
    """Iteriert über Module für ein Ollama-Modell."""
    for module in modules:
        # Phase 21: had_new_results nur auf "ran" setzen — "skipped" und
        # "failed" dürfen den Counter nicht hochzählen.
        _run_module_for_model(
            runner, model, module, existing_tests,
            force=force, audit=audit_mode, mcp_mode=mcp_mode,
        )




def run_commercial_batch(
    modules: list[dict[str, Any]],
    validator: ConfigValidator,
    force: bool = False,
    audit_mode: bool = False,
    mcp_mode: str = "live",
) -> None:
    """Batch-Run für alle konfigurierten kommerziellen Modelle."""
    print("\n🏢  [2/2] KOMMERZIELLE MODELLE (API)")
    print(f"{'=' * 40}")

    runner = UnifiedBenchmarkRunner(force=force, audit_mode=audit_mode)
    from utils.adaptive_pause import BenchmarkMode
    runner.mode = BenchmarkMode.DEV

    active_providers = _resolve_active_commercial_providers(validator)
    if not active_providers:
        return

    active_providers = _check_commercial_provider_accessibility(validator, active_providers)
    if not active_providers:
        return

    existing_tests = _load_commercial_existing_tests(validator, force)
    tasks = _flatten_commercial_tasks(active_providers)
    print(f"Geplante Tasks: {len(tasks)} Modell-Kombinationen")

    quota_exhausted_providers: set[str] = set()
    for i, task in enumerate(tasks, 1):
        if task["provider"] in quota_exhausted_providers:
            print(f"\n⏭️  MOD [Comm {i}/{len(tasks)}]: {task['provider']}/{task['name']} — Provider '{task['provider']}' quota-erschöpft, überspringe.")
            continue
        print(f"\n➡️  MOD [Comm {i}/{len(tasks)}]: {task['provider']}/{task['name']}")
        quota_exhausted_providers = _run_commercial_model_task(
            runner=runner,
            modules=modules,
            task=task,
            i=i,
            total=len(tasks),
            existing_tests=existing_tests,
            force=force,
            audit_mode=audit_mode,
            mcp_mode=mcp_mode,
            quota_exhausted_providers=quota_exhausted_providers,
        )

# -- Phase 3D: Helfer für run_commercial_batch -------------------------------------

def _resolve_active_commercial_providers(
    validator: ConfigValidator,
) -> dict[str, dict[str, Any]]:
    """Filtert Provider nach enabled-Flag und vorhandenem API-Key (env_var)."""
    providers_config = validator.config.get("providers", {}).get("commercial", {})
    active_providers = {
        k: v for k, v in providers_config.items() if v.get("enabled", False)
    }
    valid_providers: dict[str, dict[str, Any]] = {}
    for k, v in active_providers.items():
        env_key = v.get("env_var")
        if env_key and not os.getenv(env_key):
            print(f"⚠️  Überspringe Provider '{k}': API Key ({env_key}) fehlt in Umgebung.")
            continue
        valid_providers[k] = v
    if not valid_providers:
        print("⚠️  Keine validen kommerziellen Provider gefunden (Check API Keys).")
    return valid_providers


def _check_commercial_provider_accessibility(
    validator: ConfigValidator,
    active_providers: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Testet pro Provider, ob der LLMClient ihn erreichen kann (Budget/Auth/Netz)."""
    print("\n🔍 Prüfe API-Zugang für Provider...")
    llm_client = LLMClient(validator.config)
    accessible: dict[str, dict[str, Any]] = {}
    for k, v in active_providers.items():
        client = llm_client.clients.get(k)
        if client is None:
            print(f"   ⚠️  Provider '{k}' hat keinen dedizierten Client. Überspringe Check.")
            accessible[k] = v
            continue
        print(f"   • {k:<12} Prüfe Zugang...", end=" ", flush=True)
        if client.is_accessible():
            print("✅ OK")
            accessible[k] = v
        else:
            print("❌ Fehlgeschlagen (Auth/Budget/Netzwerk). Überspringe. (Details: make logs)")
    if not accessible:
        print("⚠️  Keine zugänglichen kommerziellen Provider nach Prüfung gefunden.")
    return accessible


def _load_commercial_existing_tests(
    validator: ConfigValidator, force: bool,
) -> set[tuple[str, str]]:
    """Lädt Cache aus commercial_csv + cloud_csv, damit Skip-Logik greift."""
    comm_csv = Path(validator.config.get("output", {}).get("commercial_csv", "benchmark_scores/commercial_models_benchmark.csv"))
    cloud_csv = Path(validator.config.get("output", {}).get("cloud_models_csv", "benchmark_scores/cloud_models_benchmark.csv"))
    existing = get_existing_results(comm_csv, force=force)
    existing |= get_existing_results(cloud_csv, force=force)
    print(f"Ignoriere bereits vorhandene Ergebnisse ({len(existing)} Einträge aus Commercial/Cloud)\n")
    return existing


def _flatten_commercial_tasks(
    active_providers: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    """Konvertiert {provider: {models: [...]}} in flache Task-Liste."""
    tasks: list[dict[str, str]] = []
    for prov_key, prov_data in active_providers.items():
        for model_data in prov_data.get("models", []):
            tasks.append({
                "provider": prov_key,
                "id": model_data["id"],
                "name": model_data["name"],
            })
    return tasks


def _run_commercial_model_task(
    *,
    runner: UnifiedBenchmarkRunner,
    modules: list[dict[str, Any]],
    task: dict[str, str],
    i: int,
    total: int,
    existing_tests: set[tuple[str, str]],
    force: bool,
    audit_mode: bool,
    mcp_mode: str,
    quota_exhausted_providers: set[str],
) -> set[str]:
    """Iteriert über alle Module für ein einzelnes kommerzielles Modell."""
    prov_key = task["provider"]
    model_id = task["id"]
    for module in modules:
        if prov_key in quota_exhausted_providers:
            print(f"   ⏭️ Bench: {module['name']} (Provider quota-erschöpft, überspringe)")
            continue
        quota_exhausted_providers = _run_commercial_module(
            runner=runner,
            module=module,
            prov_key=prov_key,
            model_id=model_id,
            existing_tests=existing_tests,
            force=force,
            audit_mode=audit_mode,
            mcp_mode=mcp_mode,
            quota_exhausted_providers=quota_exhausted_providers,
        )
    return quota_exhausted_providers


def _run_commercial_module(
    *,
    runner: UnifiedBenchmarkRunner,
    module: dict[str, Any],
    prov_key: str,
    model_id: str,
    existing_tests: set[tuple[str, str]],
    force: bool,
    audit_mode: bool,
    mcp_mode: str,
    quota_exhausted_providers: set[str],
) -> set[str]:
    """Führt ein einzelnes Modul (Score-Delegate, Delegate, oder Normal) aus."""
    assets_todo = get_startable_assets(module, model_id, existing_tests)
    if not assets_todo:
        print(f"   ✓ Bench: {module['name']} (Bereits erledigt)")
        return quota_exhausted_providers
    print(f"   📊 Bench: {module['name']} ({len(assets_todo)} neue Tests) ...")

    # SIM102 collapsible-if: zwei separate if-Statements statt nested
    if _is_score_module(module):
        ok = _run_score_delegate_for_model(
            module, model_id, force=force, audit=audit_mode,
        )
        if not ok:
            print(
                "   ⚠️ Score-Delegate-Run fehlgeschlagen "
                f"(provider={prov_key}, model={model_id}, module={module['key']})"
            )
        return quota_exhausted_providers

    if module.get("delegate_script"):
        ok = _run_delegate_for_model(
            module, model_id, force=force, audit=audit_mode, mcp_mode=mcp_mode,
        )
        if not ok:
            print(
                "   ⚠️ Delegate-Run fehlgeschlagen "
                f"(provider={prov_key}, model={model_id}, module={module['key']})"
            )
        return quota_exhausted_providers

    return _run_commercial_module_normal(
        runner=runner,
        module=module,
        prov_key=prov_key,
        model_id=model_id,
        assets_todo=assets_todo,
        force=force,
        quota_exhausted_providers=quota_exhausted_providers,
    )


def _run_commercial_module_normal(
    *,
    runner: UnifiedBenchmarkRunner,
    module: dict[str, Any],
    prov_key: str,
    model_id: str,
    assets_todo: list[Any],
    force: bool,
    quota_exhausted_providers: set[str],
) -> set[str]:
    """Standard-Modul-Run über UnifiedBenchmarkRunner.run_benchmark."""
    try:
        results = runner.run_benchmark(
            provider=prov_key, model=model_id,
            benchmark_info=module, assets=assets_todo,
        )
    except KeyboardInterrupt:
        print("\n⛔  Abbruch durch Benutzer.")
        sys.exit(1)
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"   ❌ Fehler: {e}")
        return quota_exhausted_providers

    quota_exhausted_providers = _update_quota_exhaustion(
        runner=runner,
        results=results,
        prov_key=prov_key,
        quota_exhausted_providers=quota_exhausted_providers,
    )
    if results:
        runner.save_results(results)
    return quota_exhausted_providers


def _update_quota_exhaustion(
    *,
    runner: UnifiedBenchmarkRunner,
    results: list[dict[str, Any]],
    prov_key: str,
    quota_exhausted_providers: set[str],
) -> set[str]:
    """Doppel-Erkennung: Runner-Flag (Budget-Keywords) + Fallback (0-Token/0%)."""
    if runner.provider_quota_exhausted:
        print(f"   💸 Budget-/Quota-Fehler via Runner erkannt für Provider '{prov_key}'. Alle weiteren Modelle dieses Providers werden übersprungen.")
        quota_exhausted_providers.add(prov_key)
        runner.provider_quota_exhausted = False
        return quota_exhausted_providers

    if not results:
        return quota_exhausted_providers
    all_zero_tokens = all(r.get("tokens_used", 0) == 0 for r in results)
    all_zero_scores = all(r.get("percentage", 0) == 0.0 for r in results)
    if all_zero_tokens and all_zero_scores and prov_key not in quota_exhausted_providers:
        print(f"   💸 Quota-Erschöpfung (Fallback-Erkennung) für Provider '{prov_key}'. Alle weiteren Modelle dieses Providers werden übersprungen.")
        quota_exhausted_providers.add(prov_key)
    return quota_exhausted_providers


def main():
    """Main entry point."""
    args = _parse_cli_args()
    _print_banner(args)
    validator = ConfigValidator()
    modules = _resolve_active_modules_from_args(validator, args)
    if not modules:
        print("❌ Keine Module konfiguriert/aktiviert.")
        sys.exit(1)
    _print_active_modules(modules)

    if _run_tooluse_backlog_phase(validator, args):
        sys.exit(1)

    _run_main_benchmark_phases(modules, validator, args)


# -- Phase 3F3: Helfer für main ---------------------------------------------------

def _parse_cli_args() -> argparse.Namespace:
    """CLI-Argparse-Setup. Standard-Werte: audit=True, mcp_mode='live'."""
    parser = argparse.ArgumentParser(description="Crucible Automatic Benchmark")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Erzwingt das erneute Ausführen aller Tests (ignoriert Cache).",
    )
    parser.add_argument(
        "--modules",
        type=str,
        help="Kommagetrennte Liste von Modulen (Keys), die ausgeführt werden sollen (z.B. 'political_compass').",
    )
    parser.add_argument(
        "--silent",
        action="store_false",
        dest="audit",
        help="Deaktiviert Audit-Logging. Standard: Audit ist aktiv.",
    )
    parser.add_argument(
        "--mcp-mode",
        default="live",
        choices=["live", "mock"],
        help="MCP-Server-Modus für Module mit requires_mcp: true (default: live).",
    )
    return parser.parse_args()


def _print_banner(args: argparse.Namespace) -> None:
    """ASCII-Banner mit Modus-Hinweisen."""
    print(f"{'#' * 60}")
    print("🤖  CRUCIBLE AUTOMATIC BENCHMARK")
    print("    Füllt automatisch fehlende Benchmarks auf.")
    if args.force:
        print("    ⚠️  FORCE MODE: Alle Tests laufen erneut!")
    if not args.audit:
        print("    🔕  SILENT MODE: Audit-Protokolle deaktiviert.")
    if args.modules:
        print(f"    🎯 FOKUS: Nur Module '{args.modules}'")
    print(f"{'#' * 60}\n")


def _resolve_active_modules_from_args(
    validator: ConfigValidator, args: argparse.Namespace,
) -> list[dict[str, Any]]:
    """Lädt Module + filtert per --modules CLI-Argument."""
    modules = get_all_modules(validator)
    if not args.modules:
        return modules
    wanted = [m.strip() for m in args.modules.split(",")]
    filtered = [m for m in modules if m["key"] in wanted]
    if len(filtered) < len(wanted):
        missing = set(wanted) - {m["key"] for m in filtered}
        print(f"⚠️  Warnung: Gewünschte Module nicht gefunden/aktiviert: {missing}")
    return filtered


def _print_active_modules(modules: list[dict[str, Any]]) -> None:
    """Übersicht der aktivierten Module vor dem Lauf."""
    print(f"📋 Aktivierte Module ({len(modules)}):")
    for m in modules:
        print(f"   - {m['name']} ({m['key']})")


def _run_main_benchmark_phases(
    modules: list[dict[str, Any]],
    validator: ConfigValidator,
    args: argparse.Namespace,
) -> None:
    """Phasen 1/1b/2: Lokale (Ollama + llama.cpp) und kommerzielle Modelle."""
    aborted = False
    try:
        # Phase 1: Lokale Modelle (Ollama)
        try:
            run_local_batch(
                modules, validator,
                force=args.force, audit_mode=args.audit, mcp_mode=args.mcp_mode,
            )
        except (KeyboardInterrupt, SystemExit):
            print("\n⛔  Abbruch durch Benutzer (Lokale Modelle).")
            aborted = True

        # Phase 1b: Lokale Modelle (llama.cpp)
        if not aborted:
            try:
                run_llamacpp_batch(
                    modules, validator,
                    force=args.force, audit_mode=args.audit, mcp_mode=args.mcp_mode,
                )
            except (KeyboardInterrupt, SystemExit):
                print("\n⛔  Abbruch durch Benutzer (llama.cpp).")
                aborted = True

        # Phase 1c: Lokale Modelle (vLLM)
        if not aborted:
            try:
                run_vllm_batch(
                    modules, validator,
                    force=args.force, audit_mode=args.audit, mcp_mode=args.mcp_mode,
                )
            except (KeyboardInterrupt, SystemExit):
                print("\n⛔  Abbruch durch Benutzer (vLLM).")
                aborted = True

        # Phase 2: Kommerzielle Modelle
        if not aborted:
            try:
                run_commercial_batch(
                    modules, validator,
                    force=args.force, audit_mode=args.audit, mcp_mode=args.mcp_mode,
                )
            except (KeyboardInterrupt, SystemExit):
                print("\n⛔  Abbruch durch Benutzer (Kommerzielle Modelle).")
                aborted = True
    finally:
        print("\n\n✅  AUTOMATIC RUN VERLASSEN.")
        if aborted:
            sys.exit(1)


if __name__ == "__main__":
    main()
