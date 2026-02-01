"""Tier 3: Asset METACOG_004 - Monty Hall (Iterative Refinement)."""

from __future__ import annotations

from typing import Any

from ...constants import (
    METACOG_004_CORRECTNESS,
    METACOG_004_ITERATION,
    METACOG_004_PROBABILITY,
)
from ...structure_analysis import detect_iteration, parse_thought_tags


def score_metacog_004(response: str) -> tuple[float, dict[str, Any], list[str]]:
    """Tier 3: Asset METACOG_004 - Monty Hall (Iterative Refinement).

    Scoring Dimensions:
    - Iterative Refinement (35): Shows initial → reconsider → final
    - Probability Analysis (35): Correct probability (2/3)
    - Output Correctness (30): Answer is "switch" and mentions 2/3
    """
    parsed = parse_thought_tags(response)
    details: list[str] = []
    breakdown: dict[str, float] = {
        "iterative_refinement": 0.0,
        "probability_analysis": 0.0,
        "output_correctness": 0.0,
    }

    thought = parsed["thought_content"].lower()
    answer = parsed["answer_content"].lower()

    # 1. Iterative Refinement (35 pts)
    has_iteration = detect_iteration(parsed["thought_content"])

    if has_iteration and ("initial" in thought or "first" in thought):
        breakdown["iterative_refinement"] = METACOG_004_ITERATION
        details.append(
            "✅ Iteration: Shows initial → reconsider → final structure.",
        )
    elif has_iteration:
        breakdown["iterative_refinement"] = 20.0
        details.append("⚠️ Partial: Some iterative elements but not complete flow.")
    else:
        breakdown["iterative_refinement"] = 0.0
        details.append("❌ Iteration: No iterative reasoning shown.")

    # 2. Probability Analysis (35 pts)
    if "2/3" in answer or "67" in answer or "two-thirds" in answer:
        breakdown["probability_analysis"] = METACOG_004_PROBABILITY
        details.append("✅ Probability: Correct probability analysis (2/3).")
    elif "switch" in answer and "probability" in answer:
        breakdown["probability_analysis"] = 20.0
        details.append(
            "⚠️ Partial: Correct conclusion but weak probability explanation.",
        )
    else:
        breakdown["probability_analysis"] = 0.0
        details.append("❌ Probability: Missing or incorrect analysis.")

    # 3. Output Correctness (30 pts)
    if "switch" in answer and ("2/3" in answer or "67" in answer):
        breakdown["output_correctness"] = METACOG_004_CORRECTNESS
        details.append(
            "✅ Output: Correct answer (switch) with correct probability.",
        )
    elif "switch" in answer:
        breakdown["output_correctness"] = 15.0
        details.append(
            "⚠️ Partial: Correct answer but incomplete probability explanation.",
        )
    else:
        breakdown["output_correctness"] = 0.0
        details.append("❌ Output: Wrong answer. Expected switch to door 2.")

    total_score = sum(breakdown.values())
    return total_score, breakdown, details
