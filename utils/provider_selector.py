import sys
import importlib.util
from typing import Optional

from utils.benchmark_utils import select_from_list
from utils.model_utils import is_cloud_model, get_ollama_models_info


class ProviderSelector:
    """Class responsible for interactive provider and model selection."""

    def __init__(self, config: dict):
        self.config = config

    def select_provider(self, provider_type: Optional[str] = None) -> tuple[str, str]:
        """Interaktive Provider-Auswahl (commercial/local/cloud)."""
        if provider_type and provider_type in ["commercial", "local", "cloud"]:
            return self._select_provider_models(provider_type)

        options = [
            (
                "commercial",
                "Kommerzielle Modelle (API Provider) - Mistral, Claude, GPT",
            ),
            ("local", "Lokale Modelle (Ollama, LM Studio) - Offline"),
            ("cloud", "Cloud Modelle (Ollama Proxy) - MiniMax, DeepSeek Cloud"),
        ]

        selected = select_from_list(
            options,
            display_func=lambda x: x[1],
            prompt="Wähle Provider-Typ",
            title="PROVIDER",
        )

        if selected:
            # Shorten display for UX
            short_name = selected[1].split(" - ")[0]
            print(f"✓  {short_name}")
            return self._select_provider_models(selected[0])

        sys.exit(0)

    def _select_provider_models(self, provider_type: str) -> tuple[str, str]:
        """Wählt Provider und Modell basierend auf Typ."""
        if provider_type == "commercial":
            return self._select_commercial_model()
        if provider_type == "cloud":
            return self._select_cloud_model()
        return self._select_local_model()

    def _select_cloud_model(self) -> tuple[str, str]:
        """Wählt ein Cloud-Modell über Ollama."""
        print("\nLade Cloud-Modelle via Ollama...")

        models = get_ollama_models_info()

        cloud_models = [m for m in models if is_cloud_model(m["name"], m["size_gb"])]

        if not cloud_models:
            print("\n⚠️  Keine Cloud-Modelle in Ollama gefunden.")
            print("Hast du Modelle wie 'minimax-m2:cloud' geladen?")
            sys.exit(1)

        def display_model(m):
            return (m["name"], f"Typ: Cloud Proxy | Aktualisiert: {m['modified']}")

        selected = select_from_list(
            cloud_models,
            display_func=display_model,
            prompt="Wähle ein Cloud-Modell",
            title="CLOUD OLLAMA-MODELLE",
        )

        if selected:
            print(f"✓ Ausgewählt: {selected['name']}")
            return "ollama", selected["name"]

        sys.exit(0)

    def _select_commercial_model(self) -> tuple[str, str]:
        """Wählt kommerzielles Modell (Mistral/Claude/GPT)."""
        commercial_config = self.config.get("providers", {}).get("commercial", {})
        models_flat = []

        for provider_key, provider_data in commercial_config.items():
            # Only include models from enabled providers
            if not provider_data.get("enabled", False):
                continue

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
                f"{m['description']} (Model: {m['id']})",
            )

        selected = select_from_list(
            models_flat,
            display_func=display_model,
            prompt="Wähle ein Modell",
            title="KOMMERZIELLE MODELLE",
        )

        if selected:
            print(f"✓ Ausgewählt: {selected['name']}")
            return str(selected["provider"]), str(selected["id"])

        sys.exit(0)

    def _select_local_model(self) -> tuple[str, str]:
        """Wählt lokales Ollama-Modell."""
        print("\nLade verfügbare Modelle...")

        models = get_ollama_models_info()

        # Filter OUT cloud models for the local list to avoid confusion (using SSOT)
        local_models = [m for m in models if not is_cloud_model(m["name"], m["size_gb"])]

        if not local_models:
            # Check if we should warn about installation
            if importlib.util.find_spec("ollama") is None:
                print("\n❌ Ollama Python-Bibliothek nicht installiert.")
                print("Bitte installieren: pip install ollama")
                sys.exit(1)

            print(
                "\n⚠️  Keine geeigneten lokalen Ollama-Modelle gefunden (oder Ollama läuft nicht)!"
            )
            print("Installiere Modelle mit: ollama pull qwen2.5-coder:7b")
            print("Befehl zum Starten: ollama serve")
            sys.exit(1)

        def display_model(m):
            return (
                m["name"],
                f"Größe: {m['size_gb']:.1f} GB | Aktualisiert: {m['modified']}",
            )

        selected = select_from_list(
            local_models,
            display_func=display_model,
            prompt="Wähle ein Modell",
            title="LOKALE OLLAMA-MODELLE",
        )

        if selected:
            print(f"✓ Ausgewählt: {selected['name']}")
            return "ollama", selected["name"]

        sys.exit(0)
