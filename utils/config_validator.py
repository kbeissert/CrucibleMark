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


    def get_provider_config(self, provider_key: str) -> Optional[dict[str, Any]]:
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
