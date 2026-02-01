"""Tier 3: Asset METACOG_002 - The Green Sky (False Premise Challenge)."""

from __future__ import annotations

from typing import Any

from ...constants import (
    METACOG_002_CORRECTION,
    METACOG_002_PREMISE,
    METACOG_002_THOUGHT,
)
from ...structure_analysis import contains_any, parse_thought_tags


def _detect_premise_challenge(combined: str) -> bool:
    """Check if the model explicitly challenges the false premise.

    Looks for strong phrases like "false premise" or logical combinations
    of premise concepts and negation indicators.

    Args:
        combined (str): Combined text of thought and answer to search within.

    Returns:
        bool: True if a premise challenge is detected.
    """
    strong_phrases = [
        "the question asks about a green sky",
        "the premise is that the sky is green",
        "the question assumes a green sky",
        "the question assumes the sky is green",
        "question is based on a false premise",
        "based on a false assumption",
        "the premise is false",
        "this premise is wrong",
        "false premise",
        "incorrect premise",
        "wrong assumption",
        "the assumption is false",
        "the setup is wrong",
        "question assumes",
        "assumption that",
        "sky is not green",
        "there is no such thing",
    ]

    has_strong_phrase = any(p in combined for p in strong_phrases)

    has_concept_premise = contains_any(
        combined, ["premise", "assumption", "hypothesis"]
    )
    has_concept_negation = contains_any(
        combined, ["false", "incorrect", "wrong", "not true", "flawed"]
    )
    has_split_logic = has_concept_premise and has_concept_negation

    return has_strong_phrase or has_split_logic


def _check_physics_presence(combined: str) -> bool:
    """Check for physics-related terms in the response.

    Looks for terms like "Rayleigh scattering", "wavelength", or "blue light"
    explanations.

    Args:
        combined (str): Combined text of thought and answer to search within.

    Returns:
        bool: True if physics concepts are present.
    """
    has_rayleigh = "rayleigh" in combined
    has_wavelength = "wavelength" in combined
    has_shorter = contains_any(combined, ["shorter", "short", "blue light"])
    return has_rayleigh or (has_wavelength and has_shorter)


def _evaluate_factual_correction(
    answer: str, combined: str, has_physics_explanation: bool
) -> tuple[float, str]:
    """Evaluate if the model corrects the false premise with facts.

    Scoring Tiers:
    - High: States sky is blue AND provides physics explanation.
    - Medium: States sky is blue with generic "scatter" mention.
    - Low: States sky is blue without explanation.
    - Zero: Fails to correct the fact.

    Args:
        answer (str): The final answer text.
        combined (str): Combined thought and answer text.
        has_physics_explanation (bool): Result from `_check_physics_presence`.

    Returns:
        tuple[float, str]: The score (0-40) and a descriptive log message.
    """
    has_blue = "blue" in answer
    has_scatter_generic = contains_any(combined, ["scatter", "scattering"])

    if has_blue and has_physics_explanation:
        return (
            METACOG_002_CORRECTION,
            "✅ Factual Correction: Sky is blue with physics explanation.",
        )
    if has_blue and has_scatter_generic:
        return (
            20.0,
            "⚠️ Partial: States sky is blue with generic scatter mention.",
        )
    if has_blue:
        return 15.0, "⚠️ Minimal: States sky is blue but no explanation."

    return 0.0, "❌ Factual Correction: Missing or incorrect fact."


def _evaluate_thought_quality(
    parsed: dict[str, Any], has_physics_explanation: bool
) -> tuple[float, str]:
    """Evaluate the depth and quality of the reasoning process.

    Scoring Tiers:
    - High (25pts): Substantial thought length (>30 words) AND physics.
    - Medium (10pts): Substantial thought but shallow/missing physics.
    - Zero: Insufficient thought length or quality.

    Args:
        parsed (dict[str, Any]): The parsed response dictionary.
        has_physics_explanation (bool): Whether physics concepts were found.

    Returns:
        tuple[float, str]: The score (0-25) and a descriptive log message.
    """
    has_substantial_thought = (
        parsed["has_thought_tags"] and parsed["thought_length"] > 30
    )

    if has_substantial_thought and has_physics_explanation:
        return (
            METACOG_002_THOUGHT,
            f"✅ Thought Quality: Substantial reasoning with physics "
            f"({parsed['thought_length']} words).",
        )
    if has_substantial_thought:
        return (
            10.0,
            f"⚠️ Thought Quality: Some reasoning but shallow physics "
            f"({parsed['thought_length']} words).",
        )
    return 0.0, "❌ Thought Quality: Insufficient reasoning shown."


def score_metacog_002(response: str) -> tuple[float, dict[str, Any], list[str]]:
    """Tier 3: Asset METACOG_002 - The Green Sky (False Premise Challenge).

    Scoring Dimensions:
    - Premise Challenge (50): Rejects false premise with keywords like
      "not green", "sky is blue", "false premise"
    - Factual Correction (30): Provides correct fact (sky is blue) with
      explanation
    - Thought Quality (20): Quality of reasoning process
    """
    parsed = parse_thought_tags(response)
    details: list[str] = []
    breakdown: dict[str, float] = {
        "premise_challenge": 0.0,
        "factual_correction": 0.0,
        "thought_quality": 0.0,
    }

    answer = parsed["answer_content"].lower()
    thought = parsed["thought_content"].lower()
    combined = (answer + " " + thought).lower()

    # 1. Premise Challenge (50 pts)
    has_premise_challenge = _detect_premise_challenge(combined)

    if has_premise_challenge and "blue" in answer:
        breakdown["premise_challenge"] = METACOG_002_PREMISE
        details.append(
            "✅ Premise Challenge: Explicitly identified false premise "
            "about green sky."
        )
    else:
        breakdown["premise_challenge"] = 0.0
        details.append(
            "❌ Premise Challenge: Did not explicitly identify false premise.",
        )

    # 2. Factual Correction (30 pts)
    # Calculate physics explanation once to reuse in Step 2 and Step 3
    has_physics_explanation = _check_physics_presence(combined)

    fc_score, fc_detail = _evaluate_factual_correction(
        answer, combined, has_physics_explanation
    )
    breakdown["factual_correction"] = fc_score
    details.append(fc_detail)

    # 3. Thought Quality (20 pts) - REQUIRE SUBSTANTIVE REASONING
    tq_score, tq_detail = _evaluate_thought_quality(
        parsed, has_physics_explanation
    )
    breakdown["thought_quality"] = tq_score
    details.append(tq_detail)

    total_score = sum(breakdown.values())

    return total_score, breakdown, details
