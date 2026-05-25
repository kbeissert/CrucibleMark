"""
Provider-spezifische LLM Clients
Getrennte Implementierungen für Ollama, Anthropic, Mistral
"""
import time
import logging
from typing import Any, List, Optional, Callable
from utils.constants import MAX_TOKENS_ANTHROPIC, TIMEOUT_ANTHROPIC_API, ANTHROPIC_NO_TEMPERATURE_MODELS
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
            # base_url explicitly set to bypass VS Code / OpenRouter proxy (ANTHROPIC_BASE_URL env var)
            self._client = anthropic.Anthropic(
                api_key=api_key,
                timeout=TIMEOUT_ANTHROPIC_API,
                base_url="https://api.anthropic.com",
            )
        return self._client
    def is_accessible(self) -> bool:
        """Prüft Zugang zu Anthropic API durch Test-Request."""
        if anthropic is None:
            return False
        try:
            check_client = anthropic.Anthropic(
                api_key=self.client.api_key,
                max_retries=0,
                base_url="https://api.anthropic.com",
            )
            check_client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1,
                messages=[{"role": "user", "content": "Hi"}],
            )
            return True
        except anthropic.AuthenticationError as e:
            logger.warning("Anthropic Access Check: Authentifizierung fehlgeschlagen: %s", e)
            return False
        except anthropic.PermissionDeniedError as e:
            logger.warning("Anthropic Access Check: Zugriff verweigert (Budget/Permissions): %s", e)
            return False
        except anthropic.NotFoundError as e:
            # Testmodell nicht gefunden, aber API selbst ist erreichbar
            logger.warning("Anthropic Access Check: Testmodell nicht gefunden, API aber erreichbar: %s", e)
            return True
        except anthropic.RateLimitError as e:
            logger.warning("Anthropic Access Check: Rate Limit — API erreichbar: %s", e)
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
            func_kwargs: dict[str, Any] = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
            }
            system = kwargs.get("system")
            if system:
                func_kwargs["system"] = system
            if model not in ANTHROPIC_NO_TEMPERATURE_MODELS:
                func_kwargs["temperature"] = temperature
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
            stop_reason = getattr(response, "stop_reason", None)
            if stop_reason == "refusal":
                logger.warning("Anthropic API refusal for model %s", model)
                return ""
            text_blocks = [b for b in response.content if hasattr(b, "text") and b.type == "text"]
            text = text_blocks[0].text if text_blocks else ""
            if stream_handler and text:
                stream_handler(text)
            return text
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
