"""
Ollama provider for the LLM Judge.
Communicates with a local Ollama instance via its REST API.
No API key required; configurable base_url.
"""

from utils.constants import DEFAULT_UNLOAD_DELAY_MS
from utils.constants import MS_PER_SECOND

import logging
import time
from typing import Any

from utils.constants import OLLAMA_DEFAULT_BASE_URL
from .base_provider import JudgeProviderResponse, LLMJudgeProvider

# Optional import guard: declared before try-block as per project convention
requests_module: Any | None = None
try:
    import requests as requests_module  # type: ignore[no-redef]
except ImportError:
    pass

logger = logging.getLogger(__name__)

_CHAT_ENDPOINT = "/api/chat"
_HEALTH_ENDPOINT = "/api/tags"
_GENERATE_ENDPOINT = "/api/generate"


class OllamaProvider(LLMJudgeProvider):
    """
    LLM Judge provider backed by a locally running Ollama instance.

    No authentication required. Configure base_url in provider config.

    Configuration keys:
        model           – Ollama model tag (e.g. llama3.2)
        temperature     – default: 0.1
        max_tokens      – mapped to Ollama 'num_predict'
        timeout_seconds – default: 120
        base_url        – default: http://localhost:11434
    """

    PROVIDER_NAME = "ollama"

    def __init__(
        self,
        model: str,
        temperature: float,
        max_tokens: int,
        timeout_seconds: int,
        base_url: str = OLLAMA_DEFAULT_BASE_URL,
    ) -> None:
        if requests_module is None:
            raise ImportError(
                "The 'requests' package is required for OllamaProvider. "
                "Install it with: pip install requests"
            )
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._timeout = timeout_seconds
        self._base_url = base_url.rstrip("/")

    def complete(self, system_prompt: str, user_prompt: str) -> JudgeProviderResponse:
        """Call the Ollama /api/chat endpoint and return a structured response."""
        payload = {
            "model": self._model,
            "stream": False,
            "options": {
                "temperature": self._temperature,
                "num_predict": self._max_tokens,
            },
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        url = self._base_url + _CHAT_ENDPOINT
        start = time.monotonic()
        assert requests_module is not None; response = requests_module.post(url, json=payload, timeout=self._timeout)
        response.raise_for_status()
        latency_ms = (time.monotonic() - start) * MS_PER_SECOND
        data = response.json()
        raw_text: str = data.get("message", {}).get("content", "")
        logger.debug(
            "Ollama judge response received (model=%s, latency=%.0f ms)",
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
        """Check that the Ollama server is reachable and the model is available."""
        try:
            url = self._base_url + _HEALTH_ENDPOINT
            resp = requests_module.get(url, timeout=self._timeout)
            resp.raise_for_status()
            models = [m.get("name", "") for m in resp.json().get("models", [])]
            # Accept both exact match and prefix match (e.g. "llama3.2" in "llama3.2:latest")
            # Cloud models might not appear in /api/tags if they are proxied
            if "-cloud" in self._model.lower() or ":cloud" in self._model.lower():
                return True

            available = any(
                self._model == m or m.startswith(self._model) for m in models
            )
            if not available:
                logger.warning(
                    "Ollama model '%s' not found. Available: %s", self._model, models
                )
            return available
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.warning("Ollama health check failed: %s", exc)
            return False

    def unload_model(self, model_id: str, unload_delay_ms: int = DEFAULT_UNLOAD_DELAY_MS) -> bool:
        """
        Evict a model from Ollama's VRAM by setting keep_alive to 0.

        Blocks until Ollama confirms the unload (HTTP 200), then waits
        ``unload_delay_ms`` milliseconds so GPU memory is freed before the
        judge model loads.

        Sequence when called from judge_runner:
          [Benchmark task complete]
          → [unload_model called — confirmed OK]
          → [unload_delay_ms sleep]
          → [Judge model loads via complete()]

        This method never raises — failures are logged as warnings so that
        the judge can still attempt to run (possibly on a degraded system).

        Args:
            model_id: Ollama model tag to evict (e.g. ``"llama3.2"``).
            unload_delay_ms: Milliseconds to sleep after confirmed unload.
                             Passed from ProviderConfig.unload_delay_ms.

        Returns:
            True if Ollama confirmed the unload, False otherwise.
        """
        payload = {
            "model": model_id,
            "keep_alive": 0,
            "stream": False,
        }
        url = self._base_url + _GENERATE_ENDPOINT
        try:
            resp = requests_module.post(url, json=payload, timeout=self._timeout)
            resp.raise_for_status()
            logger.debug(
                "Ollama unload confirmed for model '%s' (status=%s).",
                model_id,
                resp.status_code,
            )
            if unload_delay_ms > 0:
                time.sleep(unload_delay_ms / MS_PER_SECOND)
            return True
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.warning("Ollama unload failed for model '%s': %s", model_id, exc)
            return False
