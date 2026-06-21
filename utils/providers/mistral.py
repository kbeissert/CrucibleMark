"""
Provider-spezifische LLM Clients
Getrennte Implementierungen für Ollama, Anthropic, Mistral
"""
import os
import logging
from typing import Any, List, Optional, Callable
# Optional Provider Imports
try:
    pass
except ImportError:
    ollama = None
try:
    pass
except ImportError:
    anthropic = None
try:
    from mistralai import Mistral
except ImportError:
    Mistral = None
try:
    pass
except ImportError:
    OpenAI = None
# Configure logging
logger = logging.getLogger(__name__)
from utils.providers.base import BaseProviderClient
class MistralClient(BaseProviderClient):
    """Mistral AI Provider Client"""
    PROVIDER_NAMES = ["mistral"]
    PROVIDER_CONFIG_KEY = "mistral"
    DEFAULT_TOKEN_PARAM = "max_tokens"

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self._client = None
    @property
    def client(self):
        """Lazy-loaded Mistral Client"""
        if self._client is None:
            if Mistral is None:
                raise ImportError("Library 'mistralai' not installed.")
            # Support both MISTRAL_API_KEY and CODESTRAL_API_KEY
            # Using basic retrieval since OR logic prevents simple get_required_env usage
            api_key = os.environ.get("MISTRAL_API_KEY") or os.environ.get(
                "CODESTRAL_API_KEY"
            )
            if not api_key:
                raise ValueError(
                    "MISTRAL_API_KEY or CODESTRAL_API_KEY environment variable not set"
                )
            # Set explicit timeout (120s) to avoid indefinite hangs on API congestion
            self._client = Mistral(api_key=api_key, timeout_ms=120000)
        return self._client
    def is_accessible(self) -> bool:
        """Prüft Zugang zu Mistral API."""
        try:
            # Mistral client usually supports listing models as a cheap check
            self.client.models.list()
            return True
        except Exception as e:
            logger.debug("Mistral Access Check Failed: %s", e)
            return False
    def _resolve_model(self, model: str) -> str:
        """Stellt sicher, dass ein konkretes Modell übergeben wurde."""
        if not model or model.lower() == "mistral":
            raise ValueError(f"No specific Mistral model provided. Received: '{model}'. A concrete model name must be provided (e.g. 'mistral-large-latest').")
        return model
    def query(
        self,
        model: str,
        prompt: str,
        temperature: float,
        stream_handler: Optional[Callable[[str], None]] = None,
        **kwargs,
    ) -> str:
        """Query Mistral API"""
        try:
            model = self._resolve_model(model)
            token_param_name, max_tokens = self._resolve_request_tokens(model, kwargs)
            # Note: Streaming not implemented yet for Mistral in this wrapper
            _system = kwargs.get("system")
            func_kwargs = {
                "model": model,
                "messages": (
                    [{"role": "system", "content": _system}] if _system else []
                ) + [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "random_seed": 42,
            }
            response, used_max_tokens, fallback_triggered = self._execute_with_token_fallback(
                func=self.client.chat.complete,
                token_param_name=token_param_name,
                initial_max_tokens=max_tokens,
                error_keywords=["maximum context length", "max_tokens", "too large"],
                func_kwargs=func_kwargs
            )
            # Capture Metadata
            usage = response.usage
            reasoning_tokens = self._extract_reasoning_tokens(usage)
            self.last_response_metadata = {
                "model": response.model,
                "id": response.id,
                "usage": usage,
                "token_limit_fallback": fallback_triggered,
                "token_limit_used": used_max_tokens,
                "finish_reason": getattr(response.choices[0], "finish_reason", None) if response.choices else None,
                "reasoning_tokens": reasoning_tokens,
            }
            content = response.choices[0].message.content
            # Reasoning models (e.g. magistral) return a list of chunks
            # [ThinkChunk(...), TextChunk(...)]. Extract text and think parts separately.
            # chunk.text / chunk.thinking can be str OR list[str] depending on SDK version —
            # use _chunk_to_str() to normalize both cases.
            if isinstance(content, list):
                def _chunk_to_str(val: object) -> str:
                    """Normalize a chunk field to plain string.

                    chunk.text / chunk.thinking can be:
                    - str (normal case)
                    - list[str] (some SDK versions)
                    - list[chunk-like objects] (Magistral Small: thinking contains
                      nested TextChunk objects with a .text attribute)
                    Never fall back to repr(obj) — that would leak object strings
                    into the scorer and cause false-positive keyword matches.
                    """
                    if isinstance(val, str):
                        return val
                    if isinstance(val, list):
                        parts = []
                        for x in val:
                            if isinstance(x, str):
                                parts.append(x)
                            elif hasattr(x, "text") and isinstance(getattr(x, "text", None), str):
                                parts.append(x.text)
                            # deliberately skip unknown objects — no repr() fallback
                        return "".join(parts)
                    return ""

                text_parts = [
                    _chunk_to_str(getattr(chunk, "text", None))
                    for chunk in content
                    if getattr(chunk, "type", None) == "text"
                ]
                think_parts = [
                    _chunk_to_str(getattr(chunk, "thinking", None))
                    for chunk in content
                    if getattr(chunk, "type", None) == "thinking" and getattr(chunk, "thinking", None)
                ]
                content = "".join(text_parts)
                # If TextChunk is empty but ThinkChunk has content, store it as metadata
                # so the audit log can surface it as informational context
                if think_parts:
                    self.last_response_metadata["think_content"] = "".join(think_parts)
            if stream_handler and content:
                stream_handler(content)
            return content
        except Exception:
            # Let RetryHandler handle logging
            raise
    def get_available_models(self) -> List[str]:
        """Listet verfügbare Mistral-Modelle"""
        return [
            "mistral-large-latest",
            "mistral-medium-latest",
            "mistral-small-latest",
            "open-mistral-7b",
        ]
