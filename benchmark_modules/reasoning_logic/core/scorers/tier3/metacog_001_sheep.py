"""Tier 3: Asset METACOG_001 - The Sheep Trap (Self-Correction)."""

from __future__ import annotations

import re
from typing import Any

from ...constants import (
    METACOG_001_CORRECTNESS,
)
from ...robust_metrics import (
    detect_self_correction_robust,
    score_linguistic_analysis_objective,
)
from ...structure_analysis import parse_thought_tags


def score_metacog_001(response: str) -> tuple[float, dict[str, Any], list[str]]:
    """Tier 3: Asset METACOG_001 - The Sheep Trap (Self-Correction).

    Scoring Dimensions:
    - Self-Correction (40): Catches and corrects initial wrong instinct
    - Linguistic Analysis (30): Quality of thought process (explicitly
      analyzing "all but 9")
    - Output Correctness (30): Final answer must be 9
    """
    parsed = parse_thought_tags(response)
    details: list[str] = []
    breakdown: dict[str, float] = {
        "self_correction": 0.0,
        "linguistic_analysis": 0.0,
        "output_correctness": 0.0,
    }

    # 1. Self-Correction Check (40 pts) - HYBRID MULTI-LAYER DETECTION
    correction_result = detect_self_correction_robust(
        thought=parsed["thought_content"],
        answer=parsed["answer_content"],
        expected_answer="9",
    )
    breakdown["self_correction"] = correction_result["score"]
    details.extend(correction_result["evidence"])

    # 2. Linguistic Analysis (30 pts) - OBJECTIVE CRITERIA
    linguistic_result = score_linguistic_analysis_objective(
        thought=parsed["thought_content"],
        answer=parsed["answer_content"],
        phrase="all but 9",
    )
    breakdown["linguistic_analysis"] = linguistic_result["score"]
    details.extend(linguistic_result["evidence"])

    # 3. Output Correctness (30 pts) - FIX: Check last numeric token
    answer_lower = parsed["answer_content"].lower().strip()
    # Extract the last number mentioned as the final answer
    numbers = re.findall(r"\d+", answer_lower)
    final_number = numbers[-1] if numbers else None

    if final_number == "9":
        breakdown["output_correctness"] = METACOG_001_CORRECTNESS
        details.append("✅ Output: Correct answer (9).")
    else:
        breakdown["output_correctness"] = 0.0
        found_val = final_number if final_number else "none"
        details.append(
            f"❌ Output: Wrong answer. Expected 9, got {found_val}.",
        )

    total_score = sum(breakdown.values())

    return total_score, breakdown, details
