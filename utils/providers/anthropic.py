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
    PROVIDER_CONFIG_KEY = "anthropic"
    DEFAULT_TOKEN_PARAM = "max_tokens"

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
            token_param_name, max_tokens = self._resolve_request_tokens(model, kwargs)
            func_kwargs: dict[str, Any] = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
            }
            system = kwargs.get("system")
            if system:
                func_kwargs["system"] = system
            if model not in ANTHROPIC_NO_TEMPERATURE_MODELS:
                func_kwargs["temperature"] = temperature
            if stream_handler:
                func_kwargs["stream"] = True
                return self._query_streaming(
                    model, max_tokens, func_kwargs, fallback_triggered=False
                )
            response, used_max_tokens, fallback_triggered = self._execute_with_token_fallback(
                func=self.client.messages.create,
                token_param_name="max_tokens",
                initial_max_tokens=max_tokens,
                error_keywords=["max_tokens"],
                func_kwargs=func_kwargs
            )
            # Capture Metadata
            reasoning_tokens = self._extract_reasoning_tokens(response.usage)
            think_content = self._extract_think_content(response.content)
            self.last_response_metadata = {
                "model": response.model,
                "id": response.id,
                "usage": response.usage,
                "finish_reason": getattr(response, "stop_reason", None),
                "token_limit_fallback": fallback_triggered,
                "token_limit_used": used_max_tokens,
                "reasoning_tokens": reasoning_tokens,
            }
            if think_content:
                self.last_response_metadata["think_content"] = think_content
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

    def _extract_reasoning_tokens(self, usage) -> int | None:
        """Delegiert an BaseProviderClient._extract_reasoning_tokens (SSoT).

        Anthropic nutzt ``output_tokens_details`` statt ``completion_tokens_details``.
        Die Base-Methode prüft beide Pfade.
        """
        return super()._extract_reasoning_tokens(usage)

    def _extract_think_content(self, content_blocks) -> str | None:
        """Extrahiere thinking-Content aus Anthropic ContentBlock-Liste."""
        think_parts: list[str] = []
        for block in content_blocks:
            if getattr(block, "type", None) == "thinking" and hasattr(block, "thinking"):
                thinking = block.thinking
                if thinking:
                    think_parts.append(str(thinking))
        return "".join(think_parts) if think_parts else None

    def _query_streaming(
        self,
        model: str,
        max_tokens: int,
        func_kwargs: dict[str, Any],
        fallback_triggered: bool = False,
    ) -> str:
        """Streaming-Query für Anthropic mit Thinking-Extraktion."""
        full_content = ""
        from utils.providers.base import ThinkAccumulator
        think = ThinkAccumulator()
        stream_usage = None
        model_name = None
        response_id = None
        stop_reason = None
        used_max_tokens = max_tokens

        try:
            response_stream = self.client.messages.create(**func_kwargs)
            for event in response_stream:
                # Capture metadata from stream events
                if event.type == "message_start":
                    model_name = event.message.model
                    response_id = event.message.id
                    stream_usage = event.message.usage
                elif event.type == "content_block_start":
                    block = event.content_block
                    if getattr(block, "type", None) == "thinking":
                        if hasattr(block, "thinking") and block.thinking:
                            think.add(block.thinking)
                elif event.type == "content_block_delta":
                    delta = event.delta
                    if hasattr(delta, "type") and delta.type == "thinking_delta":
                        if hasattr(delta, "thinking") and delta.thinking:
                            think.add(delta.thinking)
                            if stream_handler:
                                stream_handler(delta.thinking)
                    elif hasattr(delta, "type") and delta.type == "input_delta":
                        if hasattr(delta, "partial_json") and delta.partial_json:
                            full_content += delta.partial_json
                            if stream_handler:
                                stream_handler(delta.partial_json)
                elif event.type == "message_delta":
                    delta = event.delta
                    if hasattr(delta, "stop_reason"):
                        stop_reason = delta.stop_reason
                    if hasattr(delta, "usage"):
                        stream_usage = delta.usage

            used_max_tokens, fallback_triggered = self._get_used_max_tokens(
                max_tokens, stream_usage
            )

            self.last_response_metadata = {
                "model": model_name or model,
                "id": response_id,
                "usage": stream_usage,
                "finish_reason": stop_reason,
                "token_limit_fallback": fallback_triggered,
                "token_limit_used": used_max_tokens,
                "reasoning_tokens": self._extract_reasoning_tokens(stream_usage),
            }
            if think.has_content:
                self.last_response_metadata["think_content"] = think.content

        except Exception:
            raise

        return full_content

    def _get_used_max_tokens(self, initial: int, usage) -> tuple[int, bool]:
        """Ermittle tatsächliche max_tokens und ob Fallback ausgelöst wurde."""
        if not usage:
            return initial, False
        output = getattr(usage, "output_tokens", 0) or 0
        # Fallback: wenn output_tokens < initial, aber kein explizites Fallback-Signal
        return initial, False
    def get_available_models(self) -> List[str]:
        """Listet verfügbare Claude-Modelle"""
        return [
            "claude-sonnet-4-5-20250929",
            "claude-opus-4-5-20251101",
            "claude-3-haiku-20240307",
        ]
