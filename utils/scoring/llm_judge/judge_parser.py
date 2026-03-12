"""
Parser for LLM Judge responses.
Extracts REASONING: and SCORE: blocks from raw text.

Handles edge cases:
  - Score wrapped in brackets: SCORE: [4]
  - Score as a word:  SCORE: four
  - Score on a separate line after the label
  - Missing REASONING section (non-fatal)
  - Completely missing SCORE (returns parse_success=False)

Never raises an exception from parse(); callers can check parse_success.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Word-to-integer mapping for written-out score words
# ---------------------------------------------------------------------------
_WORD_TO_INT: Dict[str, int] = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}

# Regex patterns (compiled once at import time)
_RE_SCORE = re.compile(
    r"(?:#{1,4}\s*)?(?:\*{1,2})?\s*SCORE\s*(?:\*{1,2})?[\s:\-]+(?:\*{1,2})?\s*[\[\(\"']?(\d+|one|two|three|four|five|six|seven|eight|nine|ten)[\]\)\"']?(?:\*{1,2})?",
    re.IGNORECASE | re.MULTILINE,
)

_RE_REASONING = re.compile(
    r"(?:-{3,}\s*\n\s*)?(?:#{1,4}\s*)?(?:\*{1,2})?\s*REASONING\s*(?:\*{1,2})?[\s:\-]+\s*(?:\*{1,2})?\s*(.*?)(?=(?:-{3,}\s*\n\s*)?(?:#{1,4}\s*)?(?:\*{1,2})?\s*SCORE|\Z)",
    re.IGNORECASE | re.DOTALL,
)


@dataclass
class JudgeResult:
    """Structured output of the judge parser."""

    score: Optional[int]
    reasoning: str
    raw_response: str
    parse_success: bool
    # Populated by judge_runner after parsing (not set by the parser itself)
    judge_latency_ms: Optional[float] = None
    judge_provider_used: Optional[str] = None
    judge_model_used: Optional[str] = None


def parse(raw_response: str) -> JudgeResult:
    """
    Parse a raw LLM judge response into a typed JudgeResult.

    The function is intentionally non-raising: on any parse failure it returns
    JudgeResult(score=None, parse_success=False, ...) and logs a warning.

    Args:
        raw_response: The complete text output from the judge LLM.

    Returns:
        JudgeResult with extracted score and reasoning.
    """
    reasoning = _extract_reasoning(raw_response)
    score = _extract_score(raw_response)

    if score is None:
        logger.warning(
            "LLM Judge: could not parse SCORE from response. "
            "Raw response (last 800 chars): %.800s",
            raw_response[-800:],
        )
        with open("last_failed_raw.txt", "w", encoding="utf-8") as f:
            f.write(raw_response)
        return JudgeResult(
            score=None,
            reasoning=reasoning,
            raw_response=raw_response,
            parse_success=False,
        )

    return JudgeResult(
        score=score,
        reasoning=reasoning,
        raw_response=raw_response,
        parse_success=True,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_score(text: str) -> Optional[int]:
    """
    Locate the SCORE marker and return the integer value.

    Accepts:
        SCORE: 4
        SCORE: [4]
        SCORE: "four"
        SCORE - 4
        score: 4          (case-insensitive)
    """
    matches = _RE_SCORE.findall(text)
    if not matches:
        return None

    # Always take the last match to avoid false positives in reasoning text
    raw_value = matches[-1].lower().strip()

    # Numeric string
    if raw_value.isdigit():
        return int(raw_value)

    # Written-out word
    return _WORD_TO_INT.get(raw_value)


def _extract_reasoning(text: str) -> str:
    """
    Extract the text block following the REASONING: label.

    Returns an empty string if REASONING: is absent (non-fatal).
    """
    match = _RE_REASONING.search(text)
    if not match:
        return ""
    return match.group(1).strip()
