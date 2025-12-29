#!/usr/bin/env python3
"""
Listet verfügbare Modelle (Lokal & Kommerziell) auf.
Prüft Konfiguration und API-Keys.
"""

import os
import sys
import yaml
import subprocess
import shutil
from pathlib import Path
from typing import Any

# Add project root to path to import utils
sys.path.append(str(Path(__file__).parent.parent))
from utils.model_utils import is_model_suitable_for_benchmark

# Farben für Terminal-Output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def load_config() -> dict[str, Any]:
    """Lädt die benchmark_config.yaml."""
    config_path = Path("benchmark_config.yaml")
    if not config_path.exists():
        print(f"{Colors.FAIL}Fehler: benchmark_config.yaml nicht gefunden.{Colors.ENDC}")
        sys.exit(1)

    with open(config_path) as f:
        return yaml.safe_load(f)

def check_ollama():
    """Prüft und listet Ollama Modelle mit Eignungs-Check."""
    print(f"\n{Colors.HEADER}=== Lokale Modelle (Ollama) ==={Colors.ENDC}")

    try:
        import ollama
        try:
            models_response = ollama.list()
            # Handle both object and dict response types
            model_list = models_response.models if hasattr(models_response, 'models') else models_response.get('models', [])

            if not model_list:
                print(f"{Colors.WARNING}Keine Modelle in Ollama gefunden.{Colors.ENDC}")
                return

            # Header
            print(f"{Colors.BOLD}{'STATUS':<4} {'NAME':<30} {'SIZE':<10} {'REASON'}{Colors.ENDC}")
            print("-" * 60)

            for model in model_list:
                name = model.model if hasattr(model, 'model') else model.get('name', 'unknown')
                size_bytes = model.size if hasattr(model, 'size') else model.get('size', 0)
                size_gb = size_bytes / (1024**3)

                # Check suitability using centralized logic
                is_suitable = is_model_suitable_for_benchmark(name)

                if is_suitable:
                    status = "🟢"
                    reason = "Ready for Benchmark"
                    color = Colors.GREEN
                else:
                    status = "⚪"
                    reason = "Skipped (Not suitable)"
                    color = Colors.ENDC

                print(f"{status}   {color}{name:<30}{Colors.ENDC} {size_gb:>6.1f} GB   {reason}")

        except Exception as e:
             print(f"{Colors.FAIL}Fehler bei der Kommunikation mit Ollama: {e}{Colors.ENDC}")
             print("Stellen Sie sicher, dass 'ollama serve' läuft.")

    except ImportError:
        # Fallback to subprocess if ollama python package is missing (should not happen with make install)
        print(f"{Colors.WARNING}Python 'ollama' Paket nicht gefunden. Nutze CLI-Fallback...{Colors.ENDC}")
        # ... (Fallback implementation omitted for brevity, assuming requirements are installed)
        ollama_path = shutil.which("ollama")
        if ollama_path:
            result = subprocess.run([ollama_path, "list"], check=False, capture_output=True, text=True)
            print(result.stdout)
        else:
            print(f"{Colors.FAIL}Ollama Executable nicht gefunden.{Colors.ENDC}")

def check_commercial(config: dict[str, Any]):
    """Prüft kommerzielle Provider und deren Status."""
    print(f"\n{Colors.HEADER}=== Kommerzielle Modelle (API) ==={Colors.ENDC}")

    providers = config.get("providers", {}).get("commercial", {})

    if not providers:
        print("Keine kommerziellen Provider konfiguriert.")
        return

    # .env laden (falls python-dotenv installiert wäre, aber wir machen es manuell oder verlassen uns auf Environment)
    # Da wir im Makefile keine .env laden, prüfen wir os.environ.
    # Hinweis: User muss .env gesourced haben oder Variablen exportiert haben.
    # Alternativ: Wir versuchen .env einfach zu lesen für den Check.
    env_vars = os.environ.copy()
    env_path = Path(".env")
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key] = value.strip('"\'')

    for provider_key, provider_data in providers.items():
        name = provider_data.get("name", provider_key)
        enabled = provider_data.get("enabled", False)
        env_var_name = provider_data.get("env_var", "")

        # Status ermitteln
        api_key = env_vars.get(env_var_name)
        has_key = api_key is not None and len(api_key) > 0

        status_symbol = ""
        status_text = ""
        color = ""

        if not enabled:
            status_symbol = "⚪"
            status_text = "Deaktiviert (Config)"
            color = Colors.ENDC # Grau/Standard
        elif not has_key:
            status_symbol = "⚠️ "
            status_text = f"Aktiviert, aber {env_var_name} fehlt"
            color = Colors.WARNING
        else:
            status_symbol = "🟢"
            status_text = "Aktiv & Bereit"
            color = Colors.GREEN

        print(f"{color}{status_symbol} {Colors.BOLD}{name}{Colors.ENDC} ({status_text})")

        # Modelle listen wenn enabled (auch wenn Key fehlt, damit man sieht was möglich wäre)
        if enabled:
            models = provider_data.get("models", [])
            for model in models:
                model_id = model.get("id")
                model_name = model.get("name")
                print(f"   - {model_id:<30} {Colors.BLUE}# {model_name}{Colors.ENDC}")
        print("")

def main():
    config = load_config()
    check_ollama()
    check_commercial(config)

if __name__ == "__main__":
    main()
