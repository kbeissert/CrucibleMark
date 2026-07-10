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
    from utils.constants import MODEL_TYPE_OPEN_WEIGHTS_CLOUD, TIMEOUT_OLLAMA_HEALTH  # noqa: E402
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
) -> list[tuple[str, str, str]]:
    """
    Parses config to find enabled commercial models.
    Delegates to shared utility.
    """
    try:
        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)
        return get_commercial_models_from_config(config)
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Failed to load commercial models: %s", e)
        return []


def check_provider_health(
    models: list[tuple[str, str, str]], config_path: str = "benchmark_config.yaml"
) -> list[str]:
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
        with open(config_path, encoding="utf-8") as f:
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


def get_local_models() -> list[tuple[str, str, str]]:
    """
    Fetches available local models based on enabled providers in benchmark_config.yaml.
    Ollama: only when ollama_local.enabled = true (dynamic discovery).
    llama.cpp: only when llamacpp.enabled = true (explicit config list).
    Returns list of (id, pretty_name, provider_key)
    """
    import yaml
    models = []

    try:
        with open("benchmark_config.yaml", encoding="utf-8") as _f:
            _cfg = yaml.safe_load(_f)
        local_cfg = _cfg.get("providers", {}).get("local", {})
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.error("Fehler beim Laden der Provider-Config: %s", exc)
        return models

    # Ollama: nur wenn enabled
    ollama_cfg = local_cfg.get("ollama_local", {})
    if ollama_cfg.get("enabled", False):
        try:
            ollama_info = get_ollama_models_info()
            for m in ollama_info:
                models.append((m["name"], m["name"], "local"))
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.warning("Fehler beim Abrufen der Ollama-Modelle: %s", e)

    # llama.cpp: nur wenn enabled (explizite Config-Liste)
    llamacpp_cfg = local_cfg.get("llamacpp", {})
    if llamacpp_cfg.get("enabled", False):
        for m in llamacpp_cfg.get("models", []):
            mid = m.get("id", "")
            mname = m.get("name", mid)
            if mid:
                models.append((mid, mname, "local"))

    return models


def run_benchmark(
    module: str, model_id: str, provider: str, audit: bool = False, force: bool = False
):
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

    if not audit:
        cmd.append("--silent")

    if force:
        cmd.append("--force")

    try:
        # Stream output directly to console
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def select_benchmark_module(args_module: str | None = None) -> str:
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
        with open("benchmark_config.yaml", encoding="utf-8") as f:
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


def select_model_category() -> str:
    """Interaktive Auswahl der Modell-Kategorie."""
    choices = [
        ("0", "Alle Modelle (Lokal & Cloud)"),
        ("1", "Kommerzielle Modelle (Proprietary API)"),
        ("2", "Open-Weight Cloud-Modelle"),
        ("3", "Open-Weight Lokale Modelle (Ollama / llama.cpp)")
    ]

    rprint("\n[bold cyan]Wähle die Kategorie der zu testenden Modelle:[/bold cyan]")
    for key, desc in choices:
        rprint(f"  [bold yellow]{key}[/bold yellow]: {desc}")

    while True:
        try:
            choice = input("\nAuswahl (0-3) [0]: ").strip()
            if not choice:
                return "0"
            if choice in ["0", "1", "2", "3"]:
                return choice
            rprint("[red]Ungültige Auswahl. Bitte 0, 1, 2 oder 3 eingeben.[/red]")
        except KeyboardInterrupt:
            rprint("\n[yellow]Abgebrochen.[/yellow]")
            import sys
            sys.exit(0)


def gather_models(category: str) -> list[tuple[str, str, str]]:
    """Sammelt alle zu testenden Modelle basierend auf der Kategorie."""
    import yaml
    all_models = []

    try:
        with open("benchmark_config.yaml", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except Exception as e:
        logger.error("Fehler beim Laden der Konfiguration: %s", e)
        return []

    commercial = []
    open_weight_cloud = []

    providers = config.get("providers", {}).get("commercial", {})
    for p_key, p_config in providers.items():
        if p_config.get("enabled", False):
            m_type = p_config.get("model_type", "proprietary_api")
            for m in p_config.get("models", []):
                model_tuple = (m["id"], m["name"], p_key)
                if m_type == MODEL_TYPE_OPEN_WEIGHTS_CLOUD:
                    open_weight_cloud.append(model_tuple)
                else:
                    commercial.append(model_tuple)

    local_models = []
    if category in ["0", "2", "3"]:
        local_models = get_local_models()

    if category == "0":
        all_models.extend(commercial)
        all_models.extend(open_weight_cloud)
        all_models.extend(local_models)
        rprint(f"[green]Gefunden: {len(commercial)} Kommerzielle, {len(open_weight_cloud)} Open-Weight Cloud, {len(local_models)} Lokale Modelle.[/green]")
    elif category == "1":
        all_models.extend(commercial)
        rprint(f"[green]Gefunden: {len(commercial)} Kommerzielle Modelle.[/green]")
    elif category == "2":
        all_models.extend(open_weight_cloud)
        cloud_local = [m for m in local_models if m[0].endswith(":cloud")]
        all_models.extend(cloud_local)
        rprint(f"[green]Gefunden: {len(open_weight_cloud) + len(cloud_local)} Open-Weight Cloud Modelle.[/green]")
    elif category == "3":
        pure_local = [m for m in local_models if not m[0].endswith(":cloud")]
        all_models.extend(pure_local)
        rprint(f"[green]Gefunden: {len(pure_local)} Lokale Modelle.[/green]")

    return all_models



def main() -> None:
    """Main execution flow for cross-model benchmark."""
    parser = argparse.ArgumentParser(
        description="Run a benchmark module against ALL models."
    )
    parser.add_argument(
        "--module",
        help="ID of the module (e.g. content_transformation). If omitted, interactive selection is used.",
    )
    parser.add_argument(
        "--model",
        help="Run only one specific model (e.g. minimax-m2.7:cloud). Bypasses category prompt.",
    )
    parser.add_argument(
        "--skip-local", action="store_true", help="Skip local Ollama models"
    )
    parser.add_argument(
        "--skip-commercial", action="store_true", help="Skip commercial API models"
    )
    parser.add_argument(
        "--silent",
        action="store_false",
        dest="audit",
        help="Deaktiviert Audit-Logging. Standard: Audit ist aktiv.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Erzwingt einen neuen Durchlauf, auch wenn bereits Ergebnisse existieren.",
    )
    parser.add_argument(
        "--force-rerun",
        action="store_true",
        help="Alias for --force",
    )

    args = parser.parse_args()

    if args.force_rerun:
        args.force = True

    selected_module = select_benchmark_module(args.module)

    if args.model:
        # Determine provider automatically for this model
        p_type = "local"
        if not (args.model.startswith("ollama/") or ":cloud" in args.model or ":latest" in args.model or "-" in args.model):
            # heuristic: if no common ollama trait, maybe commercial, but we'll try to find it
            pass
        # Pre-check: is this model known as open_weights_cloud in config? Then keep p_type = "local".
        _known_cloud_model_ids: set[str] = set()
        try:
            with open("benchmark_config.yaml", encoding="utf-8") as _f:
                _cfg = yaml.safe_load(_f)
            for _prov_conf in _cfg.get("providers", {}).get("commercial", {}).values():
                if _prov_conf.get("model_type") == MODEL_TYPE_OPEN_WEIGHTS_CLOUD:
                    for _m in _prov_conf.get("models", []):
                        if isinstance(_m, dict) and _m.get("id"):
                            _known_cloud_model_ids.add(_m["id"])
        except Exception:
            pass

        import requests
        try:
            from utils.constants import OLLAMA_DEFAULT_BASE_URL
            resp = requests.get(f"{OLLAMA_DEFAULT_BASE_URL}/api/tags", timeout=TIMEOUT_OLLAMA_HEALTH)
            ollama_models = [m["name"] for m in resp.json().get("models", [])]
            if args.model not in ollama_models and "/" in args.model and args.model not in _known_cloud_model_ids:
                p_type = "commercial"
        except Exception:
            if args.model not in _known_cloud_model_ids and ("/" in args.model or args.model.startswith("gpt-") or args.model.startswith("claude-")):
                p_type = "commercial"

        # Output is (model_id, display_name, provider)
        all_models = [(args.model, args.model, p_type)]
        selected_category = "-1"
    else:
        selected_category = select_model_category()
        all_models = gather_models(selected_category)

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

        success = run_benchmark(
            selected_module, m_id, p_type, audit=args.audit, force=args.force
        )

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
