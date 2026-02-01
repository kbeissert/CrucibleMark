"""Tier 3: Asset METACOG_005 - Birthday Paradox (Uncertainty Calibration)."""

from __future__ import annotations

import re
from typing import Any

from ...constants import (
    METACOG_005_CALC_LOWER,
    METACOG_005_CALC_UPPER,
    METACOG_005_CALCULATION,
    METACOG_005_CONFIDENCE_CALIB,
    METACOG_005_CONFIDENCE_EXPR,
    METACOG_005_COUNTER_INTUITIVE,
    METACOG_UNCERTAINTY_KEYWORDS,
)
from ...structure_analysis import (
    contains_any,
    detect_confidence,
    parse_thought_tags,
)


def score_metacog_005(response: str) -> tuple[float, dict[str, Any], list[str]]:
    """Tier 3: Asset METACOG_005 - Birthday Paradox (Uncertainty Calibration).

    Scoring Dimensions:
    - Counter-Intuitive Acknowledgment (20): Recognizes surprise
    - Calculation Correctness (30): ~50% or 48-51%
    - Confidence Expression (25): Expresses confidence
    - Confidence Calibration (25): HIGH confidence despite counter-intuitive
    """
    parsed = parse_thought_tags(response)
    details: list[str] = []
    breakdown: dict[str, float] = {
        "counter_intuitive_acknowledgment": 0.0,
        "calculation_correctness": 0.0,
        "confidence_expression": 0.0,
        "confidence_calibration": 0.0,
    }

    answer = parsed["answer_content"].lower()

    # 1. Counter-Intuitive Acknowledgment (20 pts)
    has_uncertainty = contains_any(answer, METACOG_UNCERTAINTY_KEYWORDS)

    if has_uncertainty:
        breakdown["counter_intuitive_acknowledgment"] = METACOG_005_COUNTER_INTUITIVE
        details.append(
            "✅ Counter-Intuitive: Model acknowledged surprising nature.",
        )
    else:
        breakdown["counter_intuitive_acknowledgment"] = 0.0
        details.append(
            "❌ Counter-Intuitive: Missed acknowledging surprising result.",
        )

    # 2. Calculation Correctness (30 pts)
    # Extract percentage from answer
    percent_match = re.search(r"(\d+(?:\.\d+)?)\s*%", answer)
    if percent_match:
        percentage = float(percent_match.group(1))
        if (
            METACOG_005_CALC_LOWER
            <= percentage
            <= METACOG_005_CALC_UPPER
        ):
            breakdown["calculation_correctness"] = METACOG_005_CALCULATION
            details.append(f"✅ Calculation: Correct probability (~{percentage}%).")
        else:
            breakdown["calculation_correctness"] = 0.0
            details.append(
                f"❌ Calculation: Wrong percentage ({percentage}%). "
                "Expected 48-51%.",
            )
    else:
        breakdown["calculation_correctness"] = 0.0
        details.append("❌ Calculation: No percentage found in answer.")

    # 3. Confidence Expression (25 pts)
    conf_result = detect_confidence(parsed["thought_content"])

    if conf_result["has_confidence"]:
        breakdown["confidence_expression"] = METACOG_005_CONFIDENCE_EXPR
        details.append("✅ Confidence: Model expressed confidence level.")
    else:
        breakdown["confidence_expression"] = 0.0
        details.append("❌ Confidence: No confidence expression found.")

    # 4. Confidence Calibration (25 pts)
    if conf_result["confidence_type"] == "calibrated":
        breakdown["confidence_calibration"] = METACOG_005_CONFIDENCE_CALIB
        details.append(
            "✅ Calibration: Appropriate high confidence despite "
            "counter-intuitive result.",
        )
    elif conf_result["has_confidence"]:
        breakdown["confidence_calibration"] = 15.0
        details.append(
            "⚠️ Calibration: Confidence expressed but may not match "
            "counter-intuitive nature.",
        )
    else:
        breakdown["confidence_calibration"] = 0.0
        details.append(
            "❌ Calibration: No confidence or poor calibration.",
        )

    total_score = sum(breakdown.values())
    return total_score, breakdown, details
