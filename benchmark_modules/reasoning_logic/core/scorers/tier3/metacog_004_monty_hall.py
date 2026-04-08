"""Tier 3: Asset METACOG_004 - Monty Hall (Iterative Refinement)."""

from __future__ import annotations

import re
from typing import Any

from ...constants import (
    METACOG_004_CORRECTNESS,
    METACOG_004_ITERATION,
    METACOG_004_PROBABILITY,
)
from ...structure_analysis import detect_iteration, parse_thought_tags

# Explicit signals for a genuine second pass / reconsideration (EN + DE).
# detect_iteration() catches broad keywords like "but"/"aber"; this list
# requires a more deliberate rethinking signal to award full points.
_SECOND_THOUGHT_SIGNALS: list[str] = [
    # English
    "initially", "at first", "first i thought", "my first instinct",
    "on second thought", "let me reconsider", "thinking more carefully",
    "let me think again", "step back", "wait, ", "actually,",
    "reconsider", "reconsidering", "but actually", "but wait",
    # German
    "zunächst", "anfangs", "anfänglich", "zuerst dachte",
    "auf den ersten blick", "tatsächlich,", "korrigiere ich",
    "lass mich", "warte,", "überlege nochmal", "nochmal nachdenken",
    "bei näherer betrachtung", "eigentlich", "im zweiten schritt",
]

_CORRECT_PROBABILITY = 2 / 3  # ≈ 0.6667
_PROBABILITY_TOLERANCE = 0.05  # accepts 0.617 – 0.717


def _has_correct_probability(text: str) -> bool:
    """Return True if text contains a value semantically equivalent to 2/3.

    Recognises:
    - Fractions: "2/3"
    - Phrases: "two-thirds", "two thirds", "zwei drittel"
    - Integer percentages: 66 or 67 as standalone tokens
    - Decimal floats (. or , separator) within +-0.05 of 0.667
      e.g. 0.67, 0,67, 66.7, 66,7 -> normalised before comparison
    """
    t = text.lower()

    if "2/3" in t or "zwei drittel" in t or "two-thirds" in t or "two thirds" in t:
        return True

    # Standalone 66 or 67 (percentage context)
    if re.search(r"\b6[67]\b", t):
        return True

    # Decimal numbers with . or , as separator (handles 0.67, 0,67, 66.7, 66,7)
    for m in re.finditer(r"\b(\d+)[.,](\d+)\b", t):
        try:
            val = float(f"{m.group(1)}.{m.group(2)}")
            if val > 1.0:
                val = val / 100.0
            if abs(val - _CORRECT_PROBABILITY) <= _PROBABILITY_TOLERANCE:
                return True
        except ValueError:
            pass

    return False


def _has_switch_intent(text: str) -> bool:
    """Return True if text expresses intent to switch/change doors (EN + DE)."""
    return bool(
        re.search(
            r"\b(switch|change\s+door|wechsel[nt]?|wechsle|tauschen|tausche"
            r"|tür\s*2|tür\s*zwei|door\s*2)\b",
            text.lower(),
        )
    )


def score_metacog_004(response: str) -> tuple[float, dict[str, Any], list[str]]:
    """Tier 3: Asset METACOG_004 - Monty Hall (Iterative Refinement).

    Scoring Dimensions:
    - Iterative Refinement (35): Shows initial → reconsider → final (EN + DE)
    - Probability Analysis (35): Correct probability (~2/3), language-agnostic
    - Output Correctness (30): Switches + mentions correct probability
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
    # Full score: broad iteration signal (detect_iteration) AND an explicit
    # second-thought marker — avoids rewarding trivial "but"/"aber" matches.
    has_iteration = detect_iteration(parsed["thought_content"])
    has_second_thought = any(sig in thought for sig in _SECOND_THOUGHT_SIGNALS)

    if has_iteration and has_second_thought:
        breakdown["iterative_refinement"] = METACOG_004_ITERATION
        details.append("✅ Iteration: Shows initial → reconsider → final structure.")
    elif has_iteration or has_second_thought:
        breakdown["iterative_refinement"] = 20.0
        details.append("⚠️ Partial: Some iterative elements but not complete flow.")
    else:
        breakdown["iterative_refinement"] = 0.0
        details.append("❌ Iteration: No iterative reasoning shown.")

    # 2. Probability Analysis (35 pts)
    # Check both thought block AND answer — many models reason in <thought>
    # and only summarise in the answer without repeating the exact fraction.
    has_prob = _has_correct_probability(thought) or _has_correct_probability(answer)
    mentions_prob_concept = any(
        kw in thought + " " + answer
        for kw in ("probability", "wahrscheinlichkeit", "chance", "odds")
    )

    if has_prob:
        breakdown["probability_analysis"] = METACOG_004_PROBABILITY
        details.append("✅ Probability: Correct probability analysis (~2/3).")
    elif _has_switch_intent(answer) and mentions_prob_concept:
        breakdown["probability_analysis"] = 20.0
        details.append("⚠️ Partial: Correct conclusion but weak probability explanation.")
    else:
        breakdown["probability_analysis"] = 0.0
        details.append("❌ Probability: Missing or incorrect analysis.")

    # 3. Output Correctness (30 pts)
    has_switch = _has_switch_intent(answer)
    has_prob_in_answer = _has_correct_probability(answer)

    if has_switch and has_prob_in_answer:
        breakdown["output_correctness"] = METACOG_004_CORRECTNESS
        details.append("✅ Output: Correct answer (switch) with correct probability.")
    elif has_switch:
        breakdown["output_correctness"] = 15.0
        details.append("⚠️ Partial: Correct answer but incomplete probability explanation.")
    else:
        breakdown["output_correctness"] = 0.0
        details.append("❌ Output: Wrong answer. Expected switch to door 2.")

    total_score = sum(breakdown.values())
    return total_score, breakdown, details
