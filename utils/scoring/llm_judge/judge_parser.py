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

import json
import logging
import re
from dataclasses import dataclass
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Word-to-integer mapping for written-out score words
# ---------------------------------------------------------------------------
_WORD_TO_INT: Dict[str, int] = {
    "zero": 0,
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
    r"(?:#{1,4}\s*)?(?:\*{1,2})?\s*SCORE\s*(?:\*{1,2})?[\s:\-]+(?:\*{1,2})?\s*[\[\(\"']?(\d+|zero|one|two|three|four|five|six|seven|eight|nine|ten)[\]\)\"']?(?:\*{1,2})?",
    re.IGNORECASE | re.MULTILINE,
)

_RE_REASONING_START = re.compile(
    r"(?:-{3,}\s*\n\s*)?(?:#{1,4}\s*)?(?:\*{1,2})?\s*REASONING\s*(?:\*{1,2})?[\s:\-]+\s*(?:\*{1,2})?\s*",
    re.IGNORECASE,
)


@dataclass
class JudgeResult:
    """Structured output of the judge parser."""

    score: Optional[float]
    reasoning: str
    raw_response: str
    parse_success: bool
    # Populated by judge_runner after parsing (not set by the parser itself)
    judge_latency_ms: Optional[float] = None
    judge_provider_used: Optional[str] = None
    judge_model_used: Optional[str] = None

    # Sub-scores
    judge_task_compliance: Optional[float] = None
    judge_output_quality: Optional[float] = None
    judge_standard_adherence: Optional[float] = None
    judge_content_grounding: Optional[float] = None
    # Tool-use grounding fields (populated when tool_content was passed to the judge)
    hallucination_detected: Optional[bool] = None


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

    # Try to extract from JSON first since prompt enforces JSON format
    json_data = _extract_json_block(raw_response)

    # Initialize variables
    score = None
    sub_scores = None

    if json_data:
        raw_score = json_data.get("score")
        if isinstance(raw_score, (int, float)):
            score = float(raw_score)
        elif isinstance(raw_score, str):
            try:
                score = float(raw_score)
            except ValueError:
                score = None
        else:
            score = None

        sub_scores = json_data.get("sub_scores")

    # If JSON parse fails or is missing, try legacy text parsing
    if score is None:
        score = _extract_score(raw_response)

    if sub_scores is None:
        sub_scores = _extract_sub_scores_legacy(raw_response)

    judge_task_compliance = sub_scores.get("task_compliance") if sub_scores else None
    judge_output_quality = sub_scores.get("output_quality") if sub_scores else None
    judge_standard_adherence = sub_scores.get("standard_adherence") if sub_scores else None
    judge_content_grounding = sub_scores.get("content_grounding") if sub_scores else None

    hallucination_detected: Optional[bool] = None
    if json_data and "hallucination_detected" in json_data:
        raw_hall = json_data["hallucination_detected"]
        if isinstance(raw_hall, bool):
            hallucination_detected = raw_hall
        elif isinstance(raw_hall, str):
            hallucination_detected = raw_hall.lower() in ("true", "yes", "1")

    if score is None:
        logger.warning(
            "LLM Judge: could not parse SCORE from response. "
            "Raw response (last 800 chars): %.800s",
            raw_response[-800:],
        )
        logger.debug(
            "LLM Judge: full failed response written to debug log. Length=%d chars",
            len(raw_response),
        )
        return JudgeResult(
            score=None,
            reasoning=reasoning,
            raw_response=raw_response,
            parse_success=False,
            judge_task_compliance=judge_task_compliance,
            judge_output_quality=judge_output_quality,
            judge_standard_adherence=judge_standard_adherence,
            judge_content_grounding=judge_content_grounding,
            hallucination_detected=hallucination_detected,
        )

    return JudgeResult(
        score=score,
        reasoning=reasoning,
        raw_response=raw_response,
        parse_success=True,
        judge_task_compliance=judge_task_compliance,
        judge_output_quality=judge_output_quality,
        judge_standard_adherence=judge_standard_adherence,
        judge_content_grounding=judge_content_grounding,
        hallucination_detected=hallucination_detected,
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
    match = _RE_REASONING_START.search(text)
    if not match:
        return ""

    start_pos = match.end()

    # Try to end reasoning before JSON block if it exists
    json_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if not json_match:
        json_match = re.search(r"(\{.*\"score\".*\})", text, re.DOTALL)

    if json_match:
        end_pos = json_match.start()
        if end_pos > start_pos:
            reasoning_text = text[start_pos:end_pos].strip()
            reasoning_text = re.sub(r"-{3,}\s*$", "", reasoning_text).strip()
            return reasoning_text

    # Use the start position of the LAST valid SCORE marker (if any) as the end bound.
    # This prevents truncating the reasoning if the word "score" is used inside the reasoning itself.
    score_matches = list(_RE_SCORE.finditer(text))
    if score_matches:
        end_pos = score_matches[-1].start()
        # Ensure the score marker appears AFTER the reasoning marker
        if end_pos > start_pos:
            reasoning_text = text[start_pos:end_pos].strip()
            # Strip markdown horizontal rules often placed before the score
            reasoning_text = re.sub(r"-{3,}\s*$", "", reasoning_text).strip()
            return reasoning_text

    reasoning_text = text[start_pos:].strip()
    reasoning_text = re.sub(r"-{3,}\s*$", "", reasoning_text).strip()
    return reasoning_text


def _extract_json_block(text: str) -> Optional[dict]:
    """
    Extracts the JSON block from the new prompt format and parses it.
    Returns the parsed dict if successful, None otherwise.
    """
    matches = list(re.finditer(r"```json\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE))

    json_str = None
    if matches:
        json_str = matches[-1].group(1)
    else:
        # Fallback: some models forget the markdown block and just output raw JSON.
        # Find the last block that looks like a JSON object containing "score".
        fallback_match = re.search(r"(\{.*\"score\".*\})", text, re.DOTALL)
        if fallback_match:
            json_str = fallback_match.group(1)

    if not json_str:
        return None

    try:
        data = json.loads(json_str)
        if not isinstance(data, dict):
            return None
        return data
    except json.JSONDecodeError:
        return None


def _extract_sub_scores_legacy(text: str) -> Optional[dict]:
    """
    Extracts the JSON sub-score block from the legacy judge's output.
    Looks for the last ```json ... ``` block in the text or a raw JSON fallback.
    Returns None if no valid block is found.
    Validates that all three mandatory keys are present.
    """
    matches = list(re.finditer(r"```json\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE))

    json_str = None
    if matches:
        json_str = matches[-1].group(1)
    else:
        fallback_match = re.search(r"(\{.*\"task_compliance\".*\})", text, re.DOTALL)
        if fallback_match:
            json_str = fallback_match.group(1)

    if not json_str:
        return None

    try:
        data = json.loads(json_str)
        if not isinstance(data, dict):
            return None

        required_keys = ["task_compliance", "output_quality", "standard_adherence"]
        if not all(key in data for key in required_keys):
            return None

        for key in required_keys:
            val = data[key]
            if not isinstance(val, (int, float)) or val < 0 or val > 5:
                return None

        result = {key: float(data[key]) for key in required_keys}
        # Optional content_grounding (tooluse-specific)
        if "content_grounding" in data:
            val = data["content_grounding"]
            if isinstance(val, (int, float)) and 0 <= val <= 5:
                result["content_grounding"] = float(val)
        return result
    except json.JSONDecodeError:
        return None
