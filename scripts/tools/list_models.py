#!/usr/bin/env python3
"""
Listet verfügbare Modelle (Lokal & Kommerziell) auf.
Prüft Konfiguration und API-Keys durch echten Ping.
"""

import os
import sys
import shutil
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# Third-party imports
# pylint: disable=import-error
import yaml
from dotenv import load_dotenv

try:
    import ollama
except ImportError:
    ollama: Any = None  # type: ignore
# pylint: enable=import-error

# Add project root to path to import utils
# pylint: disable=wrong-import-position, import-error
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from utils.model_utils import is_model_suitable_for_benchmark  # noqa: E402
from utils.llm_client import LLMClient  # noqa: E402
from utils.constants import Colors  # noqa: E402
from utils.model_utils import is_cloud_model  # noqa: E402

# pylint: enable=wrong-import-position, import-error


# Load env variables early
load_dotenv()

# Suppress logging from provider clients and libraries
logging.getLogger("utils.provider_clients").setLevel(logging.CRITICAL)
logging.getLogger("utils.retry_handler").setLevel(logging.CRITICAL)
logging.getLogger("httpx").setLevel(logging.CRITICAL)
logging.getLogger("httpcore").setLevel(logging.CRITICAL)
logging.getLogger("openai").setLevel(logging.CRITICAL)


def load_config() -> Dict[str, Any]:
    """Lädt die benchmark_config.yaml."""
    config_path = Path("benchmark_config.yaml")
    if not config_path.exists():
        print(
            f"{Colors.FAIL}Fehler: benchmark_config.yaml nicht gefunden.{Colors.ENDC}"
        )
        sys.exit(1)

    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _print_ollama_model_row(model: Any) -> None:
    """Printers a single row for an Ollama model."""
    name = model.model if hasattr(model, "model") else model.get("name", "unknown")
    size_bytes = model.size if hasattr(model, "size") else model.get("size", 0)
    size_gb = size_bytes / (1024**3)

    # Check suitability using centralized logic
    is_suitable = is_model_suitable_for_benchmark(name)

    if is_suitable:
        status_icon = "🟢"
        reason = "Ready for Benchmark"
        color = Colors.GREEN
    else:
        status_icon = "⚪"
        reason = "Skipped (Not suitable)"
        color = Colors.ENDC

    print(
        f"{status_icon}   {color}{name:<30}{Colors.ENDC} {size_gb:>6.1f} GB   {reason}"
    )


def check_ollama() -> None:
    """Prüft und listet Ollama Modelle (Lokal und Cloud) mit Eignungs-Check."""

    if ollama:
        try:
            models_response = ollama.list()
            # Handle both object and dict response types
            if hasattr(models_response, "models"):
                model_list = models_response.models
            else:
                model_list = models_response.get("models", [])

            if not model_list:
                print(f"{Colors.WARNING}Keine Modelle in Ollama gefunden.{Colors.ENDC}")
                return

            # Trennung in Lokal und Cloud basierend auf SSOT-Funktion
            local_models = []
            cloud_models = []

            for model in model_list:
                name = str(
                    model.model
                    if hasattr(model, "model")
                    else model.get("name", "unknown")
                )
                size = model.size if hasattr(model, "size") else model.get("size", 0)
                size_gb = (size or 0) / (1024**3)

                # Use SSOT function for cloud detection
                if is_cloud_model(name, size_gb):
                    cloud_models.append(model)
                else:
                    local_models.append(model)

            # --- Lokale Modelle ---
            print(f"\n{Colors.HEADER}=== Lokale Modelle (Ollama) ==={Colors.ENDC}")
            if local_models:
                print(
                    f"{Colors.BOLD}{'STATUS':<4} {'NAME':<30} "
                    f"{'SIZE':<10} {'REASON'}{Colors.ENDC}"
                )
                print("-" * 60)
                for model in local_models:
                    _print_ollama_model_row(model)
            else:
                print("Keine lokalen Modelle gefunden.")

            # --- Cloud Modelle ---
            # Nur anzeigen, wenn vorhanden
            if cloud_models:
                print(f"\n{Colors.HEADER}=== Cloud Modelle (Ollama) ==={Colors.ENDC}")
                print(
                    f"{Colors.BOLD}{'STATUS':<4} {'NAME':<30} "
                    f"{'TYPE':<10} {'REASON'}{Colors.ENDC}"
                )
                print("-" * 60)

                for model in cloud_models:
                    # Slightly different printing for cloud (No size usually)
                    name = str(
                        model.model
                        if hasattr(model, "model")
                        else model.get("name", "unknown")
                    )
                    # Reuse row printer or custom? Reuse is fine, size is just 0.0 GB
                    _print_ollama_model_row(model)

        except (ConnectionError, OSError, RuntimeError) as e:
            print(
                f"{Colors.FAIL}Fehler bei der Kommunikation mit Ollama: {e}{Colors.ENDC}"
            )
            print("Stellen Sie sicher, dass 'ollama serve' läuft.")
    else:
        # Fallback to subprocess if ollama python package is missing
        print(
            f"{Colors.WARNING}Python 'ollama' Paket nicht gefunden. "
            f"Nutze CLI-Fallback...{Colors.ENDC}"
        )
        ollama_path = shutil.which("ollama")
        if ollama_path:
            result = subprocess.run(
                [ollama_path, "list"], check=False, capture_output=True, text=True
            )
            print(result.stdout)
        else:
            print(f"{Colors.FAIL}Ollama Executable nicht gefunden.{Colors.ENDC}")


def _diagnose_api_error(e: Exception) -> Tuple[str, str, Optional[str]]:
    """Analysiert Exception und gibt (Status, Msg, DetailedMsg) zurück."""
    err_str = str(e).lower()
    status = f"{Colors.FAIL}ERR {Colors.ENDC}"
    msg = "Connection Error"
    detailed_msg = None

    if "insufficient_quota" in err_str or "429" in err_str:
        status = f"{Colors.FAIL}QUOTA{Colors.ENDC}"
        msg = "Insufficient Quota"
        detailed_msg = "↳ Dein Guthaben ist aufgebraucht (Fehler 429)."
    elif "401" in err_str or "unauthorized" in err_str or "invalid api key" in err_str:
        status = f"{Colors.FAIL}AUTH{Colors.ENDC}"
        msg = "Invalid API Key"
        detailed_msg = "↳ Der API-Key wird abgelehnt (Fehler 401)."
    elif "404" in err_str or "not found" in err_str or "does not exist" in err_str:
        status = f"{Colors.FAIL}404 {Colors.ENDC}"
        msg = "No Access / Not Found"
        detailed_msg = "↳ Modell nicht gefunden oder kein Zugriff (Fehler 404/Tier)."
    elif "rate limit" in err_str:
        status = f"{Colors.FAIL}RATE{Colors.ENDC}"
        msg = "Rate Limit Exceeded"
        detailed_msg = "↳ Zu viele Anfragen in kurzer Zeit."
    else:
        clean_err = str(e).replace("\n", " ")
        detailed_msg = f"↳ Unbekannter Fehler: {clean_err[:80]}..."

    return status, msg, detailed_msg


def _test_model_connectivity(
    client: Any, model_id: str, prov_key: str, prov_name: str
) -> None:
    """Testet Konnektivität für ein bestimmtes Modell via LLMClient."""
    detailed_msg = None
    try:
        # Real Ping Test (Minimal Token usage)
        # Using the unified LLMClient to ensure Version Locking and central logic is used
        _ = client.query(
            model=model_id,
            prompt="Hi",
            provider=prov_key,
            temperature=0.1,
            max_retries=1,  # Don't retry too much for liveness check
            call_type="overhead_ping",
        )

        status = f"{Colors.GREEN}OK  {Colors.ENDC}"
        msg = "Online & Verified"
    except Exception as e:  # pylint: disable=broad-exception-caught
        status, msg, detailed_msg = _diagnose_api_error(e)

    print(f"{prov_name:<15} {model_id:<30} {status}   {msg}")

    if detailed_msg:
        print(
            f"                                               "
            f"{Colors.WARNING}{detailed_msg}{Colors.ENDC}"
        )


def check_commercial(config: Dict[str, Any]) -> None:
    """Prüft kommerzielle Provider und deren Status durch echten API-Ping."""
    providers = config.get("providers", {}).get("commercial", {})

    if not providers:
        print(
            f"{Colors.WARNING}Keine kommerziellen Provider konfiguriert.{Colors.ENDC}"
        )
        return

    # Initialize unified client
    try:
        llm_client = LLMClient(config)
    except Exception as e:
        print(
            f"{Colors.FAIL}Critical: Failed to initialize LLMClient: {e}{Colors.ENDC}"
        )
        return

    # --- Cloud Modelle (Open-Weights, groq etc) ---
    print(f"\n{Colors.HEADER}=== Cloud Modelle (Open-Weights) ==={Colors.ENDC}")
    print(
        f"{Colors.BOLD}{'PROVIDER':<15} {'MODEL':<30} {'STATUS':<6} {'MSG'}{Colors.ENDC}"
    )
    print("-" * 80)
    has_open_cloud = False
    for prov_key, prov_data in providers.items():
        if not prov_data.get("enabled", False):
            continue

        # Nur explizite Open-Weights Cloud Modelle (wie Groq oder Ollama Cloud)
        if prov_data.get("model_type") != "open_weights_cloud":
            continue

        has_open_cloud = True
        prov_name = prov_data.get("name", prov_key)
        env_var = prov_data.get("env_var", "")
        api_key = os.getenv(env_var) if env_var else None

        if not api_key and prov_key != "ollama_cloud":  # Ollama Cloud braucht meist keinen globalen Env-Key im klassischen Sinne
            print(
                f"{prov_name:<15} {'(All Models)':<30} "
                f"{Colors.FAIL}MISS{Colors.ENDC}   Missing Env Var: {env_var}"
            )
            continue

        for model in prov_data.get("models", []):
            _test_model_connectivity(llm_client, model["id"], prov_key, prov_name)

    if not has_open_cloud:
        print("Keine Open-Weights Cloud-Modelle konfiguriert.")

    # --- Echte Kommerzielle Modelle ---
    print(f"\n{Colors.HEADER}=== Kommerzielle Modelle (API) ==={Colors.ENDC}")
    print(
        f"{Colors.BOLD}{'PROVIDER':<15} {'MODEL':<30} {'STATUS':<6} {'MSG'}{Colors.ENDC}"
    )
    print("-" * 80)

    for prov_key, prov_data in providers.items():
        if not prov_data.get("enabled", False):
            continue

        # Nur proprietäre APIs
        if prov_data.get("model_type") != "proprietary_api":
            continue

        prov_name = prov_data.get("name", prov_key)
        env_var = prov_data.get("env_var", "")

        # Check API Key presence
        api_key = os.getenv(env_var) if env_var else None
        if not api_key and env_var == "OPENAI_API_KEY":
            api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            print(
                f"{prov_name:<15} {'(All Models)':<30} "
                f"{Colors.FAIL}MISS{Colors.ENDC}   Missing Env Var: {env_var}"
            )
            continue

        # Test each model
        for model in prov_data.get("models", []):
            _test_model_connectivity(llm_client, model["id"], prov_key, prov_name)


def main() -> None:
    """Main entry point."""
    config = load_config()
    check_ollama()
    check_commercial(config)


if __name__ == "__main__":
    main()
