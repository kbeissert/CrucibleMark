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
import argparse
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any, List, Dict, Set, Tuple

# Third-party imports
# pylint: disable=import-error
import yaml  # noqa: E402
import pandas as pd  # noqa: E402

try:
    from dotenv import load_dotenv
except ImportError:
    # pylint: disable=unused-argument
    def load_dotenv():
        pass


# pylint: enable=import-error

# Load environment variables
load_dotenv()

# Pfad setup
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Local imports
# pylint: disable=import-error, wrong-import-position
from scripts.core.run_local_benchmark import LocalBenchmarkRunner  # noqa: E402
from scripts.core.run_commercial_benchmark import (
    CommercialBenchmarkRunner,
)  # noqa: E402
from scripts.core.generate_leaderboard import main as gen_leaderboard  # noqa: E402
from utils.config_validator import ConfigValidator  # noqa: E402
from utils.model_utils import is_model_suitable_for_benchmark  # noqa: E402
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
            [ollama_path, "list"], capture_output=True, check=True, timeout=5
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


def get_existing_results(csv_path: Path, force: bool = False) -> Set[Tuple[str, str]]:
    """Lädt Set von (Model, AssetID) für bereits existierende Tests."""
    cache = set()
    if force:
        return cache  # Force Mode: Ignoriere existierende Ergebnisse

    if csv_path.exists():
        try:
            df = pd.read_csv(csv_path)
            # Relevante Spalten prüfen
            required = {"model", "asset_id"}
            if required.issubset(df.columns):
                # Wir merken uns (Model, AssetID) als erledigt
                for _, row in df.iterrows():
                    # Wenn Status vorhanden, prüfen wir auf success
                    # (Fehlgeschlagene Tests werden wiederholt)
                    if "status" in df.columns:
                        status = str(row.get("status", "")).lower()
                        if status != "success":
                            continue  # Skip failed tests (retry)

                    cache.add((str(row["model"]), str(row["asset_id"])))
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"⚠️ Warnung beim Lesen von {csv_path}: {e}")
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
            }
        )
    return modules


def _get_startable_assets(
    module: Dict[str, Any], model: str, existing_tests: Set[Tuple[str, str]]
) -> List[Path]:
    """Ermittelt Asset-Pfade, die für dieses Modell noch nicht getestet wurden."""
    assets_path = module["path"]

    # -------------------------------------------------------
    # SPECIAL HANDLING FOR BATCH MODULES (e.g. Political Compass)
    # -------------------------------------------------------
    # Batch-Module (wie Political Compass) erzeugen oft nur EINEN Eintrag (Aggregiert).
    # Da ein Re-Run sehr teuer ist (81+ Fragen), überspringen wir, wenn das Aggregat da ist.
    # Wir prüfen hier NICHT auf Aktualität (Datum) oder Vollständigkeit der Assets.
    if (
        module.get("execution_mode") == "batch"
        or module.get("key") == "political_compass"
    ):
        batch_id = "political_compass_v3"
        if (model, batch_id) in existing_tests:
            # Optional: Man könnte hier loggen, dass geskippt wird.
            # Da dies für jedes Modell passiert, halten wir es still oder loggen einmalig außen.
            return []
    # -------------------------------------------------------

    # Der Runner hat Methode zum Finden, aber wir brauchen den Pfad
    # Da Runner interne Methoden hat, rufen wir hier eine Hilfsfunktion nach
    # Aber wir können auch einfach globben, da wir den Pfad haben.
    # Da LocalBenchmarkRunner assets_path als String/Path erwartet:
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

            if (model, asset_id) in existing_tests:
                continue

            assets_todo.append(asset_f)
        except (OSError, yaml.YAMLError):
            # Fallback: Einfach ausführen wenn Parse Error
            assets_todo.append(asset_f)

    return assets_todo


def _run_module_for_model(
    runner: LocalBenchmarkRunner,
    model: str,
    module: Dict[str, Any],
    existing_tests: Set[Tuple[str, str]],
) -> None:
    """Führt ein einzelnes Modul für ein einzelnes Modell aus."""
    assets_todo = _get_startable_assets(
        module=module, model=model, existing_tests=existing_tests
    )
    # Note: assets_todo is calculated but currently the LocalBenchmarkRunner
    # runs ALL assets in the folder. So filtering here serves mainly for info logging
    # unless we patch the runner. The original code just logged.

    if not assets_todo:
        # If we calculate that everything is done, we could skip calling the runner.
        msg = f"   ✓ Bench: {module['name']} (Alle Tests bereits vorhanden)"
        if module.get("key") == "political_compass":
            msg += " [Batch-Mode Skip]"
        print(msg)
        return

    print(f"   📊 Bench: {module['name']} ({len(assets_todo)} neue Tests) ...")

    try:
        # Pass filtered assets (assets_todo) to evita re-running existing tests
        results = runner.run_benchmark(model, module, assets=assets_todo)
        if results:
            runner.save_results(results)
    except KeyboardInterrupt:

        print("\n⛔  Abbruch durch Benutzer.")
        sys.exit(1)
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"   ❌ Fehler: {e}")


def run_local_batch(
    modules: List[Dict[str, Any]], validator: ConfigValidator, force: bool = False
) -> None:
    """Batch-Run für alle lokalen Ollama-Modelle."""
    # pylint: disable=unused-argument
    print("\n🤖  [1/2] LOKALE MODELLE (OLLAMA)")
    print(f"{'=' * 40}")

    if not check_ollama_status():
        print("⏭️  Überspringe lokale Benchmarks, da Ollama nicht läuft.")
        return

    runner = LocalBenchmarkRunner()

    # Cache laden (bereits erledigte Tests)
    csv_path = Path("benchmark_scores/local_models_benchmark.csv")
    existing_tests = get_existing_results(csv_path, force=force)

    # Modelle holen
    try:
        all_models = runner.get_ollama_models()
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

    for i, model in enumerate(suitable_models, 1):
        print(f"\n➡️  MOD [Lokal {i}/{len(suitable_models)}]: {model}")
        for module in modules:
            # Fix call validation (pylint sometimes confused by dynamic args if passed wrong)
            _run_module_for_model(runner, model, module, existing_tests)


def run_commercial_batch(
    modules: List[Dict[str, Any]], validator: ConfigValidator, force: bool = False
) -> None:
    """Batch-Run für alle konfigurierten kommerziellen Modelle."""
    print("\n🏢  [2/2] KOMMERZIELLE MODELLE (API)")
    print(f"{'=' * 40}")

    runner = CommercialBenchmarkRunner()
    runner.mode = "test"
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
                print("❌ Fehlgeschlagen (Kein Zugriff/Budget). Überspringe.")
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
    # Check BOTH commercial CSV and golden standard CSV
    comm_csv = Path("benchmark_scores/commercial_models_benchmark.csv")
    gold_csv = Path("benchmark_scores/golden_standard_benchmark.csv")

    existing_tests = get_existing_results(comm_csv, force=force)
    # Merge with golden standards if they exist (since they are also valid test runs)
    if gold_csv.exists():
        existing_gold = get_existing_results(gold_csv, force=force)
        existing_tests.update(existing_gold)

    print(f"Ignoriere bereits vorhandene Ergebnisse ({len(existing_tests)} Einträge)\n")

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

    for i, task in enumerate(tasks, 1):
        full_name = f"{task['provider']}/{task['name']}"
        model_id = task["id"]

        print(f"\n➡️  MOD [Comm {i}/{len(tasks)}]: {full_name}")

        for module in modules:
            # Filter assets
            assets_todo = _get_startable_assets(module, model_id, existing_tests)

            if not assets_todo:
                print(f"   ✓ Bench: {module['name']} (Bereits erledigt)")
                continue

            print(f"   📊 Bench: {module['name']} ({len(assets_todo)} neue Tests) ...")
            try:
                results = runner.run_benchmark(
                    task["provider"], model_id, module, assets=assets_todo
                )
                if results:
                    runner.save_results(results)
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
    args = parser.parse_args()

    print(f"{'#' * 60}")
    print("🤖  CRUCIBLE AUTOMATIC BENCHMARK")
    print("    Füllt automatisch fehlende Benchmarks auf.")
    if args.force:
        print("    ⚠️  FORCE MODE: Alle Tests laufen erneut!")
    if args.modules:
        print(f"    🎯 FOKUS: Nur Module '{args.modules}'")
    print(f"{'#' * 60}\n")

    # Pre-Check Ollama
    if not check_ollama_status():
        print("⚠️  WARNUNG: Lokale Tests werden übersprungen.")

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

    # 1. Lokale Modelle
    try:
        run_local_batch(modules, validator, force=args.force)
    except KeyboardInterrupt:
        print("\n⛔  Abbruch durch Benutzer.")
        sys.exit(1)

    # 2. Kommerzielle Modelle
    try:
        run_commercial_batch(modules, validator, force=args.force)
    except KeyboardInterrupt:
        print("\n⛔  Abbruch durch Benutzer.")
        sys.exit(1)

    print("\n\n✅  AUTOMATIC RUN COMPLETED.")
    print("    Ergebnisse wurden in die CSV-Dateien gespeichert.")
    print("    Generiere Leaderboard...")

    # Am Ende das Leaderboard aktualisieren
    try:
        gen_leaderboard(print_table=True)
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"⚠️ Leaderboard konnte nicht generiert werden: {e}")


if __name__ == "__main__":
    main()
