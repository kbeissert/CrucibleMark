from utils.constants import MS_PER_SECOND
"""
Anthropic provider for the LLM Judge.
Uses the official anthropic Python SDK.
Auth: ANTHROPIC_API_KEY environment variable.
"""

import logging
import os
import time
from typing import Any, Optional

from .base_provider import JudgeProviderResponse, LLMJudgeProvider

_TRANSIENT_STATUS_CODES = frozenset({408, 409, 429, 500, 502, 503, 504, 529})

try:
    _HEALTH_CHECK_MAX_ATTEMPTS = int(os.environ.get("CRUCIBLE_JUDGE_HEALTH_MAX_ATTEMPTS", "3"))
except (ValueError, TypeError):
    _HEALTH_CHECK_MAX_ATTEMPTS = 3
try:
    _HEALTH_CHECK_BACKOFF_SECONDS = float(os.environ.get("CRUCIBLE_JUDGE_HEALTH_BACKOFF", "1.0"))
except (ValueError, TypeError):
    _HEALTH_CHECK_BACKOFF_SECONDS = 1.0


def _is_transient_error(exc: BaseException) -> bool:
    """Return True if exc looks like a transient connectivity / capacity issue."""
    if anthropic_module is None:
        return False
    if isinstance(exc, (anthropic_module.APIConnectionError, anthropic_module.APITimeoutError)):
        return True
    if isinstance(exc, anthropic_module.APIStatusError):
        return exc.status_code in _TRANSIENT_STATUS_CODES
    return False

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
        latency_ms = (time.monotonic() - start) * MS_PER_SECOND
        raw_text: str = "".join(
            block.text for block in message.content if hasattr(block, "text")
        ) if message.content else ""
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
        """Ping the Anthropic API with a minimal request to verify connectivity.

        Retries transient errors (529 overloaded, 429 rate-limit, 5xx, network/timeout)
        with exponential backoff before declaring the judge unavailable. Permanent
        errors (auth, permission, bad-request) fail fast without retry.
        """
        for attempt in range(1, _HEALTH_CHECK_MAX_ATTEMPTS + 1):
            try:
                self._client.messages.create(
                    model=self._model,
                    max_tokens=10,
                    messages=[{"role": "user", "content": "ping"}],
                )
                if attempt > 1:
                    logger.info(
                        "Anthropic health check succeeded on attempt %d/%d",
                        attempt, _HEALTH_CHECK_MAX_ATTEMPTS,
                    )
                return True
            except Exception as exc:  # pylint: disable=broad-exception-caught
                if not _is_transient_error(exc) or attempt == _HEALTH_CHECK_MAX_ATTEMPTS:
                    logger.warning(
                        "Anthropic health check failed: %s", exc,
                    )
                    return False
                backoff = _HEALTH_CHECK_BACKOFF_SECONDS * (2 ** (attempt - 1))
                logger.info(
                    "Anthropic health check transient failure on attempt %d/%d "
                    "(%s: %s) — retrying in %.1fs",
                    attempt, _HEALTH_CHECK_MAX_ATTEMPTS,
                    type(exc).__name__, exc, backoff,
                )
                time.sleep(backoff)
        return False
