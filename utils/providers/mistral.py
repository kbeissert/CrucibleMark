"""
Provider-spezifische LLM Clients
Getrennte Implementierungen für Ollama, Anthropic, Mistral
"""

import os
import time
import logging
from typing import Any, List, Optional, Callable, Dict

from utils.ollama_config import CODING_BENCHMARK_OPTIONS, CREATIVE_BENCHMARK_OPTIONS
from utils.constants import MAX_TOKENS_ANTHROPIC, DEFAULT_MISTRAL_MODEL
from utils.env_utils import get_required_env
from utils.model_utils import is_reasoning_model

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

import warnings

try:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        pass
except ImportError:
    genai = None

# Configure logging
logger = logging.getLogger(__name__)


from utils.providers.base import BaseProviderClient

class MistralClient(BaseProviderClient):
    """Mistral AI Provider Client"""

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
        """Löst Modell-Name auf (Config-Fallback)"""
        # Nur wenn kein Modell oder der generische Provider-Name übergeben wurde, Fallback nutzen.
        if not model or model == "mistral":
            return self.config.get("mistral", {}).get("model", DEFAULT_MISTRAL_MODEL)
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

            # Mistral supports max_tokens
            max_tokens = kwargs.get("max_tokens")
            if not max_tokens:
                max_tokens = self.config.get("defaults", {}).get("generation", {}).get("num_predict", 8192)

            # Note: Streaming not implemented yet for Mistral in this wrapper
            func_kwargs = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "random_seed": 42,
            }

            response, used_max_tokens, fallback_triggered = self._execute_with_token_fallback(
                func=self.client.chat.complete,
                token_param_name="max_tokens",
                initial_max_tokens=max_tokens,
                error_keywords=["maximum context length", "max_tokens", "too large"],
                func_kwargs=func_kwargs
            )

            # Capture Metadata
            self.last_response_metadata = {
                "model": response.model,
                "id": response.id,
                "usage": response.usage,
                "token_limit_fallback": fallback_triggered,
                "token_limit_used": used_max_tokens,
                "finish_reason": getattr(response.choices[0], "finish_reason", None) if response.choices else None,
            }

            content = response.choices[0].message.content
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


