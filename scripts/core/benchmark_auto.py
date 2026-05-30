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
import time
import argparse
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any, List, Dict, Set, Tuple

# Third-party imports
# pylint: disable=import-error
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

# Pfad setup
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Local imports
# pylint: disable=import-error, wrong-import-position
from scripts.core.unified_runner import UnifiedBenchmarkRunner  # noqa: E402
from scripts.core.generate_leaderboard import main as gen_leaderboard  # noqa: E402
from utils.config_validator import ConfigValidator  # noqa: E402
from utils.model_utils import is_model_suitable_for_benchmark, get_ollama_models_info  # noqa: E402
from utils.llm_client import LLMClient  # noqa: E402
from utils.module_registry import get_active_modules  # noqa: E402

# pylint: enable=import-error, wrong-import-position

# Logging Setup
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("auto_benchmark")


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



def _strip_hf_prefix(model_id: str) -> str:
    """Normalisiert HF-URL-Präfix: 'hf.co/user/ModelName:tag' → 'ModelName:tag'.

    Ollama listet HF-Modelle manchmal mit vollem Pfad, die CSV speichert nur den
    letzten Bestandteil — beide Formen müssen im Cache-Lookup als identisch gelten.
    """
    import re as _re_hf
    return _re_hf.sub(r'^hf\.co/[^/]+/', '', model_id)


def get_existing_results(csv_path: Path, force: bool = False) -> Set[Tuple[str, str]]:
    """Lädt Set von (Model, AssetID) für bereits existierende Tests über alle Provider-CSVs hinweg."""
    cache = set()
    if force:
        return cache  # Force Mode: Ignoriere existierende Ergebnisse

    # Wir checken ab sofort ALLE Haupt-CSVs (3-CSV Architektur)
    validator = ConfigValidator()
    output_cfg = validator.config.get("output", {})

    csv_paths = [
        Path(output_cfg.get("local_models_csv", "benchmark_scores/local_models_benchmark.csv")),
        Path(output_cfg.get("cloud_models_csv", "benchmark_scores/cloud_models_benchmark.csv")),
        Path(output_cfg.get("commercial_models_csv", "benchmark_scores/commercial_models_benchmark.csv"))
    ]

    for path in csv_paths:
        if path.exists():
            try:
                df = pd.read_csv(path)
                # Relevante Spalten prüfen
                required = {"model", "asset_id"}
                if required.issubset(df.columns):
                    # Wir merken uns (Model, AssetID) als erledigt
                    # Status-Werte die als "abgeschlossen" gelten und NICHT wiederholt werden:
                    # success            — reguläres Ergebnis
                    # language_mismatch  — Modell hat bewusst in falscher Sprache geantwortet (valides Ergebnis)
                    # truncated          — Antwort wurde abgeschnitten (valides, bewertetes Ergebnis)
                    # refusal            — Modell hat die Aufgabe verweigert (refusal_flag, kein Re-Run)
                    # Nur technische Fehler (error, api_error, timeout) werden wiederholt.
                    COMPLETED_STATUSES = {"success", "language_mismatch", "truncated", "refusal"}
                    for _, row in df.iterrows():
                        if "status" in df.columns:
                            status = str(row.get("status", "")).lower()
                            if status not in COMPLETED_STATUSES:
                                continue  # Technischer Fehler – wiederholen

                        model_str = str(row["model"])
                        asset_str = str(row["asset_id"])
                        cache.add((model_str, asset_str))
                        # Auch normalisierte Form ohne HF-Präfix speichern, damit
                        # 'hf.co/bartowski/X' und 'X' als dieselben Ergebnisse gelten.
                        stripped = _strip_hf_prefix(model_str)
                        if stripped != model_str:
                            cache.add((stripped, asset_str))
            except Exception as e:  # pylint: disable=broad-exception-caught
                print(f"⚠️ Warnung beim Lesen von {path}: {e}")

    # Zusätzlich Batch-Mode CSVs (z.B. Political Compass) zur Vermeidung von Re-Runs einlesen
    pc_csv = Path("benchmark_scores/political_compass_leaderboard.csv")
    if pc_csv.exists():
        try:
            df_pc = pd.read_csv(pc_csv)
            if "model" in df_pc.columns:
                for _, row in df_pc.iterrows():
                    model_str = str(row["model"])
                    cache.add((model_str, "political_compass_v3"))
                    stripped = _strip_hf_prefix(model_str)
                    if stripped != model_str:
                        cache.add((stripped, "political_compass_v3"))
        except Exception as e:
            print(f"⚠️ Warnung beim Lesen von {pc_csv}: {e}")

    return cache


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
    """Ermittelt Asset-Pfade, die für dieses Modell noch nicht getestet wurden."""
    assets_path = module["path"]

    # -------------------------------------------------------
    # CARD-BASED SKIP (skip_if_card_false)
    # -------------------------------------------------------
    # Wenn die Model Card einen Key mit Wert False trägt, wird das Modul
    # für dieses Modell komplett übersprungen — kein Re-Run nötig.
    # Beispiel: supports_tool_use: false → Tooluse-Assets werden nicht ausgeführt.
    skip_card_key = module.get("skip_if_card_false")
    if skip_card_key:
        import json as _json
        from utils.model_utils import _find_card as _fc
        _card_dir = ROOT_DIR / "benchmark_scores" / "model_cards"
        _card_path = _fc(model, card_dir=_card_dir)
        if _card_path.exists():
            _card = _json.loads(_card_path.read_text())
            if _card.get(skip_card_key) is False:
                print(f"   ⏩ Bench: {module['name']} ({skip_card_key}=false in Card — übersprungen)")
                return []
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
        import re as _re_auto
        model_normalized = _re_auto.sub(r"-\d{8}$", "", model)
        model_normalized = _re_auto.sub(r"-(0[1-9]|1[0-2])\d{2}$", "", model_normalized)
        model_hf_stripped = _strip_hf_prefix(model)
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

            model_hf_stripped = _strip_hf_prefix(model)
            if (model, asset_id) in existing_tests or (model_hf_stripped, asset_id) in existing_tests:
                continue

            assets_todo.append(asset_f)
        except (OSError, yaml.YAMLError):
            # Fallback: Einfach ausführen wenn Parse Error
            assets_todo.append(asset_f)

    return assets_todo


def _run_delegate_for_model(
    module: Dict[str, Any],
    model: str,
    force: bool = False,
    audit: bool = True,
    mcp_mode: str = "live",
) -> bool:
    """Delegiert die Ausführung eines Moduls an das zuständige Fachscript.

    Das Fachscript verantwortet seinen eigenen Lifecycle (inkl. MCP falls nötig).
    Returns True wenn der Prozess erfolgreich beendet wurde (rc == 0).
    """
    script = ROOT_DIR / module["delegate_script"]
    extra = list(module.get("delegate_extra_args", []) or [])
    cmd = [sys.executable, str(script)] + extra + ["--model", model]
    if force:
        cmd.append("--force")
    if not audit:
        cmd.append("--silent")
    if module.get("requires_mcp"):
        cmd += ["--mcp-mode", mcp_mode]
    result = subprocess.run(cmd, cwd=str(ROOT_DIR), check=False)
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

    if module.get("delegate_script"):
        return _run_delegate_for_model(module, model, force=force, audit=audit, mcp_mode=mcp_mode)

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


def run_llamacpp_batch(
    modules: List[Dict[str, Any]],
    validator: ConfigValidator,
    force: bool = False,
    audit_mode: bool = False,
    mcp_mode: str = "live",
) -> None:
    """Batch-Run für alle konfigurierten llama.cpp-Modelle (explizite Liste, kein auto_discover).

    Startet den llama.cpp-Server für das erste Modell, führt alle Module aus,
    swappt dann auf das nächste Modell und fährt den Server nach dem letzten Modell herunter.
    """
    print("\n🖥️  [1b/2] LOKALE MODELLE (LLAMA.CPP)")
    print(f"{'=' * 40}")

    prov_cfg = validator.config.get("providers", {}).get("local", {}).get("llamacpp", {})
    if not prov_cfg.get("enabled", False):
        print("⏭️  llama.cpp Provider deaktiviert — überspringe.")
        return

    models_list = prov_cfg.get("models", [])
    if not models_list:
        print("⚠️  Keine llama.cpp-Modelle konfiguriert.")
        return

    # Cache: bereits erledigte Tests aus local_models_benchmark.csv laden
    csv_path = Path(
        validator.config.get("output", {}).get("local_models_csv", "benchmark_scores/local_models_benchmark.csv")
    )
    existing_tests = get_existing_results(csv_path, force=force)

    runner = UnifiedBenchmarkRunner(audit_mode=audit_mode)

    # Verwende den runner-internen LlamaCppClient (shared state → kein Doppel-Swap)
    lcpp_client = runner.client.clients.get("llamacpp")
    if lcpp_client is None:
        print("❌ LlamaCppClient nicht im Client-Registry gefunden.")
        return

    model_ids = [m["id"] for m in models_list if m.get("id")]

    print(f"Konfigurierte Modelle: {len(model_ids)}")
    print(f"Liste: {', '.join(model_ids)}\n")
    print(f"Ignoriere bereits vorhandene Ergebnisse in: {csv_path}\n")

    # Prophylaktisch alle laufenden llama-server stoppen (Port 1234 Standard + Port 1235)
    # damit kein alter Prozess den Start blockiert oder Token-Rates verfälscht.
    print("   🧹 Stoppe laufende llama-server (prophylaktisch) ...")
    stop_cmd = prov_cfg.get("server_stop_cmd", "pkill -f llama-server")
    subprocess.run(stop_cmd, shell=True, check=False, capture_output=True)
    time.sleep(3)

    try:
        for i, model_id in enumerate(model_ids, 1):
            print(f"\n➡️  MOD [llama.cpp {i}/{len(model_ids)}]: {model_id}")

            # Server für dieses Modell starten / umschalten
            if not lcpp_client.start_server(model_id):
                print(f"   ❌ Server für '{model_id}' konnte nicht gestartet werden — überspringe.")
                continue

            had_new_results = False
            for module in modules:
                had_new_results |= _run_module_for_model(
                    runner, model_id, module, existing_tests,
                    force=force, audit=audit_mode, mcp_mode=mcp_mode,
                    provider="llamacpp",
                )
            if had_new_results:
                try:
                    gen_leaderboard(print_table=False)
                except Exception as e:  # pylint: disable=broad-exception-caught
                    print(f"   ⚠️ Leaderboard-Update fehlgeschlagen: {e}")

    except KeyboardInterrupt:
        print("\n⛔  Abbruch durch Benutzer.")
    finally:
        print("\n   🛑 Stoppe llama.cpp Server...")
        lcpp_client.stop_server()
        if sys.exc_info()[0] is KeyboardInterrupt:
            sys.exit(1)


def run_local_batch(
    modules: List[Dict[str, Any]],
    validator: ConfigValidator,
    force: bool = False,
    audit_mode: bool = False,
    mcp_mode: str = "live",
) -> None:
    # pylint: disable=unused-argument
    ollama_path = shutil.which("ollama")
    if not ollama_path:
        # Kein Ollama installiert — Sektion still überspringen
        return

    print("\n🤖  [1/2] LOKALE MODELLE (OLLAMA)")
    print(f"{'=' * 40}")

    if not check_ollama_status():
        print("⏭️  Überspringe lokale Benchmarks, da Ollama nicht läuft.")
        return

    runner = UnifiedBenchmarkRunner(audit_mode=audit_mode)

    # Cache laden (bereits erledigte Tests)
    validator = ConfigValidator()
    csv_path = Path(validator.config.get("output", {}).get("local_models_csv", "benchmark_scores/local_models_benchmark.csv"))
    existing_tests = get_existing_results(csv_path, force=force)

    # Modelle holen
    try:
        all_models = [m["name"] for m in get_ollama_models_info()]
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"❌ Fehler beim Laden der Modell-Liste: {e}")
        return

    # Filtern nach Benchmark-Eignung (keine Embeddings/Vision)
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
            if had_new_results:
                try:
                    gen_leaderboard(print_table=False)
                except Exception as e:  # pylint: disable=broad-exception-caught
                    print(f"   ⚠️ Leaderboard-Update fehlgeschlagen: {e}")
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

    runner = UnifiedBenchmarkRunner(audit_mode=audit_mode)
    from utils.adaptive_pause import BenchmarkMode
    runner.mode = BenchmarkMode.DEV
    runner.force = False

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

            if module.get("delegate_script"):
                ok = _run_delegate_for_model(
                    module, model_id, force=force, audit=audit_mode, mcp_mode=mcp_mode
                )
                if ok:
                    had_new_results = True
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

        if had_new_results:
            try:
                gen_leaderboard(print_table=False)
            except Exception as e:  # pylint: disable=broad-exception-caught
                print(f"   ⚠️ Leaderboard-Update fehlgeschlagen: {e}")


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
        print("    Generiere Leaderboard aus den neuen CSV-Daten...")

        # Am Ende das Leaderboard IMMER aktualisieren (auch bei Abbruch)
        try:
            df = gen_leaderboard(print_table=not aborted)
            if aborted and df is not None:
                print("\n📊 Kurzübersicht Leaderboard:")
                if "Model Name" in df.columns and "Total Score" in df.columns:
                    print(f"   {'Modell':<30} | Score")
                    print("   " + "-" * 40)
                    for _, row in df.iterrows():
                        print(f"   {str(row['Model Name'])[:30]:<30} | {row['Total Score']}")
                else:
                    print(f"   (Header Fehler. Verfügbar: {', '.join(df.columns[:5])})")

        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"⚠️ Leaderboard konnte nicht generiert werden: {e}")

        if aborted:
            sys.exit(1)


if __name__ == "__main__":
    main()
