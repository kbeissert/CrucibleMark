"""Validierung der Benchmark-Konfiguration.

Prüft:
- Golden Standard korrekt konfiguriert (Provider-Referenz)
- Provider existiert und ist aktiviert
- API Keys vorhanden
- Modell existiert beim Provider
"""

import os
import logging
from pathlib import Path
from typing import Any
import yaml
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Provider-Config liegt im config/-Verzeichnis (relativ zum Projekt-Root)
PROVIDER_CONFIG_PATH = Path("config/provider_config.yaml")


class ConfigValidator:
    """Validiert benchmark_config.yaml und merged provider_config.yaml."""

    def __init__(self, config_path: str = "benchmark_config.yaml"):
        """Initialisiert Validator.

        Args:
            config_path: Pfad zur Benchmark-Config (ohne providers-Block)
        """
        self.config_path = Path(config_path)
        self.provider_config_path = PROVIDER_CONFIG_PATH
        self.config = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        """Lädt benchmark_config.yaml, merged provider_config.yaml und prüft auf Duplikat-IDs."""
        if not self.config_path.exists():
            logger.error("Config file not found: %s", self.config_path)
            raise FileNotFoundError(f"Config nicht gefunden: {self.config_path}")

        try:
            with open(self.config_path, encoding="utf-8") as f:
                config: dict[str, Any] = yaml.safe_load(f) or {}
        except (OSError, yaml.YAMLError) as e:
            logger.error("Failed to load config: %s", e)
            raise

        # Provider-Config einblenden (SCSS-Partial-Prinzip)
        if self.provider_config_path.exists():
            try:
                with open(self.provider_config_path, encoding="utf-8") as f:
                    provider_data: dict[str, Any] = yaml.safe_load(f) or {}
                providers = provider_data.get("providers")
                if providers:
                    config["providers"] = providers
                    # Thinking-Profil-Expansion: vLLM-Modelle mit
                    # ``enable_thinking: true`` werden transparent in zwei
                    # Einträge aufgespalten (Standard + Thinking). Muss VOR
                    # der Duplikat-Prüfung laufen, damit die generierten
                    # ``{id}-thinking``-IDs in den Check einbezogen werden.
                    self._expand_thinking_profiles(providers)
                    self._check_duplicate_model_ids(providers)
            except (OSError, yaml.YAMLError) as e:
                logger.error("Failed to load provider_config.yaml: %s", e)
                raise
        else:
            logger.warning(
                "provider_config.yaml nicht gefunden (%s) — kein Provider geladen.",
                self.provider_config_path,
            )

        return config

    def _expand_thinking_profiles(self, providers: dict[str, Any]) -> None:
        """Expändiert vLLM-Modelle mit ``enable_thinking: true`` in zwei Profile.

        Pro ``enable_thinking: true``-Eintrag werden zwei Einträge erzeugt:

        * **Standard-Profil** (Original-ID): ``enable_thinking`` wird
          konsumiert, dafür explizit ``chat_template_kwargs: {"enable_thinking": False}``
          gesetzt — verhindert, dass das TOML/Server-Default-Verhalten Thinking
          ungewollt aktiviert.
        * **Thinking-Profil** (``{id}-thinking``): zeigt per ``card_model_id``
          auf dieselbe Card wie das Original, hebt aber ``enable_thinking`` per
          ``chat_template_kwargs: {"enable_thinking": True}`` an und übernimmt
          ``thinking_max_tokens`` (provider-default > per-Modell-Override).

        Beide Profile zeigen auf dasselbe TOML (``config`` identisch) → der
        vLLM-Connector erkennt die Identität und führt keinen Container-Swap
        durch (per-Request-Param-Wechsel reicht).

        Wichtig: Nur Provider mit ``api_type == "vllm"`` werden expandiert.
        llama.cpp nutzt ``enable_thinking`` als Server-Flag (``--reasoning off``)
        mit abweichender Semantik — eine automatische Expansion würde dort
        fehlerhafte Einträge erzeugen.
        """
        for section_key, section in providers.items():
            if not isinstance(section, dict):
                continue
            for prov_key, prov_cfg in section.items():
                if not isinstance(prov_cfg, dict):
                    continue
                if prov_cfg.get("api_type") != "vllm":
                    continue
                models = prov_cfg.get("models")
                if not isinstance(models, list):
                    continue
                expanded: list[dict[str, Any]] = []
                for model in models:
                    if not isinstance(model, dict) or not model.get("enable_thinking"):
                        expanded.append(model)
                        continue
                    original_id = model.get("id")
                    original_name = model.get("name", original_id or "")
                    if not original_id:
                        expanded.append(model)
                        continue

                    thinking_max_tokens = model.get(
                        "thinking_max_tokens",
                        prov_cfg.get("thinking_max_tokens"),
                    )
                    if thinking_max_tokens is None:
                        raise ValueError(
                            f"vLLM-Modell '{original_id}' (Provider {prov_key}) hat "
                            f"'enable_thinking: true' aber kein 'thinking_max_tokens' — "
                            f"weder im model_cfg noch im Provider-Default. "
                            f"Bitte 'thinking_max_tokens' setzen (z.B. 32768)."
                        )

                    # Original-Eintrag: enable_thinking konsumieren,
                    # explizit auf False in chat_template_kwargs setzen.
                    # dual_profile markiert beide Einträge als Shared-Card-Profile.
                    standard = dict(model)
                    standard.pop("enable_thinking", None)
                    standard["chat_template_kwargs"] = {"enable_thinking": False}
                    standard["dual_profile"] = True
                    expanded.append(standard)

                    # Thinking-Eintrag: eigener id-Suffix, gleiche Card,
                    # höheres max_tokens-Budget.
                    thinking_entry = dict(model)
                    thinking_entry.pop("enable_thinking", None)
                    thinking_entry["id"] = f"{original_id}-thinking"
                    thinking_entry["name"] = f"{original_name} Thinking"
                    thinking_entry["card_model_id"] = original_id
                    thinking_entry["chat_template_kwargs"] = {"enable_thinking": True}
                    thinking_entry["max_tokens"] = thinking_max_tokens
                    thinking_entry["dual_profile"] = True
                    expanded.append(thinking_entry)

                prov_cfg["models"] = expanded

    def _check_duplicate_model_ids(self, providers: dict[str, Any]) -> None:
        """Prüft alle expliziten Modell-IDs auf Duplikate über alle Provider hinweg.

        Duplikate werden als WARNING geloggt. Der erste Eintrag gewinnt (First-Win).
        auto_discover-Provider (Ollama) werden übersprungen.
        """
        seen: dict[str, str] = {}  # model_id → "section/provider_key"

        for section_key, section in providers.items():
            if not isinstance(section, dict):
                continue
            for prov_key, prov_cfg in section.items():
                if not isinstance(prov_cfg, dict):
                    continue
                if prov_cfg.get("auto_discover"):
                    continue
                for model in prov_cfg.get("models", []):
                    if not isinstance(model, dict):
                        continue
                    mid = model.get("id")
                    if not mid:
                        continue
                    location = f"{section_key}/{prov_key}"
                    if mid in seen:
                        logger.warning(
                            "Duplikat-Modell-ID '%s': bereits registriert unter '%s', "
                            "Eintrag unter '%s' wird ignoriert.",
                            mid,
                            seen[mid],
                            location,
                        )
                    else:
                        seen[mid] = location


    def get_provider_config(self, provider_key: str) -> dict[str, Any] | None:
        """Holt Provider-Konfiguration.

        Args:
            provider_key: Provider Key (z.B. 'mistral', 'anthropic')

        Returns:
            Provider Config oder None
        """
        return self.config.get("providers", {}).get("commercial", {}).get(provider_key)

    def get_enabled_commercial_providers(self) -> dict[str, dict[str, Any]]:
        """Holt alle aktivierten kommerziellen Provider.

        Returns:
            Dict mit provider_key -> provider_config
        """
        commercial = self.config.get("providers", {}).get("commercial", {})
        return {
            key: provider
            for key, provider in commercial.items()
            if provider.get("enabled", False)
        }

    def validate_golden_standard(self) -> tuple[bool, str]:
        """Validiert die golden_standard Konfiguration."""
        try:
            # Check basic structure
            golden_std = self.config.get("golden_standard", {})
            if not golden_std:
                return False, "Fehlender 'golden_standard' Bereich in Konfiguration."

            provider_key = golden_std.get("provider")
            if not provider_key:
                return False, "Kein Provider für Golden Standard konfiguriert."

            # Verify provider exists and is enabled
            provider_cfg = self.get_provider_config(provider_key)
            if not provider_cfg:
                return False, f"Golden Standard Provider '{provider_key}' ist nicht in 'providers.commercial' konfiguriert."

            if not provider_cfg.get("enabled", False):
                return False, f"Golden Standard Provider '{provider_key}' ist deaktiviert (enabled: false)."

            # Verify API Key is available
            api_key_env = provider_cfg.get("api_key_env")
            if api_key_env and not os.getenv(api_key_env):
                return False, f"Fehlender API-Key für Golden Standard Provider: Environment Variable '{api_key_env}' nicht gesetzt."

            model = provider_cfg.get("model")
            if not model:
                return False, f"Kein Modell für Golden Standard Provider '{provider_key}' konfiguriert."

            return True, f"Golden Standard valide (Provider: {provider_key}, Modell: {model})"

        except Exception as e:
            return False, f"Interner Validierungsfehler: {e}"


def validate_config_quick() -> bool:
    """Schnelle Validierung für CLI-Tools.

    Returns:
        True wenn Golden Standard korrekt konfiguriert
    """
    try:
        validator = ConfigValidator()
        is_valid, message = validator.validate_golden_standard()
        logger.info(message)
        return is_valid
    except (OSError, yaml.YAMLError) as e:
        logger.error("Config-Validierung fehlgeschlagen: %s", e)
        return False
