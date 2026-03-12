"""
Anthropic provider for the LLM Judge.
Uses the official anthropic Python SDK.
Auth: ANTHROPIC_API_KEY environment variable.
"""

import logging
import time
from typing import Any, Optional

from .base_provider import JudgeProviderResponse, LLMJudgeProvider

# Optional import guard: declared before try-block as per project convention
anthropic_module: Optional[Any] = None
try:
    import anthropic as anthropic_module  # type: ignore[no-redef]
except ImportError:
    pass

logger = logging.getLogger(__name__)


class AnthropicProvider(LLMJudgeProvider):
    """
    LLM Judge provider backed by the Anthropic API.

    Configuration keys:
        model           – default: claude-haiku-4-5
        temperature     – default: 0.1
        max_tokens      – default: 1024
        timeout_seconds – default: 30
    """

    PROVIDER_NAME = "anthropic"

    def __init__(
        self, model: str, temperature: float, max_tokens: int, timeout_seconds: int
    ) -> None:
        if anthropic_module is None:
            raise ImportError(
                "The 'anthropic' package is required for AnthropicProvider. "
                "Install it with: pip install anthropic"
            )
        from utils.env_utils import get_required_env

        api_key = get_required_env("ANTHROPIC_API_KEY")
        self._client = anthropic_module.Anthropic(
            api_key=api_key, timeout=float(timeout_seconds)
        )
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens

    def complete(self, system_prompt: str, user_prompt: str) -> JudgeProviderResponse:
        """Send a message to the Anthropic API and return a structured response."""
        start = time.monotonic()
        message = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            temperature=self._temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        latency_ms = (time.monotonic() - start) * 1000.0
        raw_text: str = message.content[0].text if message.content else ""
        logger.debug(
            "Anthropic judge response received (model=%s, latency=%.0f ms)",
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
        """Ping the Anthropic API with a minimal request to verify connectivity."""
        try:
            self._client.messages.create(
                model=self._model,
                max_tokens=10,
                messages=[{"role": "user", "content": "ping"}],
            )
            return True
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.warning("Anthropic health check failed: %s", exc)
            return False
