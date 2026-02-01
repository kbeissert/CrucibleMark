"""Module for structural and linguistic analysis of reasoning text."""

import re
from typing import Any

from .constants import (
    METACOG_ALTERNATIVES_KEYWORDS,
    METACOG_CONFIDENCE_KEYWORDS,
    METACOG_ITERATION_KEYWORDS,
    METACOG_SELF_CORRECTION_KEYWORDS,
    METACOG_UNCERTAINTY_KEYWORDS,
)


def contains_any(text: str, keywords: list[str]) -> bool:
    """Check if any keyword exists in text.

    Args:
        text (str): The text to search within (will be case-sensitive unless per-processed).
        keywords (list[str]): List of keyword strings to search for.

    Returns:
        bool: True if at least one keyword is found, False otherwise.
    """
    return any(k in text for k in keywords)


def parse_thought_tags(response: str) -> dict[str, Any]:
    """Extract <thought> and answer content from response.

    Supports multiple tag formats: <thought>, <think>, <thinking>, <reason>.

    Args:
        response (str): The full raw model response string.

    Returns:
        dict[str, Any]: A dictionary containing:
            - thought_content (str): Extracted internal reasoning.
            - thought_length (int): Word count of reasoning.
            - answer_content (str): The final answer text.
            - has_thought_tags (bool): Whether tags were successfully found.
            - thought_tag_type (str | None): The type of tag found (e.g. "<think>").
    """
    # Try different thought tag patterns (for different models)
    thought_patterns = [
        (r"<thought>(.*?)</thought>", "<thought>"),
        (r"<think>(.*?)</think>", "<think>"),  # DeepSeek R1
        (r"<thinking>(.*?)</thinking>", "<thinking>"),  # Alternative
        (r"<reason>(.*?)</reason>", "<reason>"),  # Alternative
    ]

    for pattern, tag_name in thought_patterns:
        thought_match = re.search(pattern, response, re.DOTALL)
        if thought_match:
            thought_content = thought_match.group(1).strip()
            thought_length = len(thought_content.split())

            # Extract answer (everything after closing tag)
            answer_start = thought_match.end()
            answer_content = response[answer_start:].strip()

            return {
                "has_thought_tags": True,
                "thought_content": thought_content,
                "thought_length": thought_length,
                "answer_content": answer_content,
                "thought_tag_type": tag_name,
            }

    # Fallback: Look for "Answer:" or "Final Answer:" separator
    # Many models (including DeepSeek R1 via Ollama sometimes) output reasoning text
    # followed by "Answer: X" without XML tags.
    split_patterns = [
        r"\nAnswer:",
        r"\nFinal Answer:",
        r"\n\*\*Answer:",
        r"\n\*\*Final Answer:",
        r"Answer: ",  # Case where it's not on new line but clearly labeled
    ]

    for pattern in split_patterns:
        split_match = re.search(pattern, response, re.IGNORECASE)
        if split_match:
            thought_content = response[: split_match.start()].strip()
            # answer_content usually includes the label (e.g. "Answer: X")
            answer_content = response[split_match.start() :].strip()

            # If thought is substantial (>5 words), treat it as thought
            if len(thought_content.split()) > 5:
                return {
                    "has_thought_tags": True,  # Virtual tags
                    "thought_content": thought_content,
                    "thought_length": len(thought_content.split()),
                    "answer_content": answer_content,
                    "thought_tag_type": "implicit_separator",
                }

    # No thought tags found
    return {
        "has_thought_tags": False,
        "thought_content": "",
        "thought_length": 0,
        "answer_content": response.strip(),
        "thought_tag_type": None,
    }


def detect_self_correction(thought: str) -> bool:
    """Detect self-correction keywords in thought process.

    Args:
        thought (str): The thought content to analyze.

    Returns:
        bool: True if self-correction keywords are present.
    """
    return contains_any(thought.lower(), METACOG_SELF_CORRECTION_KEYWORDS)


def detect_alternatives(thought: str) -> int:
    """Count alternative approach indicators in thought.

    Args:
        thought (str): The thought content to analyze.

    Args:
        thought (str): The thought content to analyze.

    Returns:
        dict[str, Any]: A dictionary containing:
            - has_confidence (bool): If confidence keywords exist.
            - has_uncertainty (bool): If uncertainty keywords exist.
            - confidence_type (str): 'calibrated', 'confident', or 'uncertain'.
    """
    return sum(1 for kw in METACOG_ALTERNATIVES_KEYWORDS if kw in thought.lower())


def detect_iteration(thought: str) -> bool:
    """Detect iterative refinement keywords in thought.

    Args:
        thought (str): The thought content to analyze.

    Returns:
        bool: True if iterative refinement keywords are present.
    """
    return contains_any(thought.lower(), METACOG_ITERATION_KEYWORDS)


def detect_confidence(thought: str) -> dict[str, Any]:
    """Analyze confidence expression in thought.

    Returns:
        dict with keys: has_confidence, has_uncertainty, confidence_type
    """
    thought_lower = thought.lower()
    has_confidence = contains_any(
        thought_lower, METACOG_CONFIDENCE_KEYWORDS,
    )
    has_uncertainty = contains_any(
        thought_lower, METACOG_UNCERTAINTY_KEYWORDS,
    )

    confidence_type = (
        "calibrated"
        if (has_confidence and has_uncertainty)
        else ("confident" if has_confidence else "uncertain")
    )

    return {
        "has_confidence": has_confidence,
        "has_uncertainty": has_uncertainty,
        "confidence_type": confidence_type,
    }
