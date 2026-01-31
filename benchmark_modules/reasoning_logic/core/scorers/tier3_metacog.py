"""Scores Tier 3 Metacognition Assets (e.g. Metacog 001-005)."""

import re
from typing import Any

from ..constants import (
    METACOG_UNCERTAINTY_KEYWORDS,
)
from ..robust_metrics import (
    detect_self_correction_robust,
    score_linguistic_analysis_objective,
)
from ..structure_analysis import (
    contains_any,
    detect_alternatives,
    detect_confidence,
    detect_iteration,
    parse_thought_tags,
)


# Define constants for Magic Numbers
SELF_CORRECTION_SCORE = 40.0
LINGUISTIC_ANALYSIS_SCORE = 30.0
OUTPUT_CORRECTNESS_SCORE = 30.0
PREMISE_CHALLENGE_SCORE = 50.0
FACTUAL_CORRECTION_SCORE = 30.0
THOUGHT_QUALITY_SCORE = 20.0
ALTERNATIVE_EXPLORATION_SCORE = 40.0
THOUGHT_QUALITY_THRESHOLD = 30
ALTERNATIVE_EXPLORATION_THRESHOLD = 2
THOUGHT_DEPTH_HIGH_THRESHOLD = 50
THOUGHT_DEPTH_MEDIUM_THRESHOLD = 25
CALCULATION_CORRECTNESS_LOWER = 48
CALCULATION_CORRECTNESS_UPPER = 51
LOGICAL_CORRECTNESS_SCORE = 30.0
THOUGHT_DEPTH_SCORE = 30.0

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
    breakdown["self_correction"] = SELF_CORRECTION_SCORE if correction_result["score"] else 0.0
    details.extend(correction_result["evidence"])

    # 2. Linguistic Analysis (30 pts) - OBJECTIVE CRITERIA
    linguistic_result = score_linguistic_analysis_objective(
        thought=parsed["thought_content"],
        answer=parsed["answer_content"],
        phrase="all but 9",
    )
    breakdown["linguistic_analysis"] = (
        LINGUISTIC_ANALYSIS_SCORE if linguistic_result["score"] else 0.0
    )
    details.extend(linguistic_result["evidence"])

    # 3. Output Correctness (30 pts) - FIX: Check last numeric token
    answer_lower = parsed["answer_content"].lower().strip()
    # Extract the last number mentioned as the final answer
    numbers = re.findall(r"\d+", answer_lower)
    final_number = numbers[-1] if numbers else None

    if final_number == "9":
        breakdown["output_correctness"] = OUTPUT_CORRECTNESS_SCORE
        details.append("✅ Output: Correct answer (9).")
    else:
        breakdown["output_correctness"] = 0.0
        found_val = final_number if final_number else "none"
        details.append(
            f"❌ Output: Wrong answer. Expected 9, got {found_val}.",
        )

    total_score = sum(breakdown.values())

    return total_score, breakdown, details


def _detect_premise_challenge(combined: str) -> bool:
    """Helper: Checks if the model challenges the false premise."""
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
    """Helper: Checks for physics keywords."""
    has_rayleigh = "rayleigh" in combined
    has_wavelength = "wavelength" in combined
    has_shorter = contains_any(
        combined, ["shorter", "short", "blue light"]
    )
    return has_rayleigh or (has_wavelength and has_shorter)


def _evaluate_factual_correction(
    answer: str, combined: str, has_physics_explanation: bool
) -> tuple[float, str]:
    """Helper: Evaluates physics explanation for blue sky."""
    has_blue = "blue" in answer
    has_scatter_generic = contains_any(
        combined, ["scatter", "scattering"]
    )

    if has_blue and has_physics_explanation:
        return (
            FACTUAL_CORRECTION_SCORE,
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
    """Helper: Evaluates reasoning depth."""
    has_substantial_thought = (
        parsed["has_thought_tags"] and parsed["thought_length"] > 30
    )

    if has_substantial_thought and has_physics_explanation:
        return (
            THOUGHT_QUALITY_SCORE,
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
        breakdown["premise_challenge"] = PREMISE_CHALLENGE_SCORE
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

    if alt_count >= ALTERNATIVE_EXPLORATION_THRESHOLD:
        breakdown["alternative_exploration"] = ALTERNATIVE_EXPLORATION_SCORE
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
        answer, ["logic", "logically", "reason", "because"],
    )
    if has_logic_keywords:
        breakdown["logical_correctness"] = LOGICAL_CORRECTNESS_SCORE
        details.append("✅ Logic: Sound reasoning demonstrated.")
    else:
        breakdown["logical_correctness"] = 15.0
        details.append("⚠️ Logic: Limited explicit logical reasoning.")

    # 3. Thought Depth (30 pts)
    if parsed["thought_length"] > THOUGHT_DEPTH_HIGH_THRESHOLD:
        breakdown["thought_depth"] = THOUGHT_DEPTH_SCORE
        details.append(
            f"✅ Depth: Thorough analysis ({parsed['thought_length']} words).",
        )
    elif parsed["thought_length"] > THOUGHT_DEPTH_MEDIUM_THRESHOLD:
        breakdown["thought_depth"] = 15.0
        details.append(
            f"⚠️ Depth: Moderate analysis ({parsed['thought_length']} words).",
        )
    else:
        breakdown["thought_depth"] = 0.0
        details.append("❌ Depth: Insufficient analysis.")

    total_score = sum(breakdown.values())
    return total_score, breakdown, details


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
        breakdown["iterative_refinement"] = 35.0
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
        breakdown["probability_analysis"] = 35.0
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
        breakdown["output_correctness"] = OUTPUT_CORRECTNESS_SCORE
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
        breakdown["counter_intuitive_acknowledgment"] = 20.0
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
        if CALCULATION_CORRECTNESS_LOWER <= percentage <= CALCULATION_CORRECTNESS_UPPER:
            breakdown["calculation_correctness"] = 30.0
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
        breakdown["confidence_expression"] = 25.0
        details.append("✅ Confidence: Model expressed confidence level.")
    else:
        breakdown["confidence_expression"] = 0.0
        details.append("❌ Confidence: No confidence expression found.")

    # 4. Confidence Calibration (25 pts)
    if conf_result["confidence_type"] == "calibrated":
        breakdown["confidence_calibration"] = 25.0
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
