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
from typing import Any, Optional, Tuple
import yaml
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


class ConfigValidator:
    """Validiert benchmark_config.yaml."""

    def __init__(self, config_path: str = "benchmark_config.yaml"):
        """Initialisiert Validator.

        Args:
            config_path: Pfad zur Config-Datei
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        """Lädt Config-Datei."""
        if not self.config_path.exists():
            logger.error("Config file not found: %s", self.config_path)
            raise FileNotFoundError(f"Config nicht gefunden: {self.config_path}")

        try:
            with open(self.config_path, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except (OSError, yaml.YAMLError) as e:
            logger.error("Failed to load config: %s", e)
            raise

    def get_golden_standard_config(self) -> Optional[dict[str, Any]]:
        """Holt Golden Standard Konfiguration.

        Returns:
            Golden Standard Config oder None
        """
        return self.config.get("golden_standard")

    def get_provider_config(self, provider_key: str) -> Optional[dict[str, Any]]:
        """Holt Provider-Konfiguration.

        Args:
            provider_key: Provider Key (z.B. 'mistral', 'anthropic')

        Returns:
            Provider Config oder None
        """
        return self.config.get("providers", {}).get("commercial", {}).get(provider_key)

    def validate_golden_standard(self) -> Tuple[bool, str]:
        """Validiert Golden Standard Konfiguration.

        Returns:
            (is_valid, message)
        """
        # Validation steps
        validations = [
            self._validate_gs_section_exists,
            self._validate_gs_provider_exists,
            self._validate_gs_provider_enabled,
            self._validate_gs_api_key,
            self._validate_gs_model_exists,
        ]

        for validation_func in validations:
            is_valid, message = validation_func()
            if not is_valid:
                return False, message

        # Erfolgreiche Validierung
        gs_config = self.get_golden_standard_config()
        if not gs_config:
            return False, "Golden Standard Config missing"

        provider_key = gs_config.get("provider")
        model_id = gs_config.get("model")

        if not provider_key or not model_id:
            return False, "Provider or Model missing in Golden Standard Config"

        provider_config = self.get_provider_config(provider_key)
        if not provider_config:
            return False, f"Provider Config for {provider_key} missing"

        model_config = next(
            (m for m in provider_config.get("models", []) if m.get("id") == model_id),
            {},
        )

        provider_name = provider_config.get("name", provider_key)
        model_name = model_config.get("name", model_id)
        description = gs_config.get("description", "Keine Beschreibung")

        return True, (
            f"✅ Golden Standard konfiguriert:\n"
            f"   Provider: {provider_name}\n"
            f"   Modell: {model_name}\n"
            f"   Info: {description}"
        )

    def _validate_gs_section_exists(self) -> Tuple[bool, str]:
        """Prüft ob golden_standard Sektion existiert."""
        gs_config = self.get_golden_standard_config()
        if not gs_config:
            return False, "❌ Keine 'golden_standard' Sektion in Config gefunden"

        provider_key = gs_config.get("provider")
        model_id = gs_config.get("model")

        if not provider_key:
            return False, "❌ Golden Standard: 'provider' fehlt"

        if not model_id:
            return False, "❌ Golden Standard: 'model' fehlt"

        return True, ""

    def _validate_gs_provider_exists(self) -> Tuple[bool, str]:
        """Prüft ob der konfigurierte Provider existiert."""
        gs_config = self.get_golden_standard_config()
        if not gs_config:
            return False, "Golden Standard Config missing"

        provider_key = gs_config.get("provider")
        if not provider_key:
            return False, "Provider key missing"

        provider_config = self.get_provider_config(provider_key)

        if not provider_config:
            available = list(
                self.config.get("providers", {}).get("commercial", {}).keys()
            )
            return False, (
                f"❌ Golden Standard Provider '{provider_key}' existiert nicht\n"
                f"   Verfügbare Provider: {', '.join(available)}\n"
                f"   Korrigiere 'golden_standard.provider' in benchmark_config.yaml"
            )

        return True, ""

    def _validate_gs_provider_enabled(self) -> Tuple[bool, str]:
        """Prüft ob der Provider aktiviert ist."""
        gs_config = self.get_golden_standard_config()
        if not gs_config:
            return False, "Golden Standard Config missing"

        provider_key = gs_config.get("provider")
        if not provider_key:
            return False, "Provider key missing"

        provider_config = self.get_provider_config(provider_key)
        if not provider_config:
            return False, "Provider config missing"

        provider_name = provider_config.get("name", provider_key)

        if not provider_config.get("enabled", False):
            return False, (
                f"❌ Golden Standard Provider '{provider_name}' ist deaktiviert\n"
                f"   Setze 'providers.commercial.{provider_key}.enabled: true'"
            )

        return True, ""

    def _validate_gs_api_key(self) -> Tuple[bool, str]:
        """Prüft ob API Key gesetzt ist."""
        gs_config = self.get_golden_standard_config()
        if not gs_config:
            return False, "Golden Standard Config missing"

        provider_key = gs_config.get("provider")
        if not provider_key:
            return False, "Provider key missing"

        provider_config = self.get_provider_config(provider_key)
        if not provider_config:
            return False, "Provider config missing"

        provider_name = provider_config.get("name", provider_key)

        env_var = provider_config.get("env_var")
        if not env_var:
            return (
                False,
                f"❌ Provider '{provider_name}' hat keine 'env_var' konfiguriert",
            )

        api_key = os.getenv(env_var)
        if not api_key:
            return False, (
                f"❌ Golden Standard nicht verfügbar:\n"
                f"   Environment Variable '{env_var}' ist nicht gesetzt!\n"
                f"   Setze: export {env_var}='your-api-key'"
            )

        return True, ""

    def _validate_gs_model_exists(self) -> Tuple[bool, str]:
        """Prüft ob das konfigurierte Modell existiert."""
        gs_config = self.get_golden_standard_config()
        if not gs_config:
            return False, "Golden Standard Config missing"

        provider_key = gs_config.get("provider")
        model_id = gs_config.get("model")

        if not provider_key or not model_id:
            return False, "Provider or Model missing"

        provider_config = self.get_provider_config(provider_key)
        if not provider_config:
            return False, "Provider config missing"

        provider_name = provider_config.get("name", provider_key)

        models = provider_config.get("models", [])
        model_ids = [m.get("id") for m in models]

        if model_id not in model_ids:
            return False, (
                f"❌ Golden Standard Modell '{model_id}' existiert nicht bei {provider_name}\n"
                f"   Verfügbare Modelle: {', '.join(model_ids)}\n"
                f"   Korrigiere 'golden_standard.model' in benchmark_config.yaml"
            )

        return True, ""

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

    def get_golden_standard_csv(self) -> Path:
        """Holt Pfad zur Golden Standard CSV.

        Returns:
            Path zur CSV-Datei (dediziert für Golden Standard)
        """
        csv_file = self.config.get("output", {}).get(
            "golden_standard_csv", "benchmark_scores/golden_standard_benchmark.csv"
        )
        return Path(csv_file)

    def get_golden_standard_info(self) -> Optional[Tuple[str, str, dict[str, Any]]]:
        """Holt Golden Standard Provider, Modell und Provider-Config.

        Returns:
            (provider_key, model_id, provider_config) oder None
        """
        gs_config = self.get_golden_standard_config()
        if not gs_config:
            return None

        provider_key = gs_config.get("provider")
        model_id = gs_config.get("model")

        if not provider_key or not model_id:
            return None

        provider_config = self.get_provider_config(provider_key)
        if not provider_config:
            return None

        return provider_key, model_id, provider_config


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
