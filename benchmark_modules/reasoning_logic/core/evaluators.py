"""Evaluators for Reasoning Logic.

Contains the core scoring logic related to dispatching and result aggregation.
"""

# pylint: disable=too-many-lines

from __future__ import annotations

import re  # Added for regex matching
from typing import Any, cast
import warnings

from .constants import (
    DIMENSION_SCORE_THRESHOLDS,
    FEASIBILITY_DEFAULT_OPTIMISTIC,
    MAX_SCORE,
    OUTPUT_QUALITY_WEIGHT,
    RCI_THRESHOLD_BASIC_THINKING,
    RCI_THRESHOLD_NON_THINKING,
    RCI_THRESHOLD_THINKING,
    RUBRICS,
    THOUGHT_QUALITY_WEIGHT,
    TIER_MAPPING,
)
from .scorers.standard import score_similarity_fallback, score_standard_asset
from .scorers.tier1_physics import score_5c_paradox
from .scorers.tier2_expert import score_5e_nested_paradox
from .scorers.tier2_systems import score_5b_complex, score_5d_deadlock
from .scorers.tier3 import (
    score_metacog_001,
    score_metacog_002,
    score_metacog_003,
    score_metacog_004,
    score_metacog_005,
)
from .structure_analysis import parse_thought_tags


def emit_legacy_warning(asset_id: str, deprecation_version: str = "v3.0") -> None:
    """
    Emit deprecation warning for tests still using legacy scoring.

    Args:
        asset_id: The test asset identifier
        deprecation_version: Version when legacy will be removed
    """
    warnings.warn(
        f"Asset '{asset_id}' uses legacy scoring system. "
        f"This will be removed in {deprecation_version}. "
        f"Please migrate to v2.0 rubric-based scoring.",
        DeprecationWarning,
        stacklevel=3,
    )


# ============================================================================
# NEW GRANULAR SCORING RUBRICS (v2.0)
# RUBRICS and DIMENSION_SCORE_THRESHOLDS live in constants/rubrics.py (SSoT)
# ============================================================================


def calculate_dimension_score(
    response: str, keywords: list[str], max_weight: int
) -> float:
    """Proportional keyword matching with partial credit using Regex."""
    if not keywords:
        return 0.0

    matches = sum(
        1 for pattern in keywords if re.search(pattern, response, re.IGNORECASE)
    )
    match_ratio = matches / len(keywords)

    for threshold, multiplier in DIMENSION_SCORE_THRESHOLDS:
        if match_ratio >= threshold:
            return float(max_weight * multiplier)

    return 0.0


def score_granular_rubric(
    response: str, asset_id: str
) -> tuple[float, dict[str, float], list[str]]:
    """Generic granular scorer using RUBRICS."""
    rubric = RUBRICS.get(asset_id)
    if not rubric:
        return 0.0, {}, ["Error: Missing Rubric"]

    scores = {}
    details = ["ℹ️ Algorithm: v2.1 Stricter Matching"]

    for dimension, config in rubric.items():
        weight = cast(int, config.get("weight", 0))
        keywords = cast(list[str], config.get("keywords", []))

        score = calculate_dimension_score(response, keywords, weight)
        scores[dimension] = score
        if score > 0:
            details.append(f"✅ {dimension}: {score:.1f}/{weight}")
        else:
            details.append(f"❌ {dimension}: 0/{weight}")

    total = sum(scores.values())
    return total, scores, details


class ReasoningEvaluator:
    """Evaluator class for Reasoning benchmarks.

    Acts as a Facade/Dispatcher to specific scoring logic (Strategy Pattern).
    """

    def __init__(self, asset: dict[str, Any]) -> None:
        """Initialize the evaluator with asset configuration."""
        self.asset = asset

        # Dispatcher Mapping
        self._scorers = {
            "reasoning_5e_001": score_5e_nested_paradox,
            "reasoning_metacog_001": score_metacog_001,
            "reasoning_metacog_002": score_metacog_002,
            "reasoning_metacog_003": score_metacog_003,
            "reasoning_metacog_004": score_metacog_004,
            "reasoning_metacog_005": score_metacog_005,
        }

        # Check scoring version for granular scoring (v2.0)
        # Defaults to 1.0 (Legacy) if not specified
        try:
            # Check root, but also metadata (YAML structure places it in metadata)
            val = self.asset.get("scoring_version")
            if val is None:
                val = self.asset.get("metadata", {}).get("scoring_version", 1.0)
            version = float(val)
        except (ValueError, TypeError):
            version = 1.0

        if version >= 2.0 or self.asset["metadata"]["id"] in RUBRICS:
            # v2.0: build rubric-wrapper scorers from the RUBRICS registry
            def _make_rubric_wrapper(rubric_id: str) -> Any:
                def wrapper(text: str, *_args: Any) -> tuple[float, dict[str, float], list[str]]:
                    return score_granular_rubric(text, rubric_id)
                return wrapper

            rubric_ids = [
                "reasoning_5a_001", "reasoning_5c_001", "reasoning_5b_001",
                "reasoning_5d_001", "reasoning_5e_001", "reasoning_metacog_004",
            ]
            for rid in rubric_ids:
                if rid in RUBRICS:
                    self._scorers[rid] = _make_rubric_wrapper(rid)
        else:
            # Uses Legacy Scorers
            emit_legacy_warning(self.asset["metadata"]["id"])
            self._scorers["reasoning_5c_001"] = score_5c_paradox
            self._scorers["reasoning_5b_001"] = score_5b_complex
            self._scorers["reasoning_5d_001"] = score_5d_deadlock
            # 5e remains default (handled in init dict or fallback)

    def score_response(self, response: str) -> dict[str, Any]:
        """Customize scoring for reasoning.

        Refactored to reduce complexity (Facade Pattern).
        """
        asset_id = self.asset["metadata"]["id"]
        expected_output = self.asset.get("expected_output", {})

        # Strategy Pattern for Scoring
        if handler := self._scorers.get(asset_id):
            # FIX: Metacognition assets require RAW response (with tags).
            # Other assets (5b, 5c, etc.) require CLEAN options (without tags).
            if "metacog" in asset_id:
                input_text = response
            else:
                input_text = self._strip_thinking_tags(response)

            # --- Feasibility Extraction for Hardened Scorers ---
            # Assets 5d and 5e now require feasibility parameter
            if asset_id in ["reasoning_5d_001", "reasoning_5e_001"]:
                feasibility = self._extract_feasibility(input_text)
                total_score, score_breakdown, details = cast(Any, handler)(
                    input_text,
                    feasibility,
                )
            else:
                # Standard signature (float, dict, list)
                total_score, score_breakdown, details = cast(Any, handler)(input_text)

        elif (
            isinstance(expected_output, dict) and "required_findings" in expected_output
        ):
            clean_response = self._strip_thinking_tags(response)
            findings = cast("list[str]", expected_output["required_findings"])
            total_score, score_breakdown, details = score_standard_asset(
                clean_response,
                findings,
                self.asset,
            )
        else:
            clean_response = self._strip_thinking_tags(response)
            total_score, score_breakdown, details = score_similarity_fallback(
                clean_response,
                self.asset,
            )

        # Normierung auf MAX_SCORE
        total_score = min(total_score, MAX_SCORE)

        # --- Tier Classification & Metadata Tagging ---
        tier_type = self._determine_tier(asset_id)

        # Assemble Result
        def get_score_val(value: Any) -> float:  # noqa: ANN401
            if isinstance(value, dict):
                return float(value.get("score", 0))
            return float(value)

        return {
            "status": "success",
            "total_score": float(total_score),
            "max_score": MAX_SCORE,
            "tier": tier_type,
            "category_scores": {
                k: {"achieved": get_score_val(v), "max": MAX_SCORE, "name": k}
                for k, v in score_breakdown.items()
            },
            "details": details,
            "violations": [],
        }

    def _determine_tier(self, asset_id: str) -> str:
        """Determine the reasoning tier based on asset ID from configuration.

        Args:
            asset_id (str): The unique identifier of the asset.

        Returns:
            str: The Tier name (e.g. "Tier 2 (Expert Systems)").
        """
        for tier_name, assets in TIER_MAPPING.items():
            if asset_id in assets:
                return tier_name
        return "Tier 1 (Operational Logic)"

    def _strip_thinking_tags(self, text: str) -> str:
        """Remove <think>...</think> blocks from DeepSeek R1 responses.

        These blocks contain internal reasoning that should not be scored
        for non-metacognitive tasks (like Tier 1/2 standard assets).

        Args:
            text (str): The raw response text containing potential tags.

        Returns:
            str: Cleaned text with thought blocks removed and whitespace trimmed.
        """
        # We can reuse the logic from parse_thought_tags or keep it simple here.
        # Since we just want to remove them, we can use the parser to get answer_content
        # or stick to the regex. To keep it simple and decoupled from parser logic which
        # aims to extract thoughts:
        parsed = parse_thought_tags(text)

        # Only strip explicit XML structural tags (<think>, <thought>, etc.)
        # for standard logic testing. Implicit separators (like "**Answer:**")
        # usually mean the model provided its reasoning in the main body,
        # which we MUST evaluate for points.
        if (
            parsed["has_thought_tags"]
            and parsed.get("thought_tag_type") != "implicit_separator"
        ):
            return parsed["answer_content"]

        # Fallback if parser didn't split it or if it's an implicit separator that is part of the final answer text
        return text.strip()

    def parse_thought_tags(self, response: str) -> dict[str, Any]:
        """Expose parser for testing/external use."""
        return parse_thought_tags(response)

    def _extract_feasibility(self, response: str) -> int:
        """Extract feasibility rating from model response.

        Parses text for explicit ratings like "Feasibility: 7/10",
        markdown formats, or loose contextual keywords.
        Uses optimized regex pattern matching (Single Pass with Groups).

        Args:
            response (str): The raw text response from the model.

        Returns:
            int: Extracted feasibility score (0-10). Returns DEFAULT if not found.
        """
        # Optimization: Combined regex pattern (Task-10)
        # Groups correspond to the original priority list logic
        pattern = (
            r"(\d+)\s*/\s*10|"  # 1. 0/10
            r"(\d+)\s*out of 10|"  # 2. 0 out of 10
            r"Feasibility:\s*(\d+)\s*/\s*10|"  # 3. Feasibility: 0/10
            r"(?:^|\n)\*\*Feasibility:\s*(\d+)\*\*|"  # 4. **Feasibility: 0**
            r"Feasibility:\s*(\d+)(?!\d)|"  # 5. Feasibility: 0
            r"feasibility.*?:\s*(\d+)(?!\d)|"  # 6. feasibility...: 0
            r"feasibility assessment[:\s]+(\d+)|"  # 7. feasibility assessment: 0
            r"feasibility[:\s]+(\d+)|"  # 8. feasibility: 0
            r"feasibility.*?(\d+)\s*/\s*10|"  # 9. feasibility... 0/10
            r"rate.*?(\d+)\s*/\s*10|"  # 10. rate... 0/10
            r"assess.*?(\d+)\s*/\s*10|"  # 11. assess... 0/10
            r"impossib.*feasibility[:\s]*(\d+)"  # 12. impossible... feasibility: 0
        )

        match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
        if match:
            # Find the captured group (only one will be non-None)
            for group_val in match.groups():
                if group_val is not None:
                    try:
                        rating = int(group_val)
                        return max(0, min(10, rating))
                    except ValueError:
                        continue

        # ⚠️ BETTER DEFAULT: 7 instead of 5
        # Rationale: If no explicit rating given, assume "optimistic but cautious"
        return FEASIBILITY_DEFAULT_OPTIMISTIC


# ============================================================================
# RCI CALCULATION & CLASSIFICATION (Module-Level Functions)
# ============================================================================


def calculate_rci(
    tier1_2_scores: list[float],
    tier3_scores: list[float],
) -> float:
    """Calculate Reasoning Complexity Index (RCI).

    Formula: RCI = (Avg_Output_Tier1+2 x 0.6) + (Avg_Thought_Tier3 x 0.4)

    Args:
        tier1_2_scores: List of output quality scores from Tier 1-2 assets
        tier3_scores: List of thought quality scores from Tier 3 assets

    Returns:
        RCI score (0-100)
    """
    avg_output = (sum(tier1_2_scores) / len(tier1_2_scores)) if tier1_2_scores else 0.0
    avg_thought = (sum(tier3_scores) / len(tier3_scores)) if tier3_scores else 0.0

    rci = (avg_output * OUTPUT_QUALITY_WEIGHT) + (avg_thought * THOUGHT_QUALITY_WEIGHT)
    return min(rci, MAX_SCORE)


def classify_model(rci: float) -> str:
    """Classify model based on RCI score.

    Classification:
    - Non-Thinking: RCI < 50%
    - Basic Thinking: RCI 50-70%
    - Thinking: RCI 70-85%
    - Deep Thinking: RCI > 85%

    Args:
        rci: Reasoning Complexity Index score (0-100)

    Returns:
        Classification string
    """
    if rci < RCI_THRESHOLD_NON_THINKING:
        return "Non-Thinking Model"
    if rci < RCI_THRESHOLD_BASIC_THINKING:
        return "Basic Thinking Model"
    if rci < RCI_THRESHOLD_THINKING:
        return "Thinking Model"
    return "Deep Thinking Model"
