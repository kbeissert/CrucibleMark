"""
Google Gemini provider for the LLM Judge.
Uses the google.generativeai SDK.
Auth: GOOGLE_API_KEY environment variable.
"""

import logging
import contextlib
import time
from typing import Any

from utils.constants import MS_PER_SECOND
from .base_provider import JudgeProviderResponse, LLMJudgeProvider

# Optional import guard: declared before try-block as per project convention
genai: Any | None = None
with contextlib.suppress(ImportError):
    import google.generativeai as genai  # type: ignore

logger = logging.getLogger(__name__)


class GoogleProvider(LLMJudgeProvider):
    """
    LLM Judge provider backed by the Google Gemini API.

    Configuration keys:
        model           - default: gemini-2.5-pro
        temperature     - default: 0.1
        max_tokens      - default: 1024
        timeout_seconds - default: 30
    """

    PROVIDER_NAME = "google"

    def __init__(
        self, model: str, temperature: float, max_tokens: int, timeout_seconds: int
    ) -> None:
        if genai is None:
            raise ImportError(
                "The 'google-generativeai' package is required for GoogleProvider. "
                "Install it with: pip install google-generativeai"
            )
        from utils.env_utils import get_required_env

        api_key = get_required_env("GOOGLE_API_KEY")
        genai.configure(api_key=api_key)

        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        # Google Generative AI SDK handles passing deadlines/timeouts natively?
        # Actually in generation_config or we just ignore timeout for now as it's not strictly easily passed to `generate_content`.
        self._timeout_seconds = timeout_seconds

    def complete(self, system_prompt: str, user_prompt: str) -> JudgeProviderResponse:
        """Send a chat completion request to the Google Gemini API."""
        start = time.monotonic()

        # Configure model with system prompt
        gemini_model = genai.GenerativeModel(
            model_name=self._model,
            system_instruction=system_prompt
        )

        generation_config = genai.types.GenerationConfig(
            temperature=self._temperature,
            max_output_tokens=self._max_tokens,
        )

        response = gemini_model.generate_content(
            user_prompt,
            generation_config=generation_config
        )

        latency_ms = (time.monotonic() - start) * MS_PER_SECOND

        raw_text: str = ""
        try:
            raw_text = response.text
        except ValueError as exc:
            # If the response doesn't contain text (e.g. blocked by safety).
            logger.error("Google Gemini returned an empty/blocked response: %s", exc)
            raw_text = ""

        logger.debug(
            "Google judge response received (model=%s, latency=%.0f ms)",
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
        """Verify Google API connectivity with a minimal request."""
        try:
            # Just listing models is a good lightweight health check
            next(genai.list_models(), None)
            return True
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.warning("Google health check failed: %s", exc)
            return False
