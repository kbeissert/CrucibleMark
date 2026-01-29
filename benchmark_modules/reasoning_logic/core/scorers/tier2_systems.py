"""Scores Tier 2 Systems Thinking Assets (e.g. 5B, 5D)."""

import re
from typing import Any

from ..constants import (
    ASSET_5B_CONCEPT_KEYWORDS,
    ASSET_5B_CORE_KEYWORDS,
    ASSET_5B_DOMAIN_KEYWORDS,
    ASSET_5B_PRIO_KEYWORDS,
    ASSET_5B_QUALIFIER_KEYWORDS,
    ASSET_5B_SOLUTION_KEYWORDS,
    ASSET_5D_CIRCULAR_KEYWORDS,
    ASSET_5D_DEADLOCK_KEYWORDS,
    ASSET_5D_WARNING_KEYWORDS,
    BONUS_CONSISTENCY,
    FEASIBILITY_HIGH_MAX,
    FEASIBILITY_HIGH_MIN,
    FEASIBILITY_IMPOSSIBLE,
    FEASIBILITY_LOW_MAX,
    MAX_SCORE,
    SCORE_THRESHOLD_HIGH,
    SCORE_THRESHOLD_MED,
    WEIGHT_CONSISTENCY,
    WEIGHT_ERROR_DETECTION,
    WEIGHT_SOLUTION_QUALITY,
)
from ..structure_analysis import contains_any


def score_5b_complex(response: str) -> tuple[float, dict[str, Any], list[str]]:
    """Tier 2: Asset 5B - Complex Reasoning Chains (System Thinking).

    Uses 3-Tier Scoring: Concepts (40) -> Solution (70) -> Prioritization (100).
    """
    resp_lower = response.lower()
    details = []
    # 1. Concept Detection (Tier 1 Check)
    c1_core = contains_any(resp_lower, ASSET_5B_CORE_KEYWORDS)
    c1_qualifier = contains_any(resp_lower, ASSET_5B_QUALIFIER_KEYWORDS)
    has_root_cause = c1_core and c1_qualifier

    c2_domain = contains_any(resp_lower, ASSET_5B_DOMAIN_KEYWORDS)
    c2_concept = contains_any(resp_lower, ASSET_5B_CONCEPT_KEYWORDS)
    has_cross_domain = c2_domain and c2_concept

    has_integrated_solution = contains_any(
        resp_lower, ASSET_5B_SOLUTION_KEYWORDS,
    )

    # 2. Prioritization Check (Tier 3 Check)
    # Look for numbered lists or explicit prioritization language
    # Regex looks for patterns like "1. ", "2. ", "Step 1:", "First:", etc.
    has_numbering = bool(
        re.search(
            r"(?:^|\n)\s*(?:\d+\.|step \d|phase \d)", response, re.IGNORECASE,
        ),
    )
    has_prio_kw = contains_any(resp_lower, ASSET_5B_PRIO_KEYWORDS)
    has_prioritization = has_numbering and has_prio_kw

    # --- SCORING LOGIC ---

    # Base Points: Error Detection (Max 40)
    error_pts = 0.0
    if has_root_cause:
        error_pts += 20.0
        details.append(
            "✅ Root Cause: Identified Versioning/Deprecation inconsistency.",
        )
    else:
        details.append(
            "❌ Root Cause: "
            "Missed the core versioning/deprecation strategy issue.",
        )

    if has_cross_domain:
        error_pts += 20.0
        details.append(
            "✅ Cross-Domain: "
            "Identified need for alignment between Code/Docs/UX.",
        )
    else:
        details.append(
            "❌ Cross-Domain: Missed the systemic link between domains.",
        )

    # Solution Quality (Max 50)
    # Tier 2: Integrated Solution (Base 30)
    # Tier 3: Prioritization (+20)
    solution_pts = 0.0

    if has_integrated_solution:
        solution_pts += SCORE_THRESHOLD_MED
        details.append(
            "✅ Solution: Proposed a unified policy/governance approach.",
        )

        # Check for Tier 3 (Prioritization) ONLY if solution is valid
        if has_prioritization:
            solution_pts += 20.0
            details.append(
                "✅ Prioritization: "
                "Structured plan with clear steps/priorities.",
            )
        else:
            details.append(
                "⚠️ Prioritization: Solution is good, "
                "but lacks clear prioritization steps (Tier 3 missed).",
            )
    # Partial credit for "fixing" things without policy
    elif "fix" in resp_lower or "korrigieren" in resp_lower:
        solution_pts = 10.0
        details.append(
            "⚠️ Solution: "
            "Proposed fixes but missed the 'Unified Policy' aspect.",
        )
    else:
        details.append("❌ Solution: No clear integrated solution found.")

    # Consistency (Max 10)
    # Bonus for full Tier 2 achievement
    consistency_pts = (
        BONUS_CONSISTENCY
        if (
            error_pts >= SCORE_THRESHOLD_HIGH
            and solution_pts >= SCORE_THRESHOLD_MED
        )
        else 0.0
    )

    total_score = error_pts + solution_pts + consistency_pts

    score_breakdown = {
        "error_detection": error_pts,
        "solution_quality": solution_pts,
        "consistency": consistency_pts,
    }

    return total_score, score_breakdown, details


def score_5d_deadlock(response: str) -> tuple[float, dict[str, Any], list[str]]:
    """Tier 2: Asset 5D - Circular Dependency (Deadlock)."""
    resp_lower = response.lower()
    breakdown: dict[str, float] = {
        "error_detection": 0.0,
        "solution_quality": 0.0,
        "consistency": 0.0,
    }

    # 1. Check for explicit Feasibility Score
    feasibility_match = re.search(r"feasibility:\s*(\d+)", resp_lower)
    feasibility_score = (
        int(feasibility_match.group(1)) if feasibility_match else None
    )

    # 2. Check for Keywords
    has_deadlock = contains_any(resp_lower, ASSET_5D_DEADLOCK_KEYWORDS)
    has_circular = contains_any(resp_lower, ASSET_5D_CIRCULAR_KEYWORDS)
    has_warning = contains_any(resp_lower, ASSET_5D_WARNING_KEYWORDS)

    # LEVEL 1: PERFECT (100)
    # Criteria: Feasibility 0 OR Strong Deadlock confirmation
    is_impossible_score = (
        feasibility_score is not None
        and feasibility_score == FEASIBILITY_IMPOSSIBLE
    )
    if is_impossible_score or has_deadlock:
        breakdown = {
            "error_detection": float(WEIGHT_ERROR_DETECTION),
            "solution_quality": float(WEIGHT_SOLUTION_QUALITY),
            "consistency": float(WEIGHT_CONSISTENCY),
        }
        return (
            float(MAX_SCORE),
            breakdown,
            ["✅ Logic Pass: Correctly identified as Impossible/Deadlock."],
        )

    # LEVEL 2: GOOD CATCH (70)
    # Criteria: Feasibility 1-3 OR Specific Circular Dependency identification
    is_low_feasibility = (
        feasibility_score is not None
        and 1 <= feasibility_score <= FEASIBILITY_LOW_MAX
    )
    if is_low_feasibility or has_circular:
        breakdown = {
            "error_detection": float(WEIGHT_ERROR_DETECTION),
            "solution_quality": float(WEIGHT_SOLUTION_QUALITY * 0.5),
            "consistency": float(WEIGHT_CONSISTENCY * 0.5),
        }
        return (
            SCORE_THRESHOLD_HIGH,
            breakdown,
            [
                "⚠️ Logic Partial (High): "
                "Identified circular dependency but was slightly optimistic.",
            ],
        )

    # LEVEL 3: WEAK WARNING (40)
    # Criteria: Feasibility 4-5 OR General warnings
    is_med_feasibility = (
        feasibility_score is not None
        and FEASIBILITY_HIGH_MIN <= feasibility_score <= FEASIBILITY_HIGH_MAX
    )
    if is_med_feasibility or has_warning:
        breakdown = {
            "error_detection": float(WEIGHT_ERROR_DETECTION * 0.5),
            "solution_quality": 0.0,
            "consistency": 0.0,
        }
        return (
            40.0,
            breakdown,
            [
                "⚠️ Logic Partial (Low): "
                "Recognized complexity/risk but missed the deadlock.",
            ],
        )

    # LEVEL 4: FAIL (0)
    return (
        0.0,
        breakdown,
        ["❌ Logic Fail: Optimism Bias. Failed to identify deadlock or risks."],
    )
