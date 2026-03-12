#!/usr/bin/env python3
"""
Cross-Model Benchmark Runner
============================

Runs a specific benchmark module against ALL available models (Local & Commercial).
Useful for validating a new module against a wide range of LLMs or generating
comprehensive leaderboards for a specific task.

Usage:
    python scripts/core/run_cross_model_benchmark.py --module content_transformation
"""

import argparse
import sys
import logging
import subprocess
from pathlib import Path
from typing import List, Tuple

# pylint: disable=import-error
import yaml
from rich.console import Console
from rich.table import Table
from rich import print as rprint

# pylint: enable=import-error

# Add project root to path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

try:
    from utils.model_utils import (
        get_ollama_models_info,
        get_commercial_models_from_config,
    )

    # from utils.config_validator import ConfigValidator
    from utils.module_registry import get_active_modules
    from utils.benchmark_utils import select_from_list
    from utils.llm_client import LLMClient
except ImportError:
    print("Error importing utils. Ensure you are running from the project root.")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("cross_model_benchmark")
console = Console()


def get_commercial_models(
    config_path: str = "benchmark_config.yaml",
) -> List[Tuple[str, str, str]]:
    """
    Parses config to find enabled commercial models.
    Delegates to shared utility.
    """
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        return get_commercial_models_from_config(config)
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Failed to load commercial models: %s", e)
        return []


def check_provider_health(
    models: List[Tuple[str, str, str]], config_path: str = "benchmark_config.yaml"
) -> List[str]:
    """
    Checks health/quota for all commercial providers involved.
    Uses unified LLMClient for connectivity checks.
    Returns a list of failed provider keys.
    """
    failed_providers = []

    # Identify unique commercial providers
    providers_to_check = set()
    for _, _, p_key in models:
        if p_key != "local":
            providers_to_check.add(p_key)

    if not providers_to_check:
        return []

    rprint(
        f"\n[bold]🔍 Pre-flight Prüfung ({len(providers_to_check)} Provider)...[/bold]"
    )

    # Retrieve config
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Fehler beim Laden der Konfiguration: %s", e)
        return list(providers_to_check)

    # Initialize generic client which handles sub-clients internally
    try:
        llm_client = LLMClient(config)
    except Exception as e:  # pylint: disable=broad-exception-caught
        rprint(
            f"[red]Kritisch: Fehler bei der Initialisierung von LLMClient: {e}[/red]"
        )
        return list(providers_to_check)

    for p_key in providers_to_check:
        try:
            # Access the specific provider implementation from the map
            provider_impl = llm_client.clients.get(p_key)

            if provider_impl:
                with console.status(f"[bold cyan]Pinging {p_key}...[/bold cyan]"):
                    is_ok = provider_impl.is_accessible()

                if is_ok:
                    rprint(f"  ✅ [green]{p_key.title()}[/green]:  Online & Quota OK")
                else:
                    rprint(
                        f"  ❌ [red]{p_key.title()}[/red]:  Verbindung abgelehnt oder Quota erschöpft"
                    )
                    failed_providers.append(p_key)
            else:
                rprint(
                    f"  ⚠️ [yellow]{p_key.title()}[/yellow]:  Keine Implementierung im LLMClient gefunden"
                )
                failed_providers.append(p_key)

        except Exception as e:  # pylint: disable=broad-exception-caught
            rprint(f"  ❌ [red]{p_key.title()}[/red]: Check crashed: {e}")
            failed_providers.append(p_key)

    return failed_providers


def get_local_models() -> List[Tuple[str, str, str]]:
    """
    Fetches available Ollama models.
    Returns list of (id, pretty_name, provider_key)
    """
    models = []
    try:
        ollama_info = get_ollama_models_info()
        for m in ollama_info:
            # name is usually 'model:tag'
            models.append((m["name"], m["name"], "local"))
    except Exception as e:  # pylint: disable=broad-exception-caught
        # Ollama might not be running
        logger.warning("Fehler beim Abrufen lokaler Modelle (Läuft Ollama?): %s", e)

    return models


def run_benchmark(module: str, model_id: str, provider: str):
    """
    Executes run_benchmark.py for a single model/module combo.
    """
    # Fix: run_benchmark.py expects --provider to be 'local' or 'commercial'
    # The specific provider (e.g. 'mistral') is resolved internally via model name
    cli_provider = "local" if provider == "local" else "commercial"

    cmd = [
        sys.executable,
        "run_benchmark.py",
        "--module",
        module,
        "--provider",
        cli_provider,
        "--model",
        model_id,
        "--multi-run",
        "1",  # Default to 1 run for speed
    ]

    try:
        # Stream output directly to console
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def select_benchmark_module(args_module: str = None) -> str:
    """Interaktive Modulauswahl, falls kein Modul per CLI übergeben wurde."""
    if args_module:
        return args_module

    rprint("[bold cyan]Kein Modul angegeben. Lade verfügbare Module...[/bold cyan]")

    try:
        # Load config directly using yaml instead of Validator wrapper
        # The Validator class wraps the config in self.config, but get_active_modules expects a dict.
        # If validator.config is a dict, it should work. Let's check where the 'list object is not callable' error
        # comes from.
        # Ah, ConfigValidator("path") returns an instance. instance.config is the dict.
        # But maybe select_benchmark_module calls something incorrectly?

        # Let's just load yaml directly to be safe and simple here
        with open("benchmark_config.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        modules_list = get_active_modules(config)

        choices = []
        for mod_id, meta, _ in modules_list:
            name = meta.get("name", mod_id)
            desc = meta.get("description", "")
            choices.append((f"{name} ({mod_id}) - {desc}", mod_id))

        # Fix: select_from_list signature is (items, display_func, prompt)
        selection_tuple = select_from_list(
            items=choices,
            display_func=lambda x: x[0],
            prompt="Wähle ein Benchmark-Modul für den Cross-Model Run:",
        )

        if not selection_tuple:
            rprint("[yellow]Kein Modul ausgewählt. Beende.[/yellow]")
            sys.exit(0)

        return selection_tuple[1]

    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Fehler beim Laden der Module: %s", e)
        sys.exit(1)


def gather_models(
    skip_local: bool, skip_commercial: bool
) -> List[Tuple[str, str, str]]:
    """Sammelt alle zu testenden Modelle."""
    all_models = []

    if not skip_commercial:
        comm_models = get_commercial_models()
        all_models.extend(comm_models)
        rprint(f"[green]Gefunden: {len(comm_models)} kommerzielle Modelle.[/green]")

    if not skip_local:
        local_models = get_local_models()
        all_models.extend(local_models)
        rprint(f"[green]Gefunden: {len(local_models)} lokale Modelle.[/green]")

    return all_models


def main():
    """Main execution flow for cross-model benchmark."""
    parser = argparse.ArgumentParser(
        description="Run a benchmark module against ALL models."
    )
    parser.add_argument(
        "--module",
        help="ID of the module (e.g. content_transformation). If omitted, interactive selection is used.",
    )
    parser.add_argument(
        "--skip-local", action="store_true", help="Skip local Ollama models"
    )
    parser.add_argument(
        "--skip-commercial", action="store_true", help="Skip commercial API models"
    )

    args = parser.parse_args()

    selected_module = select_benchmark_module(args.module)

    console.rule(f"[bold blue]📊 Cross-Model Benchmark: {selected_module}")

    # 1. Gather Models
    all_models = gather_models(args.skip_local, args.skip_commercial)

    if not all_models:
        rprint("[red]❌ Keine Modelle gefunden! Config und Ollama prüfen.[/red]")
        sys.exit(1)

    # 1.5 Health Check / Pre-flight Ping
    failed_providers = check_provider_health(all_models)

    if failed_providers:
        # pylint: disable=line-too-long
        rprint(
            f"\n[bold red]⚠️  Überspringe Provider mit Fehlern: {', '.join(failed_providers)}[/bold red]"
        )
        all_models = [m for m in all_models if m[2] not in failed_providers]

        if not all_models:
            rprint(
                "[bold red]❌ Alle Modelle aufgrund von Provider-Fehlern übersprungen. Beende.[/bold red]"
            )
            sys.exit(1)

    # 2. Confirm
    rprint("\n[bold]⚙️  Konfiguration:[/bold]")
    rprint(f"  Modul:       [cyan]{selected_module}[/cyan]")
    rprint(f"  Modelle:     [cyan]{len(all_models)}[/cyan]")

    table = Table(title="Ziel-Modelle")
    table.add_column("Provider", style="dim")
    table.add_column("Modell ID", style="bold")

    for m_id, _, p_type in all_models:
        table.add_row(p_type, m_id)

    console.print(table)

    # 3. Execution Loop
    results = {"success": [], "failure": []}

    for i, (m_id, m_name, p_type) in enumerate(all_models):
        console.rule(
            f"[yellow]🚀 Starte Lauf {i + 1}/{len(all_models)}: {m_name}[/yellow]"
        )

        success = run_benchmark(selected_module, m_id, p_type)

        if success:
            results["success"].append(m_id)
            rprint(f"[green]✅ Benchmark für {m_id} erfolgreich.[/green]")
        else:
            results["failure"].append(m_id)
            rprint(f"[red]❌ Benchmark für {m_id} fehlgeschlagen.[/red]")

    # 4. Summary
    console.rule("[bold]📝 Zusammenfassung[/bold]")
    rprint(f"[green]Erfolgreich:   {len(results['success'])}[/green]")
    rprint(f"[red]Fehlgeschlagen: {len(results['failure'])}[/red]")

    if results["failure"]:
        rprint("Fehlgeschlagene Modelle:", ", ".join(results["failure"]))


if __name__ == "__main__":
    main()
