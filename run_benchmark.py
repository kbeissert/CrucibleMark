#!/usr/bin/env python3
"""
CrucibleMark - Global Benchmark Runner
===========================================

Interaktives Benchmark-Script mit Modul- und Provider-Auswahl.
Lädt Test-Module dynamisch aus benchmark_config.yaml.

Usage:
    python run_benchmark.py                    # Interaktiv
    python run_benchmark.py --provider local   # Nur lokale Modelle
    python run_benchmark.py --module code_quality --provider commercial
"""

import argparse
import importlib.util
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from utils.model_utils import (
    get_ollama_models_info,
    resolve_provider,
)
from utils.module_loader import load_test_class
from utils.benchmark_utils import select_from_list
from utils.similarity import SemanticSimilarity
from utils.config_validator import ConfigValidator
from utils.module_registry import load_module_config, get_active_modules

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",  # Simple format for CLI output
)
logger = logging.getLogger(__name__)

# Suppress verbose HTTP logging from libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# Constants
DEFAULT_CONFIG_PATH = "benchmark_config.yaml"

# Pre-import runners to fail fast on import errors
try:
    from scripts.core.run_local_benchmark import LocalBenchmarkRunner
    from scripts.core.run_commercial_benchmark import CommercialBenchmarkRunner
except ImportError as e:
    logger.error("Error importing benchmark runners: %s", e)
    sys.exit(1)


@dataclass
class BenchmarkRunConfig:
    """Konfiguration für einen Benchmark-Lauf."""

    module_name: Optional[str] = None
    provider_type: Optional[str] = None
    model_name: Optional[str] = None
    run_all: bool = False
    num_runs: int = 1
    force: bool = False


class BenchmarkRunner:
    """Globaler Benchmark-Runner mit dynamischem Modul-Loading."""

    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        self.config_path = Path(config_path)
        # Use centralized config validation
        self.validator = ConfigValidator(config_path)
        self.config = self.validator.config

        # Check for optional dependencies at startup
        SemanticSimilarity.check_availability()

    def get_enabled_modules(self) -> dict[str, Any]:
        """Gibt alle aktivierten Module zurück, angereichert mit Metadaten (SSOT)."""
        active_list = get_active_modules(self.config)
        result = {}
        for mod_id, meta, internal_config in active_list:
            # Merge: Registry config (path) + Internal metadata (Name, Desc)
            merged = meta.copy()
            # Module config's 'metadata' block overrides/supplements
            merged.update(internal_config.get("metadata", {}))
            # Module config's 'execution' block overrides/supplements (test_class, etc)
            merged.update(internal_config.get("execution", {}))
            
            # Ensure name defaults to ID if missing
            if "name" not in merged:
                merged["name"] = mod_id.replace("_", " ").title()

            result[mod_id] = merged
        return result

    def select_module(
        self, module_name: Optional[str] = None
    ) -> tuple[Optional[str], Optional[dict[str, Any]]]:
        """Interaktive Modul-Auswahl oder direkter Zugriff."""
        modules = self.get_enabled_modules()

        if not modules:
            raise ValueError("Keine aktivierten Module gefunden!")

        # 1. Direkter Zugriff wenn angegeben
        if module_name:
            if module_name == "all":
                return None, None  # Signal für "Alle Module"
            if module_name not in modules:
                raise ValueError(f"Modul nicht gefunden: {module_name}")
            return module_name, modules[module_name]

        # 2. Interaktive Auswahl (DRY via select_from_list)
        # Wir fügen "ALLE MODULE" als eine spezielle Option am Anfang hinzu
        items = [
            (
                "all",
                {
                    "name": "ALLE MODULE AUSFÜHREN",
                    "description": "Führt einen vollständigen Benchmark durch.",
                },
            )
        ]
        items.extend(list(modules.items()))

        def display_mod(item):
            key, config = item
            return config["name"], config.get("description", "")

        selected = select_from_list(
            items,
            display_func=display_mod,
            prompt="Wähle ein Modul",
            title="TEST-MODULE"
        )

        if selected:
            key, config = selected
            if key == "all":
                print("✓  Alle Module ausgewählt")
                return None, None
            print(f"✓  {config['name']}")
            return key, config
            
        sys.exit(0)

    def select_provider(self, provider_type: Optional[str] = None) -> tuple[str, str]:
        """Interaktive Provider-Auswahl (commercial/local)."""
        if provider_type and provider_type in ["commercial", "local"]:
            return self._select_provider_models(provider_type)

        options = [
            ("commercial", "Kommerzielle Modelle (API) - Mistral, Claude, GPT"),
            ("local", "Lokale Modelle (Ollama) - Datenschutz, lokal gehostet"),
        ]

        selected = select_from_list(
            options,
            display_func=lambda x: x[1],
            prompt="Wähle Provider-Typ",
            title="PROVIDER"
        )

        if selected:
            print(f"✓  {selected[1].split(' - ')[0]}")
            return self._select_provider_models(selected[0])
            
        sys.exit(0)

    def _select_provider_models(self, provider_type: str) -> tuple[str, str]:
        """Wählt Provider und Modell basierend auf Typ."""
        if provider_type == "commercial":
            return self._select_commercial_model()
        return self._select_local_model()

    def _select_commercial_model(self) -> tuple[str, str]:
        """Wählt kommerzielles Modell (Mistral/Claude/GPT)."""
        commercial_config = self.config.get("providers", {}).get("commercial", {})
        models_flat = []

        for provider_key, provider_data in commercial_config.items():
            for model in provider_data.get("models", []):
                models_flat.append(
                    {
                        "provider": provider_key,
                        "provider_name": provider_data["name"],
                        "id": model["id"],
                        "name": model["name"],
                        "description": model["description"],
                    }
                )

        def display_model(m):
            return (
                f"[{m['provider_name']}] {m['name']}",
                f"{m['description']} (Model: {m['id']})"
            )

        selected = select_from_list(
            models_flat,
            display_func=display_model,
            prompt="Wähle ein Modell",
            title="KOMMERZIELLE MODELLE"
        )
        
        if selected:
            print(f"✓ Ausgewählt: {selected['name']}")
            return str(selected["provider"]), str(selected["id"])
            
        sys.exit(0)

    def _select_local_model(self) -> tuple[str, str]:
        """Wählt lokales Ollama-Modell."""
        print("\nLade verfügbare Modelle...")
        
        models = get_ollama_models_info()
        
        if not models:
            # Check if we should warn about installation
            if importlib.util.find_spec("ollama") is None:
                print("\n❌ Ollama Python-Bibliothek nicht installiert.")
                print("Bitte installieren: pip install ollama")
                sys.exit(1)

            print(
                "\n⚠️  Keine geeigneten Ollama-Modelle gefunden (oder Ollama läuft nicht)!"
            )
            print("Installiere Modelle mit: ollama pull qwen2.5-coder:7b")
            print("Befehl zum Starten: ollama serve")
            sys.exit(1)

        def display_model(m):
            return (
                m["name"],
                f"Größe: {m['size_gb']:.1f} GB | Aktualisiert: {m['modified']}"
            )

        selected = select_from_list(
            models,
            display_func=display_model,
            prompt="Wähle ein Modell",
            title="LOKALE OLLAMA-MODELLE"
        )
        
        if selected:
            print(f"✓ Ausgewählt: {selected['name']}")
            return "ollama", selected["name"]
            
        sys.exit(0)

    def load_module(self, _: str, module_config: dict[str, Any]):
        """Lädt Test-Modul dynamisch."""
        module_path = Path(module_config["path"])
        test_file = module_path / "test.py"

        return load_test_class(test_file, module_config["test_class"])

    def run(self, run_config: BenchmarkRunConfig):
        """Führt Benchmark aus."""
        self._print_header("CRUCIBLE MARK - BENCHMARK RUNNER")

        # Validate Model Existence (Fail Fast)
        if run_config.model_name:
            provider, model_id = resolve_provider(run_config.model_name)
            if provider == "ollama":
                available_models = get_ollama_models_info()
                model_names = [m["name"] for m in available_models]

                if model_id not in model_names:
                    print(f"\n❌ Error: Local model '{model_id}' not found in Ollama!")
                    print("\n📋 Available Local Models:")
                    for m in available_models:
                        print(f"   - {m['name']} ({m['size_gb']:.1f} GB)")

                    print("\n💡 Tip: Provide the exact name (case-sensitive) or pull it first.")
                    print(f"   ollama pull {model_id}")
                    sys.exit(1)

        # Determine modules to run
        modules_to_run = []
        if run_config.run_all:
            modules_to_run = list(self.get_enabled_modules().items())
        else:
            selected_module, module_config = self.select_module(run_config.module_name)
            if selected_module is None:  # User selected "0. ALL MODULES"
                modules_to_run = list(self.get_enabled_modules().items())
            # selected_module is known to be str here
            elif selected_module and module_config:
                modules_to_run = [(selected_module, module_config)]

                # Enforce multi-run policy from Config
                min_runs = module_config.get("min_runs", 1)
                if min_runs > 1:
                    print(
                        f"\nℹ️  Hinweis: Das Modul '{module_config['name']}' "
                        f"erfordert automatisch {min_runs} Durchläufe."
                    )
                    run_config.num_runs = max(run_config.num_runs, min_runs)

        # Determine provider and model (once for all modules if possible)
        provider = None
        model_id = None

        if run_config.model_name:
            # Auto-detect provider from model name using utils
            provider, model_id = resolve_provider(run_config.model_name)
        else:
            # Interactive selection
            provider, model_id = self.select_provider(run_config.provider_type)

        # Run benchmark for each module
        for _, module_config in modules_to_run:
            print(f"\n>>> Running Module: {module_config['name']}")
            self._run_benchmark(
                module_config,
                model_id,
                provider,
                num_runs=run_config.num_runs,
                force=run_config.force
            )

        # Leaderboard Update
        if modules_to_run:
            print("\n📊 Aktualisiere Leaderboard...")
            try:
                subprocess.run([sys.executable, "scripts/core/generate_leaderboard.py"], check=True)
            except subprocess.CalledProcessError:
                print("⚠️ Fehler beim Aktualisieren des Leaderboards.")
            except Exception as e:
                print(f"⚠️ Unerwarteter Fehler: {e}")

    def _run_benchmark(
        self,
        module_config: dict[str, Any],
        model: str,
        provider: str,
        num_runs: int = 1,
        force: bool = False,
    ):
        """Führt Benchmark aus (Lokal oder Kommerziell)."""
        is_local = provider == "ollama"

        self._print_header(
            f"STARTE {'LOKALEN' if is_local else 'KOMMERZIELLEN'} BENCHMARK"
        )
        print(f"Modul: {module_config['name']}")
        print(f"Modell: {model}")
        print(f"Provider: {provider.upper() if not is_local else 'Ollama (Local)'}")
        print(f"Runs: {num_runs}")
        print(f"Force: {'Yes (Ignore Cache)' if force else 'No'}")
        print(f"{'=' * 60}\n")

        # Load internal module config to get benchmarks/contributions
        internal_config = load_module_config(Path(module_config['path']))

        benchmark_info = {
            "name": module_config["name"],
            "path": f"{module_config['path']}/assets",
            "module_path": module_config["path"],
            "test_class": module_config.get("test_class", "CodeQualityTest"),
            "execution_mode": module_config.get("execution_mode", "standard"),
            "min_runs": module_config.get("min_runs", 1),
            "benchmarks": internal_config.get("benchmarks", []),
        }

        if is_local:
            local_runner = LocalBenchmarkRunner()
            results = local_runner.run_benchmark(
                model, benchmark_info, num_runs=num_runs
            )
            if results:
                local_runner.save_results(results)
                local_runner.print_summary(results, model)
        else:
            comm_runner = CommercialBenchmarkRunner(force=force)
            results = comm_runner.run_benchmark(
                provider, model, benchmark_info, num_runs=num_runs
            )
            if results:
                comm_runner.save_results(results)
                comm_runner.print_summary(results)

    @staticmethod
    def _print_header(title: str):
        """Hilfsmethode für konsistente Header."""
        print(f"\n{'=' * 60}")
        if "RUNNER" in title:
            print(f"🚀 {title}")
        elif "MODULE" in title:
            print(f"📦 {title}")
        else:
            print(f"🌐 {title}")
        print(f"{'=' * 60}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="CrucibleMark - Global Benchmark Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python run_benchmark.py                           # Interaktiv
  python run_benchmark.py --provider local          # Nur Ollama
  python run_benchmark.py --provider commercial     # Nur API-Modelle
  python run_benchmark.py --module code_quality     # Spezifisches Modul
        """,
    )

    parser.add_argument("--module", type=str, help="Test-Modul (z.B. code_quality)")

    parser.add_argument(
        "--provider",
        choices=["local", "commercial"],
        help="Provider-Typ (local=Ollama, commercial=Mistral/Claude/GPT)",
    )

    parser.add_argument(
        "--config",
        type=str,
        default=DEFAULT_CONFIG_PATH,
        help="Pfad zur Config-Datei (Standard: benchmark_config.yaml)",
    )

    parser.add_argument(
        "--model", type=str, help="Modell-Name (überspringt Auswahl, z.B. qwen2.5:14b)"
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Führt Benchmark für alle aktivierten Module aus",
    )

    parser.add_argument(
        "--multi-run",
        type=int,
        default=1,
        help="Anzahl der Runs (default: 1, empfohlen für Political Compass: 3)",
    )

    parser.add_argument(
        "--dev",
        action="store_true",
        help="Run in DEV mode (Faster iteration, 5-10s pauses). Default is Production (15-30s).",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-run of benchmarks even if results exist (ignores cache).",
    )

    args = parser.parse_args()

    # Propagate DEV flag globally via Environment Variable
    if args.dev:
        import os
        os.environ["CRUCIBLE_BM_MODE"] = "DEV"

    try:
        runner = BenchmarkRunner(args.config)
        config = BenchmarkRunConfig(
            module_name=args.module,
            provider_type=args.provider,
            model_name=args.model,
            run_all=args.all,
            num_runs=args.multi_run,
            force=args.force,
        )
        runner.run(config)
    except KeyboardInterrupt:
        print("\n\n❌ Benchmark abgebrochen")
        sys.exit(1)
    except Exception as e:
        logger.exception("Unerwarteter Fehler: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
