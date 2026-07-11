import sys
import logging
import importlib.util

from utils.benchmark_utils import select_from_list
from utils.constants import MODEL_TYPE_OPEN_WEIGHTS_CLOUD
from utils.model_utils import is_cloud_model, get_ollama_models_info

logger = logging.getLogger(__name__)


class ProviderSelector:
    """Class responsible for interactive provider and model selection."""

    def __init__(self, config: dict):
        self.config = config

    def select_provider(self, provider_type: str | None = None) -> tuple[str, str]:
        """Interaktive Provider-Auswahl (commercial/local/cloud)."""
        if provider_type and provider_type in ["commercial", "local", "cloud"]:
            return self._select_provider_models(provider_type)

        options = [
            (
                "commercial",
                "Kommerzielle Modelle (Proprietary API) - Anthropic, OpenAI, Google, Mistral, xAI",
            ),
            ("cloud", "Cloud Modelle (Inference Proxy) - OpenRouter, Groq, Ollama Cloud"),
            ("local", "Lokale Modelle (llama.cpp / Ollama) - Offline"),
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
            logger.info(f"✓  {short_name}")
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
        """Wählt ein Cloud-Modell (OpenRouter, Groq oder Ollama Cloud Proxy)."""
        commercial_config = self.config.get("providers", {}).get("commercial", {})
        models_flat = []

        # 1. Cloud Inference Proxy Provider aus der Config (OpenRouter, Groq, etc.)
        for provider_key, provider_data in commercial_config.items():
            if not provider_data.get("enabled", False):
                continue
            if provider_data.get("model_type") != MODEL_TYPE_OPEN_WEIGHTS_CLOUD:
                continue
            for model in provider_data.get("models", []):
                models_flat.append(
                    {
                        "provider": provider_key,
                        "provider_name": provider_data.get("name", provider_key),
                        "id": model["id"],
                        "name": model["name"],
                        "description": model.get("description", ""),
                        "source": "config",
                    }
                )

        # 2. Ollama Cloud-Proxy-Modelle (z.B. minimax-m2:cloud via Ollama)
        try:
            ollama_models = get_ollama_models_info()
            for m in ollama_models:
                if is_cloud_model(m["name"], m["size_gb"]):
                    models_flat.append(
                        {
                            "provider": "ollama",
                            "provider_name": "Ollama Cloud Proxy",
                            "id": m["name"],
                            "name": m["name"],
                            "description": f"Aktualisiert: {m['modified']}",
                            "source": "ollama",
                        }
                    )
        except Exception:  # noqa: BLE001
            pass

        if not models_flat:
            logger.warning("\n⚠️  Keine Cloud-Modelle gefunden.")
            logger.info("Stelle sicher, dass OpenRouter/Groq in benchmark_config.yaml aktiviert sind")
            logger.info("oder lade Ollama Cloud-Proxy-Modelle (z.B. 'ollama pull minimax-m2:cloud').")
            sys.exit(1)

        def display_model(m):
            return (
                f"[{m['provider_name']}] {m['name']}",
                f"{m['description']} (Model: {m['id']})" if m["description"] else f"Model: {m['id']}",
            )

        selected = select_from_list(
            models_flat,
            display_func=display_model,
            prompt="Wähle ein Cloud-Modell",
            title="CLOUD MODELLE",
        )

        if selected:
            logger.info(f"✓ Ausgewählt: {selected['name']}")
            return str(selected["provider"]), str(selected["id"])

        sys.exit(0)

    def _select_commercial_model(self) -> tuple[str, str]:
        """Wählt kommerzielles Modell (Proprietary API: Anthropic/OpenAI/Google/Mistral/xAI)."""
        commercial_config = self.config.get("providers", {}).get("commercial", {})
        models_flat = []

        for provider_key, provider_data in commercial_config.items():
            # Only include models from enabled providers
            if not provider_data.get("enabled", False):
                continue
            # Nur proprietäre API-Provider (keine Cloud Inference Proxies)
            if provider_data.get("model_type", "proprietary_api") != "proprietary_api":
                continue

            for model in provider_data.get("models", []):
                models_flat.append(
                    {
                        "provider": provider_key,
                        "provider_name": provider_data["name"],
                        "id": model["id"],
                        "name": model["name"],
                        "description": model.get("description", ""),
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
            title="KOMMERZIELLE MODELLE (PROPRIETARY API)",
        )

        if selected:
            logger.info(f"✓ Ausgewählt: {selected['name']}")
            return str(selected["provider"]), str(selected["id"])

        sys.exit(0)

    def _select_local_model(self) -> tuple[str, str]:
        """Wählt lokales Modell — nur aus aktivierten Providern (enabled: true in Config)."""
        logger.info("\nLade verfügbare lokale Modelle...")
        local_cfg = self.config.get("providers", {}).get("local", {})
        llamacpp_cfg = local_cfg.get("llamacpp", {})
        llamacpp_spark_cfg = local_cfg.get("llamacpp_spark", {})
        vllm_spark_cfg = local_cfg.get("vllm_spark", {})
        ollama_cfg = local_cfg.get("ollama_local", {})
        use_llamacpp = llamacpp_cfg.get("enabled", False)
        use_llamacpp_spark = llamacpp_spark_cfg.get("enabled", False)
        use_vllm_spark = vllm_spark_cfg.get("enabled", False)
        use_ollama = ollama_cfg.get("enabled", False)

        enabled_runtimes = self._build_enabled_local_runtimes(
            use_llamacpp, use_llamacpp_spark, use_vllm_spark,
        )

        if len(enabled_runtimes) > 1:
            return self._prompt_local_runtime(
                enabled_runtimes, llamacpp_cfg, llamacpp_spark_cfg, vllm_spark_cfg,
            )

        # Single-runtime path: direkt dispatchen, kein Prompt
        if use_llamacpp:
            return self._select_llamacpp_model(llamacpp_cfg, "llamacpp")
        if use_llamacpp_spark:
            return self._select_llamacpp_model(llamacpp_spark_cfg, "llamacpp_spark")
        if use_vllm_spark:
            return self._select_vllm_model(vllm_spark_cfg, "vllm_spark")
        if use_ollama:
            return self._select_ollama_model()
        logger.error("\n❌ Kein lokaler Provider aktiv. Bitte 'enabled: true' in benchmark_config.yaml setzen.")
        logger.info("   providers.local.ollama_local.enabled oder providers.local.llamacpp.enabled")
        sys.exit(1)

    @staticmethod
    def _build_enabled_local_runtimes(
        use_llamacpp: bool, use_llamacpp_spark: bool, use_vllm_spark: bool,
    ) -> list[tuple[str, str]]:
        """Sammelt die aktivierten lokalen Runtime-Paare (key, display)."""
        enabled: list[tuple[str, str]] = []
        if use_llamacpp:
            enabled.append(("llamacpp", "llama.cpp (MacBook Pro)"))
        if use_llamacpp_spark:
            enabled.append(("llamacpp_spark", "llama.cpp (DGX Spark)"))
        if use_vllm_spark:
            enabled.append(("vllm_spark", "vLLM (asusGX10)"))
        return enabled

    def _prompt_local_runtime(
        self,
        enabled_runtimes: list[tuple[str, str]],
        llamacpp_cfg: dict,
        llamacpp_spark_cfg: dict,
        vllm_spark_cfg: dict,
    ) -> tuple[str, str]:
        """Fragt den User nach einer lokalen Runtime und routet entsprechend."""
        runtime = select_from_list(
            enabled_runtimes,
            display_func=lambda x: x[1],
            prompt="Wähle lokale Runtime",
            title="LOKALE PROVIDER",
        )
        if runtime is None:
            sys.exit(0)
        if runtime[0] == "llamacpp":
            return self._select_llamacpp_model(llamacpp_cfg, "llamacpp")
        if runtime[0] == "llamacpp_spark":
            return self._select_llamacpp_model(llamacpp_spark_cfg, "llamacpp_spark")
        if runtime[0] == "vllm_spark":
            return self._select_vllm_model(vllm_spark_cfg, "vllm_spark")
        sys.exit(0)

    def _select_vllm_model(self, vllm_cfg: dict, provider_name: str = "vllm_spark") -> tuple[str, str]:
        """Wählt Modell aus der vLLM-Konfiguration.

        vLLM-Modell-IDs sind TOML-Namen (oder absolute Pfade), keine GGUF-Dateien.
        ``config_models`` enthält die Liste aus ``provider_config.yaml``;
        ``live_ids`` werden vom laufenden ``/v1/models``-Endpunkt geholt.
        """
        config_models = [
            {
                "provider": provider_name,
                "id": m.get("id", ""),
                "name": m.get("name", m.get("id", "")),
                "description": m.get("description", "") or m.get("config", ""),
                "file": m.get("config", ""),
            }
            for m in vllm_cfg.get("models", [])
            if m.get("id")
        ]

        live_ids: set[str] = set()
        try:
            from openai import OpenAI
            import httpx

            _client = OpenAI(
                base_url=vllm_cfg.get("base_url", "http://127.0.0.1:4300/v1"),
                api_key=vllm_cfg.get("api_key", "sk-local"),
                timeout=httpx.Timeout(connect=3.0, read=5.0, write=5.0, pool=5.0),
            )
            resp = _client.models.list()
            live_ids = {m.id for m in resp.data}
            config_ids = {m["id"] for m in config_models}
            for mid in live_ids - config_ids:
                config_models.append(
                    {"provider": provider_name, "id": mid, "name": mid,
                     "description": "Live vom Server", "file": ""}
                )
        except Exception:
            pass

        if not config_models:
            logger.warning("\n⚠️  Keine vLLM-Modelle in benchmark_config.yaml konfiguriert.")
            logger.info(f"Ergänze Modelle unter providers.local.{provider_name}.models")
            sys.exit(1)

        title = "LOKALE MODELLE (vLLM — asusGX10)"
        server_hint = " [asusGX10]"

        def display_model(m):
            live_tag = server_hint if m["id"] in live_ids else ""
            desc = m["description"] or m["file"] or ""
            return (f"{m['name']}{live_tag}", f"ID: {m['id']}  {desc}".strip())

        selected = select_from_list(
            config_models,
            display_func=display_model,
            prompt="Wähle ein Modell",
            title=title,
        )

        if selected:
            logger.info(f"✓ Ausgewählt: {selected['name']}")
            return provider_name, str(selected["id"])
        sys.exit(0)

    def _select_llamacpp_model(self, llamacpp_cfg: dict, provider_name: str = "llamacpp") -> tuple[str, str]:
        """Wählt Modell aus der llama.cpp-Konfiguration.

        Args:
            llamacpp_cfg: Provider-Konfiguration (llamacpp oder llamacpp_spark).
            provider_name: Provider-Name für die Rückgabe ("llamacpp" oder "llamacpp_spark").
        """
        config_models = [
            {
                "provider": provider_name,
                "id": m.get("id", ""),
                "name": m.get("name", m.get("id", "")),
                "description": m.get("description", ""),
                "file": m.get("file", "") or m.get("model_file", ""),
            }
            for m in llamacpp_cfg.get("models", [])
            if m.get("id")
        ]

        # Ergänze Live-Modelle vom Server (falls er läuft)
        live_ids = set()
        try:
            from openai import OpenAI
            import httpx

            _client = OpenAI(
                base_url=llamacpp_cfg.get("base_url", "http://127.0.0.1:1235/v1"),
                api_key=llamacpp_cfg.get("api_key", "sk-local"),
                timeout=httpx.Timeout(connect=3.0, read=5.0, write=5.0, pool=5.0),
            )
            resp = _client.models.list()
            live_ids = {m.id for m in resp.data}
            # Füge Live-Modelle hinzu, die nicht in der Config stehen
            config_ids = {m["id"] for m in config_models}
            for mid in live_ids - config_ids:
                config_models.append(
                    {"provider": provider_name, "id": mid, "name": mid, "description": "Live vom Server", "file": ""}
                )
        except Exception:
            pass

        if not config_models:
            logger.warning("\n⚠️  Keine llama.cpp-Modelle in benchmark_config.yaml konfiguriert.")
            logger.info(f"Ergänze Modelle unter providers.local.{provider_name}.models")
            sys.exit(1)

        # Titel anpassen je nach Provider
        if provider_name == "llamacpp_spark":
            title = "LOKALE MODELLE (llama.cpp — DGX Spark)"
            server_hint = " [DGX Spark]"
        else:
            title = "LOKALE MODELLE (llama.cpp)"
            server_hint = " [Server aktiv]"

        def display_model(m):
            live_tag = server_hint if m["id"] in live_ids else ""
            desc = m["description"] or m["file"] or ""
            return (f"{m['name']}{live_tag}", f"ID: {m['id']}  {desc}".strip())

        selected = select_from_list(
            config_models,
            display_func=display_model,
            prompt="Wähle ein Modell",
            title=title,
        )

        if selected:
            logger.info(f"✓ Ausgewählt: {selected['name']}")
            return provider_name, str(selected["id"])

        sys.exit(0)

    def _select_ollama_model(self) -> tuple[str, str]:
        """Wählt lokales Ollama-Modell (Fallback wenn llama.cpp nicht aktiv ist)."""
        models = get_ollama_models_info()
        local_models = [m for m in models if not is_cloud_model(m["name"], m["size_gb"])]

        if not local_models:
            if importlib.util.find_spec("ollama") is None:
                logger.error("\n❌ Ollama Python-Bibliothek nicht installiert.")
                logger.info("Bitte installieren: pip install ollama")
                sys.exit(1)

            logger.warning("\n⚠️  Keine geeigneten lokalen Ollama-Modelle gefunden (oder Ollama läuft nicht)!")
            logger.info("Installiere Modelle mit: ollama pull qwen2.5-coder:7b")
            logger.info("Befehl zum Starten: ollama serve")
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
            logger.info(f"✓ Ausgewählt: {selected['name']}")
            return "ollama", selected["name"]

        sys.exit(0)
