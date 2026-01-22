"""
LLM Client Wrapper
Unified Interface für Ollama und Anthropic Claude API
"""

import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
import yaml  # pylint: disable=import-error

from utils.provider_clients import OllamaClient, AnthropicClient, MistralClient
from utils.retry_handler import RetryHandler
from utils.constants import DEFAULT_TEMPERATURE, DEFAULT_MAX_RETRIES, TOKEN_ESTIMATE_RATIO

# Configure logging
logger = logging.getLogger(__name__)


class LLMClient:
    """
    Universal LLM Client für Ollama, Anthropic und Mistral

    Features:
    - Unified Interface für alle Provider
    - Automatisches Fallback bei Fehlern
    - Token-Counting (approximiert)
    - Retry-Logik mit Exponential Backoff
    - Delegation an provider-spezifische Clients
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialisiert LLM Client

        Args:
            config: Optionales Config-Dict (bereits geladen)
        """
        self.config = config or {}

        # Initialize provider clients
        self.clients = {
            'ollama': OllamaClient(self.config),
            'anthropic': AnthropicClient(self.config),
            'mistral': MistralClient(self.config)
        }

        # Initialize retry handler
        self.retry_handler = RetryHandler(max_retries=DEFAULT_MAX_RETRIES)

    def query(  # pylint: disable=too-many-arguments, too-many-positional-arguments
        self,
        model: str,
        prompt: str,
        provider: str = 'ollama',
        temperature: Optional[float] = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        stream_handler: Optional[Callable[[str], None]] = None
    ) -> str:
        """
        Universelle Query-Methode mit Delegation an Provider-Clients

        Args:
            model: Modell-Name
            prompt: Prompt-Text
            provider: 'ollama', 'anthropic' oder 'mistral'
            temperature: Temperature (optional, nutzt Config-Default)
            max_retries: Maximum Anzahl Retry-Versuche
            stream_handler: Optionaler Callback (str -> None) für Streaming Output

        Returns:
            Response-Text

        Raises:
            ValueError: Bei unbekanntem Provider
            Exception: Bei fehlgeschlagener Query nach Retries
        """
        if provider not in self.clients:
            valid_providers = list(self.clients.keys())
            logger.error(
                "Unknown provider: %s. Available: %s", provider, valid_providers
            )
            raise ValueError(
                f"Unknown provider: {provider}. Available: {valid_providers}"
            )

        if temperature is None:
            temperature = self.config.get('ollama', {}).get(
                'default_temperature', DEFAULT_TEMPERATURE
            )

        # Update retry handler with custom max_retries
        self.retry_handler.max_retries = max_retries

        logger.debug("Querying %s model '%s' (temp=%s)", provider, model, temperature)

        # Delegate to provider-specific client with retry logic
        # Note: Streaming might complicate retries (partial output already sent).
        # Ideally, stream_handler checks are inside the client, but here we just pass it.
        # If streaming fails midway, retry logic repeats the whole query ->
        # user sees duplicate stream?
        # For this entertainment feature, duplicates on error are acceptable.

        return self.retry_handler.execute_with_retry(
            lambda: self.clients[provider].query(
                model, prompt, temperature, stream_handler=stream_handler
            )
        )

    def estimate_tokens(self, text: str) -> int:
        """
        Approximiert Token-Count

        Args:
            text: Text

        Returns:
            Geschätzte Anzahl Tokens (grobe Schätzung: 1 Token ≈ 4 Zeichen)
        """
        if not text:
            return 0
        return len(text) // TOKEN_ESTIMATE_RATIO

    def get_available_models(self, provider: str = 'ollama') -> List[str]:
        """
        Listet verfügbare Modelle

        Args:
            provider: 'ollama', 'anthropic' oder 'mistral'

        Returns:
            Liste von Modell-Namen
        """
        if provider in self.clients:
            try:
                return self.clients[provider].get_available_models()
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error("Failed to get models for %s: %s", provider, e)
                return []
        return []
