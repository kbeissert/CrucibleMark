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
    pass
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

class XAIClient(BaseProviderClient):
    """XAI Provider Client"""

    def __init__(self, config: dict):
        super().__init__(config)
        self._client = None

    @property
    def client(self):
        """Lazy-loaded XAI Client using OpenAI wrapper"""
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError:
                raise ImportError("Library 'openai' not installed.")

            import httpx
            from utils.env_utils import get_required_env

            api_key = get_required_env(
                "XAI_API_KEY", "XAI_API_KEY environment variable not set"
            )

            timeout_config = httpx.Timeout(
                connect=10.0, read=180.0, write=180.0, pool=180.0
            )

            self._client = OpenAI(
                api_key=api_key,
                base_url="https://api.x.ai/v1",
                timeout=timeout_config
            )
        return self._client

    def is_accessible(self) -> bool:
        """Prüft Zugang zu XAI API."""
        try:
            from openai import OpenAI
            check_client = OpenAI(api_key=self.client.api_key, base_url="https://api.x.ai/v1", max_retries=0)
            check_client.chat.completions.create(
                model="grok-3-mini",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=1,
            )
            return True
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.debug("XAI Access Check Failed: %s", e)
            return False

    def query(
        self,
        model: str,
        prompt: str,
        temperature: float,
        stream_handler = None,
        **kwargs,
    ) -> str:
        """Query XAI API"""
        try:
            import logging
            logger = logging.getLogger(__name__)
            params = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
            }

            req_tokens = kwargs.get("max_tokens")
            if not req_tokens:
                req_tokens = self.config.get("defaults", {}).get("generation", {}).get("num_predict", 8192)

            params["max_completion_tokens"] = req_tokens

            if stream_handler:
                params["stream"] = True

            response, used_max_tokens, fallback_triggered = self._execute_with_token_fallback(
                func=self.client.chat.completions.create,
                token_param_name="max_completion_tokens",
                initial_max_tokens=req_tokens,
                error_keywords=["maximum context length", "max_tokens", "max_completion_tokens"],
                func_kwargs=params
            )

            if stream_handler:
                full_content = ""
                self.last_response_metadata = {
                    "token_limit_fallback": fallback_triggered,
                    "token_limit_used": used_max_tokens,
                }

                for chunk in response:
                    if not self.last_response_metadata.get("id") and chunk.id:
                        self.last_response_metadata["id"] = chunk.id
                    if not self.last_response_metadata.get("model") and chunk.model:
                        self.last_response_metadata["model"] = chunk.model

                    if chunk.choices and hasattr(chunk.choices[0], "finish_reason") and chunk.choices[0].finish_reason:
                        self.last_response_metadata["finish_reason"] = chunk.choices[0].finish_reason

                    if chunk.choices:
                        delta = chunk.choices[0].delta.content
                        if delta:
                            stream_handler(delta)
                            full_content += delta

                return full_content
            else:
                raw_text = response.choices[0].message.content

                self.last_response_metadata = {
                    "token_limit_fallback": fallback_triggered,
                    "token_limit_used": used_max_tokens,
                    "id": getattr(response, "id", None),
                    "model": getattr(response, "model", None),
                    "finish_reason": response.choices[0].finish_reason if response.choices else None,
                }

                if hasattr(response, "usage") and response.usage:
                    self.last_response_metadata["usage"] = response.usage

                return raw_text if raw_text else ""

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error("XAI API Error: %s", e)
            raise e

    def get_available_models(self) -> list:
        try:
            models = self.client.models.list()
            return [m.id for m in models.data]
        except Exception:
            return ["grok-3", "grok-3-mini"]
