"""
LLM Parser Utility
Provides unified parsing logic for LLM responses and usage metadata.
"""

import re
from typing import Any


class LLMParser:
    """Handles response sanitization and token usage extraction."""

    @staticmethod
    def sanitize_response(response_text: str) -> str:
        """
        Sanitizes LLM output by removing loop hallucinations and reasoning artifacts.
        """
        if not response_text:
            return response_text

        # 1. Sanitize loop hallucinations (extreme character repetition)
        if len(response_text) > 1000:
            response_text = re.sub(
                r"(.)\1{500,}",
                r"\1\n\n> [!ERROR]\n> **[GENERATION LOOP DETECTED]** Das Framework hat eine Endlosschleife des Modells erkannt (extreme Zeichen-Wiederholung) und den defekten Textblock an dieser Stelle gekürzt.\n\n",
                response_text,
                flags=re.DOTALL
            )

            # 1.1 Sanitize structural loops (sentences or code blocks repeating)
            response_text = re.sub(
                r"(.{50,})\1{10,}",
                r"\1\n\n> [!ERROR]\n> **[GENERATION LOOP DETECTED]** Das Framework hat eine Endlosschleife des Modells erkannt (strukturelle Satz- oder Block-Wiederholung) und den defekten Textblock an dieser Stelle gekürzt.\n\n",
                response_text,
                flags=re.DOTALL
            )

        # 2. Sanitation: Remove Reasoning Artifacts (DeepSeek <think>)
        if "<think>" in response_text:
            response_text = re.sub(
                r"<think>.*?</think>", "", response_text, flags=re.DOTALL
            ).strip()
            # Cleanup potential empty lines left behind
            response_text = re.sub(r"\n{3,}", "\n\n", response_text)

        return response_text

    @staticmethod
    def extract_usage_tokens(usage: Any) -> tuple[int, int]:
        """
        Extracts input and output tokens from a generic provider usage object.
        Supports Anthropic, OpenAI, Mistral (dicts and objects).
        """
        if not usage:
            return 0, 0

        input_tokens = 0
        output_tokens = 0

        # Handle Anthropic Format (has input_tokens, output_tokens)
        if hasattr(usage, "input_tokens"):
            input_tokens = usage.input_tokens
            # output_tokens might be None
            output_tokens = getattr(usage, "output_tokens", 0) or 0

            # Wenn Cache Tokens vorhanden sind (Claude 3.5 Sonnet Cache read)
            if hasattr(usage, "cache_read_input_tokens") and usage.cache_read_input_tokens:
                input_tokens += usage.cache_read_input_tokens

        # Handle both object (Pydantic/API libs) and dict formats (OpenAI / Mistral)
        elif hasattr(usage, "prompt_tokens"):
            input_tokens = usage.prompt_tokens
            output_tokens = getattr(usage, "completion_tokens", 0) or 0
        elif isinstance(usage, dict):
            input_tokens = usage.get("prompt_tokens", usage.get("input_tokens", 0))
            output_tokens = usage.get("completion_tokens", usage.get("output_tokens", 0))

        return input_tokens, output_tokens
