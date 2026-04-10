"""
Provider-spezifische LLM Clients
Getrennte Implementierungen für Ollama, Anthropic, Mistral
"""
import logging
from typing import Any, List, Optional, Callable
from utils.env_utils import get_required_env
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
    pass
except ImportError:
    Mistral = None
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None
# Configure logging
logger = logging.getLogger(__name__)
from utils.providers.base import BaseProviderClient
class OpenAIClient(BaseProviderClient):
    """OpenAI Provider Client"""
    PROVIDER_NAMES = ["openai"]

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self._client = None
    @property
    def client(self):
        """Lazy-loaded OpenAI Client"""
        if self._client is None:
            if OpenAI is None:
                raise ImportError("Library 'openai' not installed.")
            api_key = get_required_env(
                "OPENAI_API_KEY", "OPENAI_API_KEY environment variable not set"
            )
            # Configure explicit Timeout object for better handling of TTFT vs Connection
            # read=180.0s allows up to 3 mins wait for TTFT or between chunks
            # Note: httpx.Timeout does not accept 'total' argument in this version's constructor apparently,
            # or the way OpenAI client passes it down is specific.
            # Using connect/read/write/pool is standard for httpx used by OpenAI.
            import httpx
            timeout_config = httpx.Timeout(
                connect=10.0, read=180.0, write=180.0, pool=180.0
            )
            self._client = OpenAI(api_key=api_key, timeout=timeout_config)
        return self._client
    def is_accessible(self) -> bool:
        """Prüft Zugang zu OpenAI API (inkl. Quota Check)."""
        try:
            # list() reicht nicht für Quota Check (gibt oft success bei leerem Quota).
            # Daher führen wir eine minimale Generierung durch, um Billing-Status zu prüfen.
            # Eigener Client mit max_retries=0 um "Retrying..." Logs im Terminal zu vermeiden
            check_client = OpenAI(api_key=self.client.api_key, max_retries=0)
            check_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=1,
            )
            return True
        except Exception as e:
            # Fängt InsufficientQuotaError, AuthenticationError, etc.
            logger.debug("OpenAI Access Check Failed: %s", e)
            return False
    def query(
        self,
        model: str,
        prompt: str,
        temperature: float,
        stream_handler: Optional[Callable[[str], None]] = None,
        **kwargs,
    ) -> str:
        """Query OpenAI API"""
        try:
            params = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
            }
            # Reasoning models (o1, o3, o4) and some newer minis often don't support temperature
            # or have strict fixed values.
            is_reasoning = (
                model.startswith("o1") or model.startswith("o3") or model.startswith("o4") or "gpt-5" in model
            )
            if not is_reasoning:
                params["temperature"] = temperature
            token_param_name = "max_completion_tokens"  # OpenAI now universally prefers max_completion_tokens for newer models
            req_tokens = kwargs.get("max_tokens")
            explicit_budget = req_tokens is not None  # True wenn ein Modul-Budget-Cap explizit gesetzt wurde
            if not req_tokens:
                req_tokens = self.config.get("defaults", {}).get("generation", {}).get("num_predict", 8192)
            if is_reasoning and explicit_budget:
                # Reasoning-Modelle (o1/o3/gpt-5): token_budgets_reasoning_models lesen (transparent im Config).
                # Fallback: 5× das Standard-Budget wenn kein spezifischer Wert konfiguriert.
                # Hintergrund: max_completion_tokens umfasst Thinking-Tokens + sichtbaren Output.
                _reasoning_budgets = self.config.get("token_budgets_reasoning_models", {})
                _module_key = kwargs.get("_module_key")  # Optional von base_runner injiziert
                if _module_key and _module_key in _reasoning_budgets:
                    initial_tokens_to_try = _reasoning_budgets[_module_key]
                else:
                    initial_tokens_to_try = req_tokens * 5
            elif is_reasoning and req_tokens < 10000:
                # Ohne explizites Budget: Reasoning-Modelle brauchen Platz für Chain-of-Thought
                initial_tokens_to_try = 25000
            else:
                initial_tokens_to_try = req_tokens
            if stream_handler:
                params["stream"] = True
                # Request usage info in stream (OpenAI feature)
                params["stream_options"] = {"include_usage": True}
            response_or_stream, used_max_tokens, fallback_triggered = self._execute_with_token_fallback(
                func=self.client.chat.completions.create,
                token_param_name=token_param_name,
                initial_max_tokens=initial_tokens_to_try,
                error_keywords=["maximum context length", "max_tokens", "max_completion_tokens", "too large"],
                func_kwargs=params
            )
            if stream_handler:
                response_stream = response_or_stream
                full_content = ""
                self.last_response_metadata = {
                    "token_limit_fallback": fallback_triggered,
                    "token_limit_used": used_max_tokens,
                }
                for chunk in response_stream:
                    # Capture basic metadata from chunks
                    if not self.last_response_metadata.get("id") and chunk.id:
                        self.last_response_metadata["id"] = chunk.id
                    if not self.last_response_metadata.get("model") and chunk.model:
                        self.last_response_metadata["model"] = chunk.model
                    if getattr(chunk, "system_fingerprint", None):
                        self.last_response_metadata["system_fingerprint"] = (
                            chunk.system_fingerprint
                        )
                    # Capture Usage (usually in last chunk)
                    if hasattr(chunk, "usage") and chunk.usage:
                        self.last_response_metadata["usage"] = chunk.usage
                    if chunk.choices and hasattr(chunk.choices[0], "finish_reason") and chunk.choices[0].finish_reason:
                        self.last_response_metadata["finish_reason"] = chunk.choices[0].finish_reason
                    # Content
                    if chunk.choices:
                        delta = chunk.choices[0].delta.content
                        if delta:
                            stream_handler(delta)
                            full_content += delta
                return full_content
            # Blocking Call (Legacy / No Stream)
            response = response_or_stream
            # Capture Metadata
            self.last_response_metadata = {
                "model": response.model,
                "id": response.id,
                "system_fingerprint": getattr(response, "system_fingerprint", None),
                "usage": response.usage,
                "finish_reason": getattr(response.choices[0], "finish_reason", None) if response.choices else None,
                "token_limit_fallback": fallback_triggered,
                "token_limit_used": used_max_tokens,
            }
            content = response.choices[0].message.content or ""
            # Ensure we don't call stream_handler twice if falling back to blocking
            # The original code called it here, but since we have a dedicated stream branch,
            # this is only for the non-streaming case.
            # However, if the caller PROVIDED a stream_handler but somehow we ended up here
            # (which we shouldn't given the if above), we should call it.
            # But the 'if stream_handler' block handles that.
            return content
        except Exception as e:
            logger.error("OpenAI query failed: %s", e)
            raise
    def get_available_models(self) -> List[str]:
        """List available OpenAI models"""
        return ["gpt-5.2-pro", "gpt-5-mini", "o3-mini", "gpt-4o"]
