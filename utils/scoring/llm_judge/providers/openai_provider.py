"""
OpenAI provider for the LLM Judge.
Uses the official openai Python SDK.
Auth: OPENAI_API_KEY environment variable.
"""

import logging
import contextlib
import time
from typing import Any

from utils.constants import MS_PER_SECOND
from .base_provider import JudgeProviderResponse, LLMJudgeProvider

# Optional import guard: declared before try-block as per project convention
openai_module: Any | None = None
with contextlib.suppress(ImportError):
    import openai as openai_module  # type: ignore[no-redef]

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMJudgeProvider):
    """
    LLM Judge provider backed by the OpenAI API.

    Configuration keys:
        model           – default: gpt-4o-mini
        temperature     – default: 0.1
        max_tokens      – default: 1024
        timeout_seconds – default: 30
    """

    PROVIDER_NAME = "openai"

    def __init__(
        self, model: str, temperature: float, max_tokens: int, timeout_seconds: int
    ) -> None:
        if openai_module is None:
            raise ImportError(
                "The 'openai' package is required for OpenAIProvider. "
                "Install it with: pip install openai"
            )
        from utils.env_utils import get_required_env

        api_key = get_required_env("OPENAI_API_KEY")
        self._client = openai_module.OpenAI(
            api_key=api_key, timeout=float(timeout_seconds)
        )
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens

    def complete(self, system_prompt: str, user_prompt: str) -> JudgeProviderResponse:
        """Send a chat completion request to the OpenAI API."""
        start = time.monotonic()
        response = self._client.chat.completions.create(
            model=self._model,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        latency_ms = (time.monotonic() - start) * MS_PER_SECOND
        raw_text: str = ""
        if response.choices:
            raw_text = response.choices[0].message.content or ""
        logger.debug(
            "OpenAI judge response received (model=%s, latency=%.0f ms)",
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
        """Verify OpenAI API connectivity with a minimal request."""
        try:
            self._client.chat.completions.create(
                model=self._model,
                max_tokens=5,
                messages=[{"role": "user", "content": "ping"}],
            )
            return True
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.warning("OpenAI health check failed: %s", exc)
            return False
