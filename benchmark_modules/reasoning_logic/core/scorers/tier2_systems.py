"""Scores Tier 2 Systems Thinking Assets (e.g. 5B, 5D)."""

import re
from dataclasses import dataclass
from typing import Any

from ..constants import (
    ASSET_5B_CONCEPT_KEYWORDS,
    ASSET_5B_CORE_KEYWORDS,
    ASSET_5B_DOMAIN_KEYWORDS,
    ASSET_5B_PRIO_KEYWORDS,
    ASSET_5B_QUALIFIER_KEYWORDS,
    ASSET_5B_SOLUTION_KEYWORDS,
    BONUS_CONSISTENCY,
    SCORE_THRESHOLD_HIGH,
    SCORE_THRESHOLD_MED,
)
from ..structure_analysis import contains_any

PRIORITIZATION_BONUS = 20.0
MAX_ERROR_POINTS = 40.0


def _detect_5b_signals(response: str) -> dict[str, Any]:
    """Helper: Detects signals for Asset 5B scoring."""
    resp_lower = response.lower()
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
    has_numbering = bool(
        re.search(
            r"(?:^|\n)\s*(?:\d+\.|step \d|phase \d)", response, re.IGNORECASE,
        ),
    )
    has_prio_kw = contains_any(resp_lower, ASSET_5B_PRIO_KEYWORDS)
    has_prioritization = has_numbering and has_prio_kw

    return {
        "has_root_cause": has_root_cause,
        "has_cross_domain": has_cross_domain,
        "has_integrated_solution": has_integrated_solution,
        "has_prioritization": has_prioritization,
        "resp_lower": resp_lower,
    }


def score_5b_complex(response: str) -> tuple[float, dict[str, Any], list[str]]:
    """Tier 2: Asset 5B - Complex Reasoning Chains (System Thinking).

    Uses 3-Tier Scoring: Concepts (40) -> Solution (70) -> Prioritization (100).
    """
    signals = _detect_5b_signals(response)
    resp_lower = str(signals["resp_lower"])
    details = []

    # --- SCORING LOGIC ---

    # Base Points: Error Detection (Max 40)
    error_pts = MAX_ERROR_POINTS if signals["has_root_cause"] else 0.0
    details.append(
        "✅ Root Cause: Identified Versioning/Deprecation inconsistency.",
    )
    details.append(
        "❌ Root Cause: "
        "Missed the core versioning/deprecation strategy issue.",
    )

    if signals["has_cross_domain"]:
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

    if signals["has_integrated_solution"]:
        solution_pts += SCORE_THRESHOLD_MED
        details.append(
            "✅ Solution: Proposed a unified policy/governance approach.",
        )

        # Check for Tier 3 (Prioritization) ONLY if solution is valid
        if signals["has_prioritization"]:
            solution_pts += PRIORITIZATION_BONUS
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
    # Bonus for full Tier 2 achievemen
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



# Constants for Deadlock Seoring
FEASIBILITY_HARD_LIMIT = 2
FEASIBILITY_SOFT_LIMIT_LOW = 3
FEASIBILITY_SOFT_LIMIT_HIGH = 4
EXPLANATION_MIN_COUNT = 2


@dataclass
class DeadlockSignals:
    """Encapsulates all signals required for deadlock scoring."""

    feasibility: int
    has_tier1: bool
    has_tier2: bool
    has_tier3: bool
    has_explanation: bool
    has_contradiction: bool


def _check_perfect_deadlock(s: DeadlockSignals) -> tuple[int, str] | None:
    if (
        s.feasibility <= 1
        and (s.has_tier2 or s.has_tier3)
        and s.has_explanation
        and not s.has_contradiction
    ):
        return (
            100,
            "Perfect: Identified deadlock with clear explanation and correct "
            "feasibility",
        )
    return None


def _check_strong_partial(s: DeadlockSignals) -> tuple[int, str] | None:
    if s.feasibility <= 1:
        if (s.has_tier2 or s.has_tier3) and not s.has_explanation:
            return (
                70,
                "Partial: Detected deadlock terminology but missing causal explanation",
            )
        if s.has_explanation and not (s.has_tier2 or s.has_tier3):
            return (
                70,
                "Partial: Explained dependency issue but missed 'deadlock' concept",
            )
    return None


def _check_weak_awareness(s: DeadlockSignals) -> tuple[int, str] | None:
    if 1 <= s.feasibility <= FEASIBILITY_HARD_LIMIT and s.has_tier1:
        return 50, "Weak: Sensed conflict but unclear on deadlock mechanism"
    return None


def _check_minimal_warning(s: DeadlockSignals) -> tuple[int, str] | None:
    if FEASIBILITY_SOFT_LIMIT_LOW <= s.feasibility <= FEASIBILITY_SOFT_LIMIT_HIGH:
        return 30, "Minimal: Expressed doubt but no clear conflict identification"
    return None


def _check_failure(s: DeadlockSignals) -> tuple[int, str] | None:
    if s.feasibility > FEASIBILITY_SOFT_LIMIT_HIGH or s.has_contradiction:
        return (
            0,
            "Failure: Optimism bias or contradicted deadlock with feasibility claim",
        )
    return None


def _build_deadlock_signals(
    response: str, feasibility: int,
) -> DeadlockSignals:
    """Helper: Extracts signals for Deadlock scoring."""
    response_lower = response.lower()

    # --- SIGNAL B: Keyword Detection (Tiered) ---
    deadlock_keywords_tier1 = ["impossible", "conflict", "cannot", "won't work"]
    deadlock_keywords_tier2 = ["deadlock", "circular", "paradox", "cyclic"]
    deadlock_keywords_tier3 = [
        "a->b->c->a",
        "cycle",
        "mutual dependency",
        "circular dependency",
    ]

    has_tier1 = any(kw in response_lower for kw in deadlock_keywords_tier1)
    has_tier2 = any(kw in response_lower for kw in deadlock_keywords_tier2)
    has_tier3 = any(kw in response_lower for kw in deadlock_keywords_tier3)

    # --- SIGNAL C: Explanation Detection ---
    explanation_indicators = [
        "because",
        "since",
        "therefore",
        "thus",
        "reason",
        "step 1 waits",
        "step 2 waits",
        "blocks",
        "dependency",
        "requires",
        "depends on",
    ]
    explanation_count = sum(
        1 for ind in explanation_indicators if ind in response_lower
    )
    has_explanation = explanation_count >= EXPLANATION_MIN_COUNT

    # --- CONTRADICTION CHECK ---
    contradiction_keywords = [
        "is feasible",
        "totally feasible",
        "highly feasible",
        "is possible to implement",
        "it can work",
        "plan works",
        "timeline works",
        "just need to",
        "simply",
    ]
    has_contradiction = any(
        kw in response_lower for kw in contradiction_keywords
    )

    return DeadlockSignals(
        feasibility=feasibility,
        has_tier1=has_tier1,
        has_tier2=has_tier2,
        has_tier3=has_tier3,
        has_explanation=has_explanation,
        has_contradiction=has_contradiction,
    )


def score_5d_deadlock(response: str, feasibility: int) -> tuple[int, str]:
    """Tier 2: Asset 5D - Deadlock Detection.

    Asset: reasoning_5d_001 (Circular dependency in workflow)
    Tests: Multi-signal deadlock recognition (Feasibility + Keywords + Explanation)
    """
    signals = _build_deadlock_signals(response, feasibility)

    # --- SCORING LADDER ---
    for check in (
        _check_perfect_deadlock,
        _check_strong_partial,
        _check_weak_awareness,
        _check_minimal_warning,
        _check_failure,
    ):
        result = check(signals)
        if result:
            return result

    # Fallback (edge cases)
    return 20, "Edge case: Unclear response pattern"
