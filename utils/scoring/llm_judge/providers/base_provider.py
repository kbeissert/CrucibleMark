"""
Abstract base class for all LLM Judge providers.
Every provider must implement complete() and health_check().
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class JudgeProviderResponse:
    """Standardised response returned by every provider."""

    raw_text: str
    model_id: str
    provider_name: str
    latency_ms: float


class LLMJudgeProvider(ABC):
    """
    Contract every LLM Judge provider must satisfy.

    Subclasses must implement:
    - complete(system_prompt, user_prompt) -> JudgeProviderResponse
    - health_check() -> bool

    Provider selection is done via config; the runner never branches on
    provider type directly.
    """

    @abstractmethod
    def complete(self, system_prompt: str, user_prompt: str) -> JudgeProviderResponse:
        """
        Send a prompt to the underlying LLM and return a structured response.

        Args:
            system_prompt: The system-level instruction for the judge.
            user_prompt: The user-level payload (task + response + rubric).

        Returns:
            JudgeProviderResponse with raw text, model metadata, and latency.
        """

    @abstractmethod
    def health_check(self) -> bool:
        """
        Verify that the provider is reachable and the API key is valid.

        Returns:
            True if the provider is ready, False otherwise.
        """
