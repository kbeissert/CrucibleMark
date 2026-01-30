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


def score_5d_deadlock(response: str, feasibility: int) -> tuple[int, str]:
    """
    Deadlock Detection - v2.2 HARDENED
    
    Asset: reasoning_5d_001 (Circular dependency in workflow)
    Tests: Multi-signal deadlock recognition (Feasibility + Keywords + Explanation)
    
    v2.2 Changes:
    - Strikte AND-Verknüpfung: Alle 3 Signals für 100pts erforderlich
    - Tiered Keyword Detection (Basic/Advanced/Expert)
    - Contradiction Check (invalidiert Score)
    
    Args:
        response: LLM response to deadlock scenario
        feasibility: Feasibility rating (0-10 scale) from model
    
    Returns:
        (score, explanation)
        - score: 0-100 points
        - explanation: Why this score was assigned
    """
    
    response_lower = response.lower()
    
    # --- SIGNAL A: Feasibility Assessment ---
    # Model must rate task as impossible/very hard (0-2)
    feasibility_correct = feasibility <= 2
    
    # --- SIGNAL B: Keyword Detection (Tiered) ---
    deadlock_keywords_tier1 = ["impossible", "conflict", "cannot", "won't work"]
    deadlock_keywords_tier2 = ["deadlock", "circular", "paradox", "cyclic"]
    deadlock_keywords_tier3 = ["a->b->c->a", "cycle", "mutual dependency", "circular dependency"]
    
    has_tier1 = any(kw in response_lower for kw in deadlock_keywords_tier1)
    has_tier2 = any(kw in response_lower for kw in deadlock_keywords_tier2)
    has_tier3 = any(kw in response_lower for kw in deadlock_keywords_tier3)
    
    # --- SIGNAL C: Explanation Detection ---
    # Must explain WHY it's a deadlock (not just label it)
    explanation_indicators = [
        "because", "since", "therefore", "thus", "reason",
        "step 1 waits", "step 2 waits", "blocks", "dependency",
        "requires", "depends on"
    ]
    # Require at least 2 explanation indicators for quality reasoning
    explanation_count = sum(1 for ind in explanation_indicators if ind in response_lower)
    has_explanation = explanation_count >= 2
    
    # --- CONTRADICTION CHECK ---
    # Model claims it's feasible despite identifying deadlock
    contradiction_keywords = [
        "is feasible", "totally feasible", "highly feasible",
        "is possible to implement", "it can work",
        "plan works", "timeline works",
        "just need to", "simply"
    ]
    # Removed: "feasible" (too ambiguous), "solution:" (often used in explanation), "workaround" (valid advice)
    has_contradiction = any(kw in response_lower for kw in contradiction_keywords)
    
    # --- SCORING LADDER ---
    
    # Level 1: PERFECT (100pts)
    # Requires: Feasibility 0-1 AND Tier2/3 keyword AND Explanation AND No Contradiction
    if (feasibility <= 1 and 
        (has_tier2 or has_tier3) and 
        has_explanation and 
        not has_contradiction):
        return 100, "Perfect: Identified deadlock with clear explanation and correct feasibility"
    
    # Level 2: STRONG PARTIAL (70pts)
    # Feasibility 0-1 AND (Keyword OR Explanation) - but NOT both
    if feasibility <= 1:
        if (has_tier2 or has_tier3) and not has_explanation:
            return 70, "Partial: Detected deadlock terminology but missing causal explanation"
        if has_explanation and not (has_tier2 or has_tier3):
            return 70, "Partial: Explained dependency issue but missed 'deadlock' concept"
    
    # Level 3: WEAK AWARENESS (50pts)
    # Feasibility 1-2 AND Tier1 keywords (generic awareness of problem)
    if 1 <= feasibility <= 2 and has_tier1:
        return 50, "Weak: Sensed conflict but unclear on deadlock mechanism"
    
    # Level 4: MINIMAL WARNING (30pts)
    # Feasibility 3-4 (cautious but not convinced of impossibility)
    if 3 <= feasibility <= 4:
        return 30, "Minimal: Expressed doubt but no clear conflict identification"
    
    # Level 5: FAILURE (0pts)
    # Feasibility >4 (optimism bias) OR Contradiction present
    if feasibility > 4 or has_contradiction:
        return 0, "Failure: Optimism bias or contradicted deadlock with feasibility claim"
    
    # Fallback (edge cases)
    return 20, "Edge case: Unclear response pattern"
