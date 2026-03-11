"""
Mistral AI provider for the LLM Judge.
Uses the official mistralai Python SDK.
Auth: MISTRAL_API_KEY environment variable.
"""

import logging
import time
from typing import Any, Optional

from .base_provider import JudgeProviderResponse, LLMJudgeProvider

# Optional import guard: declared before try-block as per project convention
mistral_module: Optional[Any] = None
try:
    from mistralai import Mistral as mistral_module  # type: ignore[no-redef]
except ImportError:
    pass

logger = logging.getLogger(__name__)


class MistralProvider(LLMJudgeProvider):
    """
    LLM Judge provider backed by the Mistral AI API.

    Configuration keys:
        model           – default: mistral-small-latest
        temperature     – default: 0.1
        max_tokens      – default: 1024
        timeout_seconds – default: 30
    """

    PROVIDER_NAME = "mistral"

    def __init__(self, model: str, temperature: float, max_tokens: int, timeout_seconds: int) -> None:
        if mistral_module is None:
            raise ImportError(
                "The 'mistralai' package is required for MistralProvider. "
                "Install it with: pip install mistralai"
            )
        from utils.env_utils import get_required_env

        api_key = get_required_env("MISTRAL_API_KEY")
        self._client = mistral_module(api_key=api_key)
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._timeout = timeout_seconds

    def complete(self, system_prompt: str, user_prompt: str) -> JudgeProviderResponse:
        """Send a chat request to the Mistral API and return a structured response."""
        start = time.monotonic()
        response = self._client.chat.complete(
            model=self._model,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        latency_ms = (time.monotonic() - start) * 1000.0
        raw_text: str = ""
        if response.choices:
            raw_text = response.choices[0].message.content or ""
        logger.debug(
            "Mistral judge response received (model=%s, latency=%.0f ms)",
            self._model,
            latency_ms,
        )
        return JudgeProviderResponse(
            raw_text=raw_text,
            model_id=self._model,
            provider_name=self.PROVIDER_NAME,
            latency_ms=latency_ms,
        )

    def health_check(self) -> bool:
        """Verify Mistral API connectivity with a minimal request."""
        try:
            self._client.chat.complete(
                model=self._model,
                max_tokens=10,
                messages=[{"role": "user", "content": "ping"}],
            )
            return True
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.warning("Mistral health check failed: %s", exc)
            return False
