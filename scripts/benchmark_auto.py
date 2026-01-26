#!/usr/bin/env python3
"""
🌙 CRUCIBLE AUTOMATED BENCHMARK 🌙
===================================
Führt ALLE aktivierten Benchmarks für ALLE verfügbaren Modelle (Lokal & Kommerziell) aus.
Gedacht für langlaufende Batch-Jobs (z.B. über Nacht).

Usage:
    python scripts/benchmark_auto.py
"""

import sys
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any, List, Dict, Set, Tuple

# Third-party imports
# pylint: disable=import-error
import yaml
import pandas as pd
# pylint: enable=import-error

# Pfad setup
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Local imports
# pylint: disable=import-error, wrong-import-position
from scripts.run_local_benchmark import LocalBenchmarkRunner
from scripts.run_commercial_benchmark import CommercialBenchmarkRunner
from scripts.generate_leaderboard import main as gen_leaderboard
from utils.config_validator import ConfigValidator
from utils.model_utils import is_model_suitable_for_benchmark
# pylint: enable=import-error, wrong-import-position

# Logging Setup
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("overnight")


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


def get_existing_results(csv_path: Path) -> Set[Tuple[str, str]]:
    """Lädt Set von (Model, AssetID) für bereits existierende Tests."""
    cache = set()
    if csv_path.exists():
        try:
            df = pd.read_csv(csv_path)
            # Relevante Spalten prüfen
            required = {"model", "asset_id"}
            if required.issubset(df.columns):
                # Wir merken uns (Model, AssetID) als erledigt
                for _, row in df.iterrows():
                    cache.add((str(row["model"]), str(row["asset_id"])))
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"⚠️ Warnung beim Lesen von {csv_path}: {e}")
    return cache


def get_all_modules(validator: ConfigValidator) -> List[Dict[str, Any]]:
    """Extrahiert alle aktivierten Module aus der Config."""
    modules = []
    if "modules" in validator.config:
        for key, mod in validator.config["modules"].items():
            if mod.get("enabled", False):
                modules.append(
                    {
                        "key": key,
                        "name": mod["name"],
                        "path": f"{mod['path']}/assets",
                        "module_path": mod["path"],  # Wichtig für Module Loader
                        "test_class": mod.get("test_class", "CodeQualityTest"),
                        "description": mod["description"],
                    }
                )
    return modules


def _get_startable_assets(
    module: Dict[str, Any], model: str, existing_tests: Set[Tuple[str, str]]
) -> List[Path]:
    """Ermittelt Asset-Pfade, die für dieses Modell noch nicht getestet wurden."""
    assets_path = module["path"]
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
        # But since the runner runs everything, skipping call prevents redundant runs.
        # So this IS an optimization if 100% are done.
        print(f"   ✓ Bench: {module['name']} (Alle Tests bereits vorhanden)")
        return

    print(f"   📊 Bench: {module['name']} ({len(assets_todo)} neue Tests) ...")

    try:
        # Der Runner führt intern alle aus. Das ist aktuell limitation, aber ok.
        results = runner.run_benchmark(model, module)
        if results:
            runner.save_results(results)
    except KeyboardInterrupt:
        print("\n⛔  Abbruch durch Benutzer.")
        sys.exit(1)
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"   ❌ Fehler: {e}")


def run_local_batch(modules: List[Dict[str, Any]], validator: ConfigValidator) -> None:
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
    existing_tests = get_existing_results(csv_path)

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
    modules: List[Dict[str, Any]], validator: ConfigValidator
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

    if not active_providers:
        print("⚠️  Keine aktiven kommerziellen Provider gefunden.")
        return

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
        print(f"\n➡️  MOD [Comm {i}/{len(tasks)}]: {full_name}")

        for module in modules:
            print(f"   📊 Bench: {module['name']} ...")
            try:
                # Assuming run_benchmark signature is (provider, model_id, module_config)
                results = runner.run_benchmark(task["provider"], task["id"], module)
                if results:
                    runner.save_results(results)
            except KeyboardInterrupt:
                print("\n⛔  Abbruch durch Benutzer.")
                sys.exit(1)
            except Exception as e:  # pylint: disable=broad-exception-caught
                print(f"   ❌ Fehler: {e}")


def main():
    """Main entry point."""
    print(f"{'#' * 60}")
    print("🌙  CRUCIBLE AUTOMATED BENCHMARK")
    print("    Führt alle Benchmarks auf allen Modellen aus.")
    print(f"{'#' * 60}\n")

    # Pre-Check Ollama
    if not check_ollama_status():
        print("⚠️  WARNUNG: Lokale Tests werden übersprungen.")

    validator = ConfigValidator()

    # Module laden
    modules = get_all_modules(validator)
    if not modules:
        print("❌ Keine Module konfiguriert/aktiviert.")
        sys.exit(1)

    print(f"📋 Aktivierte Module ({len(modules)}):")
    for m in modules:
        print(f"   - {m['name']} ({m['key']})")

    # 1. Lokale Modelle
    run_local_batch(modules, validator)

    # 2. Kommerzielle Modelle
    run_commercial_batch(modules, validator)

    print("\n\n✅  OVERNIGHT RUN COMPLETED.")
    print("    Ergebnisse wurden in die CSV-Dateien gespeichert.")
    print("    Generiere Leaderboard...")

    # Am Ende das Leaderboard aktualisieren
    try:
        gen_leaderboard(print_table=True)
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"⚠️ Leaderboard konnte nicht generiert werden: {e}")


if __name__ == "__main__":
    main()
