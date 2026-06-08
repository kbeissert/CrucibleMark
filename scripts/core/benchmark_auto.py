#!/usr/bin/env python3
"""
🤖 CRUCIBLE AUTOMATIC BENCHMARK 🤖
===================================
Führt ALLE aktivierten Benchmarks für ALLE verfügbaren Modelle (Lokal & Kommerziell) aus.
Füllt automatisch fehlende Benchmarks auf (Auto-Fill).

Usage:
    python scripts/benchmark_auto.py
"""

import sys
import os
import re
import time
import argparse
import json
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any, List, Dict, Optional, Set, Tuple

# Pfad setup — MUSS vor den `from utils...` Imports stehen!
# Python 3.14+ verändert das sys.path-Verhalten für `python script.py` —
# ohne absolutes Path-Vorab-Setting schlagen relative Package-Imports fehl.
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Third-party imports
# pylint: disable=import-error, wrong-import-position
import yaml  # noqa: E402
from utils.constants import TIMEOUT_OLLAMA_LIST_FAST  # noqa: E402
import pandas as pd  # noqa: E402

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
    normalize_model_id,
    normalize_supports_tool_use,
    strip_date_suffix,
    SUPPORT_TOOL_USE_UNTESTED,
)

# Gemeinsame llama.cpp-Batch-Orchestrierung
from scripts.core.llamacpp_batch import (  # noqa: E402
    is_llamacpp_provider,
    get_enabled_llamacpp_providers,
    set_llamacpp_provider_context,
    stop_llamacpp_provider_server,
    run_llamacpp_provider_cleanup,
    llamacpp_model_session,
    get_startable_assets,
    get_existing_results,
)

# Konstante für "Modell kann keine Tools" (getestet und fehlgeschlagen)
SUPPORT_TOOL_USE_NOT_APPLICABLE = "not_applicable"
from utils.llm_client import LLMClient  # noqa: E402
from utils.module_registry import get_active_modules  # noqa: E402
from utils.provider_health import filter_testable_cards  # noqa: E402
from datetime import datetime  # noqa: E402

# pylint: enable=import-error, wrong-import-position

# Logging Setup
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("auto_benchmark")

SCORE_EXCLUDED_MODULES = {"tooluse", "political_compass"}


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


def get_all_modules(validator: ConfigValidator) -> List[Dict[str, Any]]:
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


def _get_startable_assets(
    module: Dict[str, Any], model: str, existing_tests: Set[Tuple[str, str]]
) -> List[Path]:
    """Ermittelt Asset-Pfade, die für dieses Modell noch nicht getestet wurden.
    
    State Machine für supports_tool_use (skip_if_card_false):
    - false / "not_applicable" → Modell kann KEINE Tools → SKIP (n/a im Leaderboard)
    - true / "tested" → Modell hat Tools → prüfe ob Scores vorhanden sind
    - "untested" / anderer Wert → Test ausführen!
    
    Returns:
        Liste der zu testenden Asset-Pfade (leer wenn übersprungen oder bereits vorhanden)
    """
    assets_path = module["path"]

    # -------------------------------------------------------
    # CARD-BASED SKIP (skip_if_card_false)
    # -------------------------------------------------------
    skip_card_key = module.get("skip_if_card_false")
    if skip_card_key:
        from utils.model_utils import _find_card as _fc, normalize_supports_tool_use, SUPPORT_TOOL_USE_UNTESTED
        _card_dir = ROOT_DIR / "benchmark_scores" / "model_cards"
        _card_path = _fc(model, card_dir=_card_dir)
        if _card_path.exists():
            try:
                _card = json.loads(_card_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning(
                    "Card-Flag-Skip konnte nicht geprüft werden (model=%s, module=%s, card=%s): %s",
                    model,
                    module.get("key", module.get("name", "unknown")),
                    _card_path,
                    exc,
                )
            else:
                _raw_val = _card.get(skip_card_key)
                _norm_val = normalize_supports_tool_use(_raw_val)
                
                # Fall 1: Modell kann KEINE Tools (false oder "not_applicable")
                # → SKIP, Test nicht möglich
                if _norm_val is False or _raw_val == SUPPORT_TOOL_USE_NOT_APPLICABLE:
                    _reason = "not_applicable" if _raw_val == SUPPORT_TOOL_USE_NOT_APPLICABLE else "false"
                    print(f"   ⏩ Bench: {module['name']} ({skip_card_key}={_reason} in Card — übersprungen)")
                    return []
                
                # Fall 2: "untested" oder unbekannter Wert → Test ausführen!
                # NICHT skippen - der Test muss durchgeführt werden
                if _norm_val == SUPPORT_TOOL_USE_UNTESTED or _raw_val == SUPPORT_TOOL_USE_UNTESTED:
                    # Test ausführen - nicht skippen
                    pass
                # Fall 3: true ("tested") → weiter zum normalen Cache-Check
                # Dies geschieht weiter unten
    # -------------------------------------------------------
    # SPECIAL HANDLING FOR BATCH MODULES (e.g. Political Compass)
    # -------------------------------------------------------
    # Batch-Module (wie Political Compass) erzeugen oft nur EINEN Eintrag (Aggregiert).
    # Da ein Re-Run sehr teuer ist (81+ Fragen), überspringen wir, wenn das Aggregat da ist.
    # Wir prüfen hier NICHT auf Aktualität (Datum) oder Vollständigkeit der Assets.
    #
    # PC-Ergebnisse sind DAUERHAFT gültig und verfallen nicht automatisch.
    # Sie werden übersprungen, solange (model, "political_compass_v3") im Cache existiert.
    # Um einen Re-Run für ein Modell zu erzwingen, müssen die Zeilen dieses Modells
    # manuell aus political_compass_results.csv und political_compass_leaderboard.csv
    # entfernt werden. Falls PC-Fragen überarbeitet werden, sind alle betroffenen
    # Modell-Einträge gleichermaßen manuell zu löschen.
    if (
        module.get("execution_mode") == "batch"
        or module.get("key") == "political_compass"
    ):
        batch_id = "political_compass_v3"
        # save_leaderboard_csv() strips OpenRouter date suffixes when writing the PC leaderboard:
        # -YYYYMMDD (8-digit) and -MMDD with valid months 01-12 (e.g. -0127 for Jan 27).
        # Version suffixes like -2503 / -2411 are intentionally NOT stripped.
        # Normalize identically so the cache lookup matches dated config aliases.
        model_normalized = strip_date_suffix(model)
        model_hf_stripped = normalize_model_id(model)
        if (
            (model, batch_id) in existing_tests
            or (model_normalized, batch_id) in existing_tests
            or (model_hf_stripped, batch_id) in existing_tests
        ):
            return []
    # -------------------------------------------------------

    # Der Runner hat Methode zum Finden, aber wir brauchen den Pfad
    # Da Runner interne Methoden hat, rufen wir hier eine Hilfsfunktion nach
    # Aber wir können auch einfach globben, da wir den Pfad haben.
    # Da UnifiedBenchmarkRunner assets_path als String/Path erwartet:
    asset_files = []
    p = Path(assets_path)
    if p.exists():
        asset_files = sorted(list(p.glob("*.yaml")))

    if not asset_files:
        return []

    assets_todo = []
    for asset_f in asset_files:
        try:
            with open(asset_f, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                asset_id = data.get("metadata", {}).get("id")

            if not asset_id:
                logger.warning(
                    "Asset ohne metadata.id wird ausgeführt (model=%s, module=%s, asset=%s)",
                    model,
                    module.get("key", module.get("name", "unknown")),
                    asset_f,
                )
                assets_todo.append(asset_f)
                continue

            model_hf_stripped = normalize_model_id(model)
            if (model, asset_id) in existing_tests or (model_hf_stripped, asset_id) in existing_tests:
                continue

            assets_todo.append(asset_f)
        except (OSError, yaml.YAMLError) as exc:
            # Fallback: Einfach ausführen wenn Parse Error
            logger.warning(
                "Asset konnte nicht geparst werden, wird defensiv ausgeführt "
                "(model=%s, module=%s, asset=%s): %s",
                model,
                module.get("key", module.get("name", "unknown")),
                asset_f,
                exc,
            )
            assets_todo.append(asset_f)

    return assets_todo


def _run_delegate_for_model(
    module: Dict[str, Any],
    model: str,
    force: bool = False,
    audit: bool = True,
    mcp_mode: str = "live",
    skip_llamacpp_cleanup: bool = False,
) -> bool:
    """Delegiert die Ausführung eines Moduls an das zuständige Fachscript.

    Das Fachscript verantwortet seinen eigenen Lifecycle (inkl. MCP falls nötig).
    Returns True wenn der Prozess erfolgreich beendet wurde (rc == 0).
    """
    script = ROOT_DIR / module["delegate_script"]
    extra = list(module.get("delegate_extra_args", []) or [])
    cmd = [sys.executable, str(script)] + extra + ["--model", model]

    safe_model = normalize_model_id(model).replace("/", "_").replace(":", "_")
    summary_dir = ROOT_DIR / "outputs" / "runs" / "dispatch_summaries"
    summary_dir.mkdir(parents=True, exist_ok=True)
    summary_path = summary_dir / f"{module.get('key', 'module')}_{safe_model}.json"
    cmd += ["--summary-json", str(summary_path)]

    if force:
        cmd.append("--force")
    if not audit:
        cmd.append("--silent")
    if module.get("requires_mcp"):
        cmd += ["--mcp-mode", mcp_mode]

    # Environment für Subprozess vorbereiten - CRUCIBLE_SKIP_LLAMACPP_CLEANUP weitergeben
    env = os.environ.copy()
    if skip_llamacpp_cleanup:
        env["CRUCIBLE_SKIP_LLAMACPP_CLEANUP"] = "1"

    result = subprocess.run(cmd, cwd=str(ROOT_DIR), env=env, check=False)

    summary = _read_json_summary(summary_path, "Delegate-Summary")
    if summary:
        status = summary.get("status", "unknown")
        mode = summary.get("mode", "unknown")
        print(
            f"   ℹ️ Delegate-Summary: module={module.get('key')} "
            f"model={model} status={status} mode={mode}"
        )
    return result.returncode == 0


def _is_score_module(module: Dict[str, Any]) -> bool:
    """Returns True when the module belongs to the score-worker scope (modules 1-7)."""
    return module.get("key") not in SCORE_EXCLUDED_MODULES


def _read_json_summary(summary_path: Path, context_label: str) -> Optional[Dict[str, Any]]:
    """Loads a dispatch summary JSON file and logs a warning on parse failure."""
    if not summary_path.exists():
        return None

    try:
        return json.loads(summary_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        logger.warning("%s konnte nicht gelesen werden: %s", context_label, summary_path)
        return None


def _extract_config_model_ids(models_cfg: Any) -> List[str]:
    """Extracts model ids from provider config entries."""
    model_ids: List[str] = []
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


def _run_single_llamacpp_provider_batch(
    provider_key: str,
    provider_cfg: Dict[str, Any],
    modules: List[Dict[str, Any]],
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
    models_list = provider_cfg.get("models", [])
    model_ids = _extract_config_model_ids(models_list)
    if not model_ids:
        print(f"⚠️  Keine Modelle für '{provider_key}' konfiguriert.")
        return

    csv_path = Path(
        validator.config.get("output", {}).get("local_models_csv", "benchmark_scores/local_models_benchmark.csv")
    )
    existing_tests = get_existing_results(csv_path, force=force)

    runner = UnifiedBenchmarkRunner(force=force, audit_mode=audit_mode)
    # Cleanup-Kontrolle liegt beim Batch-Orchestrator, nicht beim einzelnen run_benchmark()-Aufruf.
    # Verhindert vorzeitigen Server-Stop zwischen Modul-Runs innerhalb desselben Modells.
    runner._skip_llamacpp_cleanup = True  # type: ignore[attr-defined]

    lcpp_client = runner.client.clients.get(provider_key)
    if lcpp_client is None:
        print(f"❌ LlamaCppClient '{provider_key}' nicht im Client-Registry gefunden.")
        return
    # Flag auch auf Client setzen, damit query() den Client nicht zurücksetzt
    lcpp_client._skip_llamacpp_cleanup = True  # type: ignore[attr-defined]
    set_llamacpp_provider_context(lcpp_client, provider_key)

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

            # Prüfe VOR dem Server-Start, ob überhaupt Tests nötig sind
            # Vermeidet unnötiges Laden/Entladen von Modellen bei vollständigen Ergebnissen
            has_missing_tests = False
            for module in modules:
                assets_todo = _get_startable_assets(module, model_id, existing_tests)
                if assets_todo:
                    has_missing_tests = True
                    break
            
            if not has_missing_tests:
                print(f"   ✓ Alle Benchmarks bereits vorhanden — überspringe Modell.")
                continue

            if not lcpp_client.start_server(model_id):
                print(f"   ❌ Server für '{model_id}' konnte nicht gestartet werden — überspringe.")
                continue

            had_new_results = False
            for module in modules:
                assets_todo = _get_startable_assets(module, model_id, existing_tests)
                module_ok = _run_module_for_model(
                    runner,
                    model_id,
                    module,
                    existing_tests,
                    force=force,
                    audit=audit_mode,
                    mcp_mode=mcp_mode,
                    provider=provider_key,
                )
                had_new_results |= module_ok

                if assets_todo and not module_ok:
                    print(
                        f"   ⚠️  Modul '{module.get('key', 'unknown')}' für '{model_id}' fehlgeschlagen "
                        "(mit offenen Assets). Restliche Module für dieses Modell werden übersprungen."
                    )
                    break

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


def _run_score_delegate_for_model(
    module: Dict[str, Any],
    model: str,
    force: bool = False,
    audit: bool = True,
) -> bool:
    """Delegiert ein Score-Modul an scripts/run_score_benchmark.py für genau 1 Modell.

    Damit bleibt benchmark_auto reiner Orchestrator; die Ausführung liegt im
    dedizierten Score-Worker.
    """
    module_key = module.get("key")
    if not module_key:
        logger.warning("Score-Delegation ohne module.key möglich: %s", module)
        return False

    script = ROOT_DIR / "scripts" / "run_score_benchmark.py"
    if not script.exists():
        print("   ⚠️  scripts/run_score_benchmark.py nicht gefunden — überspringe.")
        return False

    cmd = [
        sys.executable,
        str(script),
        "--model",
        model,
        "--modules",
        module_key,
    ]

    safe_model = normalize_model_id(model).replace("/", "_").replace(":", "_")
    summary_dir = ROOT_DIR / "outputs" / "runs" / "dispatch_summaries"
    summary_dir.mkdir(parents=True, exist_ok=True)
    summary_path = summary_dir / f"score_{module_key}_{safe_model}.json"
    cmd += ["--summary-json", str(summary_path)]

    if force:
        cmd.append("--force")
    if not audit:
        cmd.append("--silent")

    result = subprocess.run(cmd, cwd=str(ROOT_DIR), check=False)

    summary = _read_json_summary(summary_path, "Score-Delegate-Summary")
    if summary:
        status = summary.get("status", "unknown")
        mode = summary.get("mode", "unknown")
        print(
            f"   ℹ️ Score-Delegate-Summary: module={module_key} "
            f"model={model} status={status} mode={mode}"
        )
    return result.returncode == 0


def _run_module_for_model(
    runner: UnifiedBenchmarkRunner,
    model: str,
    module: Dict[str, Any],
    existing_tests: Set[Tuple[str, str]],
    force: bool = False,
    audit: bool = True,
    mcp_mode: str = "live",
    provider: str = "ollama",
) -> bool:
    """Führt ein einzelnes Modul für ein einzelnes Modell aus.

    Wenn das Modul einen `delegate_script`-Key definiert, wird die Ausführung
    vollständig an dieses Fachscript delegiert (SSOT für Lifecycle-Logik).

    Returns:
        True wenn neue Ergebnisse gespeichert wurden, False sonst.
    """
    assets_todo = _get_startable_assets(
        module=module, model=model, existing_tests=existing_tests
    )

    if not assets_todo:
        msg = f"   ✓ Bench: {module['name']} (Alle Tests bereits vorhanden)"
        if module.get("key") == "political_compass":
            msg += " [Batch-Mode Skip]"
        print(msg)
        return False

    print(f"   📊 Bench: {module['name']} ({len(assets_todo)} neue Tests) ...")

    if _is_score_module(module):
        # For local llama.cpp providers we must stay in-process to preserve the
        # server ownership/context of the already started model server.
        if not is_llamacpp_provider(provider):
            return _run_score_delegate_for_model(module, model, force=force, audit=audit)

    if module.get("delegate_script"):
        # Für llama.cpp-Provider: Cleanup-Flag an Delegate weitergeben
        _skip_cleanup = is_llamacpp_provider(provider)
        return _run_delegate_for_model(
            module, model, force=force, audit=audit, mcp_mode=mcp_mode,
            skip_llamacpp_cleanup=_skip_cleanup
        )

    try:
        results = runner.run_benchmark(provider=provider, model=model, benchmark_info=module, assets=assets_todo)
        if results:
            runner.save_results(results)
            return True
    except KeyboardInterrupt:
        print("\n⛔  Abbruch durch Benutzer.")
        sys.exit(1)
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"   ❌ Fehler: {e}")
    return False


# ---------------------------------------------------------------------------
# TOOL-USE BACKLOG: untested Cards
# ---------------------------------------------------------------------------

CARD_DIR = Path("benchmark_scores/model_cards")


def _collect_untested_tooluse_cards() -> List[Tuple[str, str]]:
    """Lädt alle Model Cards mit ``supports_tool_use == "untested"``.

    Returns:
        Liste von (model_id, display_name) Tupeln, sortiert nach model_id.
    """
    untested: List[Tuple[str, str]] = []
    if not CARD_DIR.exists():
        return untested
    for card_path in sorted(CARD_DIR.glob("*.json")):
        if card_path.name == "_index.json":
            continue
        try:
            card: Dict[str, Any] = json.loads(card_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            logger.warning("Model Card konnte nicht gelesen werden: %s", card_path)
            continue
        if not isinstance(card, dict):
            logger.warning("Model Card hat ungültiges Format (kein Objekt): %s", card_path)
            continue
        if normalize_supports_tool_use(card.get("supports_tool_use")) != SUPPORT_TOOL_USE_UNTESTED:
            continue
        model_id = card.get("model_id")
        if not model_id:
            logger.warning("Untested Card ohne model_id wird übersprungen: %s", card_path)
            continue
        # Platzhalter-Card aus dem Template nicht in den Backlog aufnehmen.
        if model_id == "test" and str(card.get("card_status", "")).lower() == "draft":
            logger.info("Überspringe Platzhalter-Card im Tool-Use-Backlog: %s", card_path)
            continue
        display_name = card.get("display_name") or model_id
        untested.append((model_id, display_name))
    return untested


def _load_cards_for_models(model_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    """Lädt Card-Dicts für die gegebenen model_ids aus CARD_DIR (SSoT)."""
    cards: Dict[str, Dict[str, Any]] = {}
    for mid in model_ids:
        # Karten-Filenamen folgen der Konvention: alle nicht-alphanumerischen
        # Zeichen werden zu '_'. Probieren wir mehrere Sanitisierungs-Levels.
        candidates = [
            CARD_DIR / f"{mid}.json",
            CARD_DIR / f"{mid.replace(':', '_')}.json",
            CARD_DIR / f"{mid.replace('/', '_').replace(':', '_')}.json",
            CARD_DIR / f"{mid.replace('/', '_').replace(':', '_').replace('.', '_')}.json",
        ]
        loaded: Dict[str, Any] = {}
        for path in candidates:
            if path.exists():
                try:
                    loaded = json.loads(path.read_text(encoding="utf-8"))
                    break
                except (json.JSONDecodeError, OSError) as exc:
                    logger.warning(
                        "Model Card für Pre-Flight konnte nicht gelesen werden "
                        "(model=%s, candidate=%s): %s",
                        mid,
                        path,
                        exc,
                    )
                    continue
        if loaded:
            cards[mid] = loaded
        else:
            logger.warning(
                "Keine lesbare Model Card für Pre-Flight gefunden (model=%s)",
                mid,
            )
    return cards


def _write_unreachable_report(
    unreachable: List[Tuple[str, str, str]],
    testable: List[Tuple[str, str]],
    total: int,
) -> Optional[Path]:
    """Schreibt einen Report über nicht-erreichbare untested-Cards.

    Returns:
        Pfad zur Report-Datei oder None wenn keine Unreachables.
    """
    if not unreachable:
        return None
    report_dir = ROOT_DIR / "outputs"
    report_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = report_dir / f"tooluse_unreachable_{timestamp}.json"
    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "summary": {
            "total_untested": total,
            "testable": len(testable),
            "unreachable": len(unreachable),
        },
        "unreachable": [
            {"model_id": mid, "display_name": name, "reason": reason}
            for mid, name, reason in unreachable
        ],
    }
    try:
        report_path.write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except OSError as exc:
        print(f"   ⚠️  Report-Datei konnte nicht geschrieben werden: {exc}")
        return None
    return report_path


def _run_untested_tooluse_models(
    models: List[Tuple[str, str]],
    mcp_mode: str = "live",
    force: bool = False,
    silent: bool = False,
) -> bool:
    """Delegiert Tool-Use-Benchmarks für ``untested`` Cards an ``run_tooluse_benchmark.py``.

    Führt VOR dem Subprocess einen Pre-Flight-Check durch:
        1. Card-Lookup pro model_id
        2. validate_untested_card() prüft Provider-Erreichbarkeit
            - Ollama: ist Modell installiert?
            - API: ist ENV-Var gesetzt?
            - llama.cpp: existiert Binary-Pfad?
        3. Unerreichbare Cards werden in outputs/tooluse_unreachable_*.json geloggt
        4. Nur testbare Cards werden an den Subprocess delegiert

    Verwendet einen einzelnen Subprozess-Call mit ``--models <comma-list>`` statt
    pro Modell einen eigenen Lauf — spart MCP-Restart-Overhead.

    Returns:
        True wenn der Lauf erfolgreich gestartet wurde. False bei leerer Liste,
        fehlendem Skript oder subprocess-Fehler.
    """
    if not models:
        return False
    script = ROOT_DIR / "scripts" / "run_tooluse_benchmark.py"
    if not script.exists():
        print("   ⚠️  scripts/run_tooluse_benchmark.py nicht gefunden — überspringe.")
        return False

    # Pre-Flight-Check: nur testbare Modelle an Subprocess delegieren
    model_ids = [mid for mid, _ in models]
    card_lookup = _load_cards_for_models(model_ids)
    testable, unreachable = filter_testable_cards(models, card_lookup=card_lookup)

    print(f"   📊 Tool-Use Backlog: {len(models)} untested Card(s) gefunden")
    for mid, dname in models:
        print(f"      • {dname}  ({mid})")
    if unreachable:
        print(f"   ⚠️  {len(unreachable)} untested Card(s) sind aktuell nicht testbar:")
        print("      Hinweis: 'ollama_model_not_installed:*' bedeutet: lokales Ollama-Modell wurde entfernt oder ist nicht mehr installiert.")
        print("      (Also nicht API/Netzwerk, sondern fehlendes lokales Modellartefakt.)")
        for mid, dname, reason in unreachable:
            print(f"      ✗ {dname}  ({mid})  →  {reason}")
    if not testable:
        print("   ⏭️  Keine testbaren Modelle — überspringe Subprocess.")
        # Report trotzdem schreiben (Diagnose)
        _write_unreachable_report(unreachable, testable, len(models))
        return True  # kein Fehler — alle untested sind dokumentiert unerreichbar

    # Unreachables-Report schreiben (auch wenn welche testbar sind)
    report_path = _write_unreachable_report(unreachable, testable, len(models))
    if report_path:
        print(f"   📝 Unreachables-Report: {report_path.relative_to(ROOT_DIR)}")

    cmd = [
        sys.executable, str(script),
        "--models", ",".join(mid for mid, _ in testable),
        "--mcp-mode", mcp_mode,
    ]

    summary_dir = ROOT_DIR / "outputs" / "runs" / "dispatch_summaries"
    summary_dir.mkdir(parents=True, exist_ok=True)
    summary_path = summary_dir / "tooluse_backlog_dispatch.json"
    cmd += ["--summary-json", str(summary_path)]

    if force:
        cmd.append("--force")
    if silent:
        cmd.append("--silent")
    print(
        f"   → Delegiere {len(testable)} testbare Modell(e) an run_tooluse_benchmark.py "
        f"(MCP={mcp_mode}, force={force})"
    )
    try:
        result = subprocess.run(cmd, cwd=str(ROOT_DIR), check=False)
    except KeyboardInterrupt:
        print("⛔  Abbruch durch Benutzer (Tool-Use Backlog).")
        raise

    summary = _read_json_summary(summary_path, "Tool-Use-Dispatch-Summary")
    if summary:
        print(
            "   ℹ️ Tool-Use-Dispatch-Summary: "
            f"status={summary.get('status', 'unknown')} "
            f"ok={summary.get('models_successful', '?')} "
            f"failed={summary.get('models_failed', '?')}"
        )
    return result.returncode == 0


def run_llamacpp_batch(
    modules: List[Dict[str, Any]],
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


def run_local_batch(
    modules: List[Dict[str, Any]],
    validator: ConfigValidator,
    force: bool = False,
    audit_mode: bool = False,
    mcp_mode: str = "live",
) -> None:
    # pylint: disable=unused-argument
    ollama_cfg = validator.config.get("providers", {}).get("local", {}).get("ollama_local", {})
    if not ollama_cfg.get("enabled", False):
        print("⏭️  Ollama local Provider deaktiviert — überspringe.")
        return

    ollama_path = shutil.which("ollama")
    if not ollama_path:
        # Kein Ollama installiert — explizit melden (kein stiller Fallback)
        print("⏭️  Überspringe lokale Benchmarks: 'ollama' Binary nicht im PATH.")
        return

    print("\n🤖  [1/2] LOKALE MODELLE (OLLAMA)")
    print(f"{'=' * 40}")

    if not check_ollama_status():
        print("⏭️  Überspringe lokale Benchmarks, da Ollama nicht läuft.")
        return

    runner = UnifiedBenchmarkRunner(force=force, audit_mode=audit_mode)

    # Cache laden (bereits erledigte Tests)
    csv_path = Path(validator.config.get("output", {}).get("local_models_csv", "benchmark_scores/local_models_benchmark.csv"))
    existing_tests = get_existing_results(csv_path, force=force)

    configured_model_ids = _extract_config_model_ids(ollama_cfg.get("models", []))
    auto_discover = bool(ollama_cfg.get("auto_discover", True))

    if configured_model_ids and not auto_discover:
        suitable_models = [m for m in configured_model_ids if is_model_suitable_for_benchmark(m)]
    else:
        try:
            all_models = [m["name"] for m in get_ollama_models_info()]
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"❌ Fehler beim Laden der Modell-Liste: {e}")
            return

        suitable_models = [m for m in all_models if is_model_suitable_for_benchmark(m)]

    if not suitable_models:
        print("⚠️  Keine geeigneten lokalen Modelle gefunden.")
        return

    print(f"Gefundene Modelle: {len(suitable_models)}")
    print(f"Liste: {', '.join(suitable_models)}\n")
    print(f"Ignoriere bereits vorhandene Ergebnisse in: {csv_path}\n")

    try:
        for i, model in enumerate(suitable_models, 1):
            print(f"\n➡️  MOD [Lokal {i}/{len(suitable_models)}]: {model}")
            had_new_results = False
            for module in modules:
                had_new_results |= _run_module_for_model(
                    runner, model, module, existing_tests,
                    force=force, audit=audit_mode, mcp_mode=mcp_mode,
                )
    except KeyboardInterrupt:
        print("\n⛔  Abbruch durch Benutzer.")
        sys.exit(1)


def run_commercial_batch(
    modules: List[Dict[str, Any]],
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

    # Provider iterieren
    providers_config = validator.config.get("providers", {}).get("commercial", {})

    active_providers = {
        k: v for k, v in providers_config.items() if v.get("enabled", False)
    }

    # Filter out providers without API Key in environment
    valid_providers = {}
    for k, v in active_providers.items():
        # Some providers might not define env_var (e.g. if they are fake ones), but standard ones do
        env_key = v.get("env_var")
        if env_key:
            if not os.getenv(env_key):
                print(
                    f"⚠️  Überspringe Provider '{k}': API Key ({env_key}) fehlt in Umgebung."
                )
                continue
        valid_providers[k] = v

    active_providers = valid_providers

    if not active_providers:
        print("⚠️  Keine validen kommerziellen Provider gefunden (Check API Keys).")
        return

    # -----------------------------------------------------
    # Check Provider Accessibility (Budget / Quota / Connectivity)
    # -----------------------------------------------------
    print("\n🔍 Prüfe API-Zugang für Provider...")
    llm_client = LLMClient(validator.config)
    accessible_providers = {}

    for k, v in active_providers.items():
        client = llm_client.clients.get(k)
        if client:
            # Formatierung verbessert: Feste Breite für Provider-Namen
            print(f"   • {k:<12} Prüfe Zugang...", end=" ", flush=True)
            if client.is_accessible():
                print("✅ OK")
                accessible_providers[k] = v
            else:
                print("❌ Fehlgeschlagen (Auth/Budget/Netzwerk). Überspringe. (Details: make logs)")
        else:
            print(
                f"   ⚠️  Provider '{k}' hat keinen dedizierten Client. Überspringe Check."
            )
            accessible_providers[k] = v

    active_providers = accessible_providers

    if not active_providers:
        print("⚠️  Keine zugänglichen kommerziellen Provider nach Prüfung gefunden.")
        return

    # Cache laden (bereits erledigte Tests)
    comm_csv = Path(validator.config.get("output", {}).get("commercial_csv", "benchmark_scores/commercial_models_benchmark.csv"))
    cloud_csv = Path(validator.config.get("output", {}).get("cloud_models_csv", "benchmark_scores/cloud_models_benchmark.csv"))

    existing_tests = get_existing_results(comm_csv, force=force)
    existing_tests.update(get_existing_results(cloud_csv, force=force))

    print(f"Ignoriere bereits vorhandene Ergebnisse ({len(existing_tests)} Einträge aus Commercial/Cloud)\n")

    # Flatten list of (provider, model_id, model_name)
    tasks = []
    for prov_key, prov_data in active_providers.items():
        for model_data in prov_data.get("models", []):
            tasks.append(
                {
                    "provider": prov_key,
                    "id": model_data["id"],
                    "name": model_data["name"],
                }
            )

    print(f"Geplante Tasks: {len(tasks)} Modell-Kombinationen")

    # Tracks providers that have been detected as quota-exhausted at runtime.
    quota_exhausted_providers: Set[str] = set()

    for i, task in enumerate(tasks, 1):
        prov_key = task["provider"]
        full_name = f"{prov_key}/{task['name']}"
        model_id = task["id"]

        if prov_key in quota_exhausted_providers:
            print(f"\n⏭️  MOD [Comm {i}/{len(tasks)}]: {full_name} — Provider '{prov_key}' quota-erschöpft, überspringe.")
            continue

        print(f"\n➡️  MOD [Comm {i}/{len(tasks)}]: {full_name}")
        had_new_results = False

        for module in modules:
            if prov_key in quota_exhausted_providers:
                print(f"   ⏭️ Bench: {module['name']} (Provider quota-erschöpft, überspringe)")
                continue

            # Filter assets
            assets_todo = _get_startable_assets(module, model_id, existing_tests)

            if not assets_todo:
                print(f"   ✓ Bench: {module['name']} (Bereits erledigt)")
                continue

            print(f"   📊 Bench: {module['name']} ({len(assets_todo)} neue Tests) ...")

            if _is_score_module(module):
                ok = _run_score_delegate_for_model(
                    module, model_id, force=force, audit=audit_mode
                )
                if ok:
                    had_new_results = True
                else:
                    print(
                        "   ⚠️ Score-Delegate-Run fehlgeschlagen "
                        f"(provider={prov_key}, model={model_id}, module={module['key']})"
                    )
                continue

            if module.get("delegate_script"):
                ok = _run_delegate_for_model(
                    module, model_id, force=force, audit=audit_mode, mcp_mode=mcp_mode
                )
                if ok:
                    had_new_results = True
                else:
                    print(
                        "   ⚠️ Delegate-Run fehlgeschlagen "
                        f"(provider={prov_key}, model={model_id}, module={module['key']})"
                    )
                continue

            try:
                results = runner.run_benchmark(
                    provider=prov_key, model=model_id, benchmark_info=module, assets=assets_todo
                )
                # Detect quota exhaustion via runner flag (Budget-/Quota-Fehler per-Test)
                if runner.provider_quota_exhausted:
                    print(f"   💸 Budget-/Quota-Fehler via Runner erkannt für Provider '{prov_key}'. Alle weiteren Modelle dieses Providers werden übersprungen.")
                    quota_exhausted_providers.add(prov_key)
                    runner.provider_quota_exhausted = False  # Reset für nächsten Provider

                if results:
                    # Fallback-Erkennung: alle Ergebnisse haben 0 Token und 0% Score
                    all_zero_tokens = all(r.get("tokens_used", 0) == 0 for r in results)
                    all_zero_scores = all(r.get("percentage", 0) == 0.0 for r in results)
                    if all_zero_tokens and all_zero_scores and len(results) > 0 and prov_key not in quota_exhausted_providers:
                        print(f"   💸 Quota-Erschöpfung (Fallback-Erkennung) für Provider '{prov_key}'. Alle weiteren Modelle dieses Providers werden übersprungen.")
                        quota_exhausted_providers.add(prov_key)

                    runner.save_results(results)
                    had_new_results = True
            except KeyboardInterrupt:
                print("\n⛔  Abbruch durch Benutzer.")
                sys.exit(1)
            except Exception as e:  # pylint: disable=broad-exception-caught
                print(f"   ❌ Fehler: {e}")


def main():
    """Main entry point."""
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
    args = parser.parse_args()

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

    validator = ConfigValidator()

    # Module laden
    modules = get_all_modules(validator)

    # Filter modules if requested
    if args.modules:
        wanted = [m.strip() for m in args.modules.split(",")]
        # Wir filtern die geladenen Module anhand des Keys
        filtered = [m for m in modules if m["key"] in wanted]
        if len(filtered) < len(wanted):
            found_keys = [m["key"] for m in filtered]
            missing = set(wanted) - set(found_keys)
            print(f"⚠️  Warnung: Gewünschte Module nicht gefunden/aktiviert: {missing}")
        modules = filtered

    if not modules:
        print("❌ Keine Module konfiguriert/aktiviert.")
        sys.exit(1)

    print(f"📋 Aktivierte Module ({len(modules)}):")
    for m in modules:
        print(f"   - {m['name']} ({m['key']})")

    # === 0. Tool-Use Backlog: untested Cards erkennen und auffüllen =============
    # Metaskript-Funktion: erkennt Cards mit supports_tool_use="untested" und
    # delegiert an run_tooluse_benchmark.py. Läuft VOR den regulären Benchmarks,
    # weil Tool-Use-Tests MCP benötigen und unabhängig vom normalen Loop sind.
    # FORCE steuert: nur untested (nie true-Cards neu testen — wer FORCE will,
    # nutzt make benchmark-tooluse-force).
    untested_cards = _collect_untested_tooluse_cards()
    if untested_cards:
        print("\n🔧 [0/2] TOOL-USE BACKLOG (untested Cards)")
        print(f"{'=' * 40}")
        stop_llamacpp_provider_server(validator.config)
        aborted = False
        try:
            _run_untested_tooluse_models(
                untested_cards,
                mcp_mode=args.mcp_mode,
                force=args.force,
                silent=not args.audit,
            )
        except KeyboardInterrupt:
            aborted = True
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"   ⚠️  Tool-Use-Backlog fehlgeschlagen (nicht fatal): {e}")
        if aborted:
            sys.exit(1)
    else:
        print("\n🔧 [0/2] TOOL-USE BACKLOG: keine untested Cards — nichts zu tun.")
    # ============================================================================

    aborted = False
    try:
        # 1. Lokale Modelle (Ollama)
        try:
            run_local_batch(modules, validator, force=args.force, audit_mode=args.audit, mcp_mode=args.mcp_mode)
        except (KeyboardInterrupt, SystemExit):
            print("\n⛔  Abbruch durch Benutzer (Lokale Modelle).")
            aborted = True

        # 1b. Lokale Modelle (llama.cpp)
        if not aborted:
            try:
                run_llamacpp_batch(modules, validator, force=args.force, audit_mode=args.audit, mcp_mode=args.mcp_mode)
            except (KeyboardInterrupt, SystemExit):
                print("\n⛔  Abbruch durch Benutzer (llama.cpp).")
                aborted = True

        # 2. Kommerzielle Modelle
        if not aborted:
            try:
                run_commercial_batch(
                    modules, validator, force=args.force, audit_mode=args.audit, mcp_mode=args.mcp_mode
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
