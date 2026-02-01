"""Tier 3: Asset METACOG_003 - The Two Doors (Alternative Exploration)."""

from __future__ import annotations

from typing import Any

from ...constants import (
    METACOG_003_ALTERNATIVES,
    METACOG_003_CORRECTNESS,
    METACOG_003_DEPTH,
    METACOG_003_THRESHOLD_ALTS,
    METACOG_003_THRESHOLD_HIGH,
    METACOG_003_THRESHOLD_MED,
)
from ...structure_analysis import (
    contains_any,
    detect_alternatives,
    parse_thought_tags,
)


def score_metacog_003(response: str) -> tuple[float, dict[str, Any], list[str]]:
    """Tier 3: Asset METACOG_003 - The Two Doors (Alternative Exploration).

    Scoring Dimensions:
    - Alternative Exploration (40): Explores 2+ approaches
    - Logical Correctness (30): Sound logic
    - Thought Depth (30): Depth of analysis
    """
    parsed = parse_thought_tags(response)
    details: list[str] = []
    breakdown: dict[str, float] = {
        "alternative_exploration": 0.0,
        "logical_correctness": 0.0,
        "thought_depth": 0.0,
    }

    answer = parsed["answer_content"].lower()

    # 1. Alternative Exploration (40 pts)
    alt_count = detect_alternatives(parsed["thought_content"])

    if alt_count >= METACOG_003_THRESHOLD_ALTS:
        breakdown["alternative_exploration"] = METACOG_003_ALTERNATIVES
        details.append(
            f"✅ Alternatives: Explored {alt_count} distinct approaches.",
        )
    elif alt_count == 1:
        breakdown["alternative_exploration"] = 20.0
        details.append("⚠️ Partial: Mentioned alternatives but limited depth.")
    else:
        breakdown["alternative_exploration"] = 0.0
        details.append("❌ Alternatives: Only single approach, no alternatives.")

    # 2. Logical Correctness (30 pts)
    has_logic_keywords = contains_any(
        answer, ["logic", "logically", "reason", "because"]
    )
    if has_logic_keywords:
        breakdown["logical_correctness"] = METACOG_003_CORRECTNESS
        details.append("✅ Logic: Sound reasoning demonstrated.")
    else:
        breakdown["logical_correctness"] = 15.0
        details.append("⚠️ Logic: Limited explicit logical reasoning.")

    # 3. Thought Depth (30 pts)
    if parsed["thought_length"] > METACOG_003_THRESHOLD_HIGH:
        breakdown["thought_depth"] = METACOG_003_DEPTH
        details.append(
            f"✅ Depth: Thorough analysis ({parsed['thought_length']} words).",
        )
    elif parsed["thought_length"] > METACOG_003_THRESHOLD_MED:
        breakdown["thought_depth"] = 15.0
        details.append(
            f"⚠️ Depth: Moderate analysis ({parsed['thought_length']} words).",
        )
    else:
        breakdown["thought_depth"] = 0.0
        details.append("❌ Depth: Insufficient analysis.")

    total_score = sum(breakdown.values())
    return total_score, breakdown, details
