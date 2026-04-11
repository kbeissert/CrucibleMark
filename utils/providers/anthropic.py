"""
Provider-spezifische LLM Clients
Getrennte Implementierungen für Ollama, Anthropic, Mistral
"""
import time
import logging
from typing import Any, List, Optional, Callable
from utils.constants import MAX_TOKENS_ANTHROPIC, TIMEOUT_ANTHROPIC_API
from utils.env_utils import get_required_env
# Optional Provider Imports
try:
    pass
except ImportError:
    ollama = None
try:
    import anthropic
except ImportError:
    anthropic = None
try:
    pass
except ImportError:
    Mistral = None
try:
    pass
except ImportError:
    OpenAI = None
# Configure logging
logger = logging.getLogger(__name__)
from utils.providers.base import BaseProviderClient
class AnthropicClient(BaseProviderClient):
    """Anthropic Claude Provider Client"""
    PROVIDER_NAMES = ["anthropic"]

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self._client = None
        self.last_request_time = 0
        self.min_request_interval = self.config.get("anthropic", {}).get(
            "min_request_interval", 0.2
        )  # Default: 0.2s between requests
    @property
    def client(self):
        """Lazy-loaded Anthropic Client"""
        if self._client is None:
            if anthropic is None:
                raise ImportError("Library 'anthropic' not installed.")
            api_key = get_required_env(
                "ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY environment variable not set"
            )
            # timeout raised because huge 8000+ token generations can easily take 3-5 minutes
            self._client = anthropic.Anthropic(api_key=api_key, timeout=TIMEOUT_ANTHROPIC_API)
        return self._client
    def is_accessible(self) -> bool:
        """Prüft Zugang zu Anthropic API durch Test-Request."""
        try:
            # Versuche minimale Generierung (Cheap & Fast) mit max_retries=0
            check_client = anthropic.Anthropic(
                api_key=self.client.api_key, max_retries=0
            )
            check_client.messages.create(
                model="claude-3-haiku-20240307",  # Günstigstes Modell für Test
                max_tokens=1,
                messages=[{"role": "user", "content": "Hi"}],
            )
            return True
        except Exception as e:
            logger.debug("Anthropic Access Check Failed: %s", e)
            return False
    def _resolve_model(self, model: str) -> str:
        """Stellt sicher, dass ein konkretes Modell übergeben wurde."""
        if not model or model.lower() == "anthropic":
            raise ValueError(f"No specific Anthropic model provided. Received: '{model}'. A concrete model name must be provided (e.g. 'claude-haiku-4-5-20251001').")
        return model
    def query(
        self,
        model: str,
        prompt: str,
        temperature: float,
        stream_handler: Optional[Callable[[str], None]] = None,
        **kwargs,
    ) -> str:
        """Query Anthropic API"""
        # Rate Limit Protection
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            sleep_time = self.min_request_interval - elapsed
            logger.debug(f"⏱️ Rate limit protection: sleeping {sleep_time:.1f}s")
            time.sleep(sleep_time)
        self.last_request_time = time.time()
        try:
            model = self._resolve_model(model)
            # Default to config, but override with kwargs if present
            max_tokens = kwargs.get("max_tokens")
            if not max_tokens:
                max_tokens = self.config.get("anthropic", {}).get(
                    "max_tokens", MAX_TOKENS_ANTHROPIC
                )
            # Note: Streaming not implemented yet for Anthropic in this wrapper
            func_kwargs = {
                "model": model,
                "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}],
            }
            response, used_max_tokens, fallback_triggered = self._execute_with_token_fallback(
                func=self.client.messages.create,
                token_param_name="max_tokens",
                initial_max_tokens=max_tokens,
                error_keywords=["max_tokens"],
                func_kwargs=func_kwargs
            )
            # Capture Metadata
            self.last_response_metadata = {
                "model": response.model,
                "id": response.id,
                "usage": response.usage,
                "finish_reason": getattr(response, "stop_reason", None),
                "token_limit_fallback": fallback_triggered,
                "token_limit_used": used_max_tokens,
            }
            if (
                stream_handler
                and response.content
                and hasattr(response.content[0], "text")
            ):
                stream_handler(response.content[0].text)
            return response.content[0].text
        except Exception:
            # Let RetryHandler handle logging
            raise
    def get_available_models(self) -> List[str]:
        """Listet verfügbare Claude-Modelle"""
        return [
            "claude-sonnet-4-5-20250929",
            "claude-opus-4-5-20251101",
            "claude-3-haiku-20240307",
        ]
