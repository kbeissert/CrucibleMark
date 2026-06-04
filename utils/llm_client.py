"""
LLM Client Wrapper
Unified Interface für Ollama und Anthropic Claude API
"""

import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
import yaml  # pylint: disable=import-error

from utils.providers.base import BaseProviderClient
from utils.retry_handler import RetryHandler
from utils.llm_parser import LLMParser
from utils.cost_tracker import CostTracker
from utils.constants import (
    DEFAULT_TEMPERATURE,
    DEFAULT_MAX_RETRIES,
    TOKEN_ESTIMATE_RATIO,
)

# Initialize global providers via import (autodiscovery)

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
    - Cost Tracking für kommerzielle APIs
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialisiert LLM Client

        Args:
            config: Optionales Config-Dict (bereits geladen)
        """
        self.config = config or {}

        # Performance tracking
        self.last_query_duration = 0.0

        # Initialize provider clients based on dynamic registry
        self.clients = {}
        for name, cls in BaseProviderClient._registry.items():
            self.clients[name] = cls(self.config)

        # Initialize retry handler
        self.retry_handler = RetryHandler(max_retries=DEFAULT_MAX_RETRIES)

        # Initialize cost tracker
        self.cost_tracker = CostTracker()
        self.last_request_cost = 0.0
        self.last_response_metadata = {}

        # Load Model Version Locks
        self.model_locks = self._load_model_locks()

    def _load_model_locks(self) -> Dict[str, Any]:
        """Loads fixed model versions from config."""
        lock_path = Path("config/commercial_models_lock.yaml")
        if lock_path.exists():
            try:
                with open(lock_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    return data.get("providers", {})
            except Exception as e:
                logger.warning(f"Could not load model locks: {e}")
        return {}

    def _resolve_model_version(self, provider: str, model_alias: str) -> str:
        """Resolves generic model name to locked version if available."""
        if provider in self.model_locks:
            provider_locks = self.model_locks[provider]
            if model_alias in provider_locks:
                locked_version = provider_locks[model_alias].get("version")
                if locked_version:
                    # Changed to DEBUG to reduce console spam during batches (e.g. Political Compass)
                    logger.debug(
                        f"🔒 Model Lock: Using {locked_version} for {model_alias}"
                    )
                    return locked_version
        return model_alias

    _LOCAL_PROVIDERS = (
        "ollama",
        "llamacpp",
        "llamacpp_spark",
        "llama_cpp",
        "llamacpp_local",
    )

    @property
    def last_load_duration(self) -> float:
        """Returns the load duration of the last request (local providers only)."""
        for name in self._LOCAL_PROVIDERS:
            client = self.clients.get(name)
            if client and hasattr(client, "last_response_metadata"):
                val = client.last_response_metadata.get("load_duration", 0.0)
                if val:
                    return val
        return 0.0

    @property
    def last_pure_execution_time(self) -> float:
        """Returns execution time minus load time (local providers only)."""
        for name in self._LOCAL_PROVIDERS:
            client = self.clients.get(name)
            if client and hasattr(client, "last_response_metadata"):
                val = client.last_response_metadata.get("pure_execution_time", 0.0)
                if val:
                    return val
        return 0.0

    def query(  # pylint: disable=too-many-arguments, too-many-positional-arguments
        self,
        model: str,
        prompt: str,
        provider: str = "ollama",
        temperature: Optional[float] = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        stream_handler: Optional[Callable[[str], None]] = None,
        **kwargs,
    ) -> str:
        """
        Universelle Query-Methode mit Delegation an Provider-Clients, Retries und Budget-Check.

        Args:
           model: Modell-Name
           prompt: Prompt-Text
           provider: 'ollama', 'anthropic' oder 'mistral'
           temperature: Temperature (optional, nutzt Config-Default)
           max_retries: Maximum Anzahl Retry-Versuche
           stream_handler: Optionaler Callback (str -> None) für Streaming Output
           **kwargs: Weitere Provider-spezifische Parameter (z.B. max_tokens)

        Returns:
           Response-Text

        Raises:
           Exception: Bei fehlgeschlagener Query nach Retries
        """
        if provider not in self.clients:
            valid_providers = list(self.clients.keys())
            logger.error(
                "Unknown provider: %s. Available: %s", provider, valid_providers
            )
            # Default to ollama if unknown? No, raise error as before.
            # But earlier code raised ValueError
            raise ValueError(
                f"Unknown provider: {provider}. Available: {valid_providers}"
            )

        # call_type aus kwargs extrahieren (z.B. "overhead_ping")
        # Muss VOR _call_provider() passieren, da es kein gültiger Provider-Parameter ist.
        call_type = kwargs.pop("call_type", "benchmark")

        # Resolve Model Version (Locking)
        target_model = self._resolve_model_version(provider, model)

        if temperature is None:
            temperature = self.config.get("ollama", {}).get(
                "default_temperature", DEFAULT_TEMPERATURE
            )

        # Enable streaming output for commercial providers by default (configurable)
        use_default_stream = False
        streaming_setting = self.config.get("output", {}).get(
            "streaming_output_commercial_providers", True
        )
        streaming_disabled = (
            isinstance(streaming_setting, str)
            and streaming_setting.strip().lower() == "force"
        ) or (streaming_setting is False)

        if (
            not streaming_disabled
            and stream_handler is None
            and provider in ["anthropic", "openai", "mistral"]
        ):

            def _default_stream_printer(chunk: str) -> None:
                print(chunk, end="", flush=True)

            stream_handler = _default_stream_printer
            use_default_stream = True

        import time

        # 2. Ausführung
        def _call_provider():
            t_start = time.time()
            res = self.clients[provider].query(
                model=target_model,
                prompt=prompt,
                temperature=temperature,
                stream_handler=stream_handler,
                _provider_name=provider,
                **kwargs,
            )
            # Only record time if call succeeds (returns without exception)
            self.last_query_duration = time.time() - t_start
            return res

        # 3. Führe mit Retry-Logik aus
        self.last_output_tokens = 0  # reset; set to actual value after successful query
        response_text = self.retry_handler.execute_with_retry(
            _call_provider, max_retries=max_retries
        )

        response_text = LLMParser.sanitize_response(response_text)

        # Update Metadata from Client
        if hasattr(self.clients[provider], "last_response_metadata"):
            self.last_response_metadata = self.clients[provider].last_response_metadata

        # 3. Cost Tracking
        usage = (
            self.last_response_metadata.get("usage")
            if self.last_response_metadata
            else None
        )

        input_tokens, output_tokens = LLMParser.extract_usage_tokens(usage)

        # Fallback to estimation for Local/Ollama or if Usage missing
        if input_tokens == 0 and output_tokens == 0:
            input_tokens = self.estimate_tokens(prompt)
            output_tokens = self.estimate_tokens(response_text)

        cost = self.cost_tracker.track_request(
            provider, model, input_tokens, output_tokens, call_type=call_type
        )
        self.last_request_cost = cost
        self.last_output_tokens = output_tokens
        self.last_token_usage = input_tokens + output_tokens

        # Only log to file/logger, do not print to stdout which might clutter interactive CLI
        if cost > 0:
            logger.debug("Cost for request: $%.6f", cost)

        if use_default_stream:
            print()

        return response_text

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

    def get_available_models(self, provider: str = "ollama") -> List[str]:
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
