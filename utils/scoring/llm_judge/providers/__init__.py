"""
LLM Judge Provider package.
Exposes the abstract base class and factory helper for provider lookup.
"""

from .base_provider import LLMJudgeProvider, JudgeProviderResponse

__all__ = ["LLMJudgeProvider", "JudgeProviderResponse"]
