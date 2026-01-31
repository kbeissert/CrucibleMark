"""
Tier 2 Expert Assets - CrucibleMark Reasoning Benchmark v2.2

Expert-level reasoning challenges for top-tier models.
Designed to prevent ceiling effects (no model should easily get 100%).
"""

from ..constants import (
    EXPERT_ANALYSIS_PERFECT,
    EXPERT_REQUIREMENTS_ALL,
)


def _analyze_problem(response_lower: str) -> tuple[int, str]:
    """Dimension 1: Problem Analysis (40pts max)"""
    mentions_req_a = any(
        kw in response_lower
        for kw in [
            "requirement a",
            "async",
            "operations complete",
            "async operations",
        ]
    )
    mentions_req_b = any(
        kw in response_lower
        for kw in ["requirement b", "commit triggers", "cleanup"]
    )
    mentions_req_c = any(
        kw in response_lower
        for kw in [
            "requirement c",
            "not block",
            "non-blocking",
            "must not block",
        ]
    )

    requirements_identified = sum(
        [mentions_req_a, mentions_req_b, mentions_req_c]
    )

    conflict_keywords_basic = [
        "conflict",
        "impossible",
        "contradiction",
        "incompatible",
    ]
    conflict_keywords_advanced = ["circular", "cyclic", "paradox", "deadlock"]
    conflict_keywords_expert = [
        "a->b->c->a",
        "dependency cycle",
        "mutual dependency",
        "circular dependency",
    ]

    has_basic_conflict = any(
        kw in response_lower for kw in conflict_keywords_basic
    )
    has_advanced_conflict = any(
        kw in response_lower for kw in conflict_keywords_advanced
    )
    has_expert_conflict = any(
        kw in response_lower for kw in conflict_keywords_expert
    )

    if (
        requirements_identified == EXPERT_REQUIREMENTS_ALL
        and has_expert_conflict
    ):
        return EXPERT_ANALYSIS_PERFECT, "Perfect analysis (all reqs + expert notation)"
    if requirements_identified == 3 and has_advanced_conflict:
        return 35, "Strong analysis (all reqs + advanced conflict)"
    if requirements_identified >= 2 and has_advanced_conflict:
        return 25, "Partial analysis (2 reqs + conflict)"
    if requirements_identified >= 2 or has_basic_conflict:
        return 15, "Weak analysis (basic awareness)"

    return 0, "No conflict recognition"


def _evaluate_solution(
    response_lower: str, feasibility: int
) -> tuple[int, str]:
    """Dimension 2: Solution Quality (40pts max)"""
    solution_keywords_req_b = [
        "modify requirement b",
        "change requirement b",
        "break requirement b",
        "deferred cleanup",
        "post-commit cleanup",
        "async cleanup after",
        "cleanup after commit",
    ]
    solution_keywords_generic = [
        "modify",
        "change one requirement",
        "relax constraint",
        "adjust",
        "break the cycle",
    ]
    solution_keywords_wrong = [
        "modify requirement a",
        "change requirement a",
        "modify requirement c",
        "change requirement c",
        "it can work",
        "here's the architecture",
    ]

    has_req_b_solution = any(
        kw in response_lower for kw in solution_keywords_req_b
    )
    has_generic_solution = any(
        kw in response_lower for kw in solution_keywords_generic
    )
    has_wrong_solution = any(
        kw in response_lower for kw in solution_keywords_wrong
    )

    feasibility_correct = feasibility <= 2

    if has_req_b_solution and feasibility_correct:
        return 40, "Perfect solution (Req B modification)"
    if has_generic_solution and feasibility_correct and not has_wrong_solution:
        return 25, "Partial solution (generic modification)"
    if feasibility_correct and not has_wrong_solution:
        return 15, "Recognized impossibility, no clear solution"
    if has_wrong_solution or feasibility > 5:
        return 0, "Wrong solution or optimism bias"

    return 10, "Minimal solution attempt"


def _assess_technical_depth(response_lower: str) -> tuple[int, str]:
    """Dimension 3: Technical Depth (20pts max)"""
    technical_patterns = [
        "saga pattern",
        "saga",
        "compensation",
        "eventual consistency",
        "two-phase commit",
        "2pc",
        "three-phase commit",
        "3pc",
        "choreography",
        "orchestration",
        "idempotent",
        "transaction log",
        "wal",
        "write-ahead",
    ]

    technical_mentions = sum(
        1 for pattern in technical_patterns if pattern in response_lower
    )

    if technical_mentions >= 2:
        return 20, "Strong technical depth (2+ patterns)"
    if technical_mentions == 1:
        return 10, "Basic technical knowledge (1 pattern)"

    return 0, "No technical patterns mentioned"


def score_5e_nested_paradox(
    response: str, feasibility: int
) -> tuple[int, str]:
    """
    Nested Transaction Paradox - v2.2 NEW EXPERT ASSET

    Asset: reasoning_5e_001
    Tests: Multi-layered impossibility recognition + Solution design
    """
    response_lower = response.lower()

    analysis_score, analysis_note = _analyze_problem(response_lower)
    solution_score, solution_note = _evaluate_solution(
        response_lower, feasibility
    )
    depth_score, depth_note = _assess_technical_depth(response_lower)

    total_score = analysis_score + solution_score + depth_score

    explanation = (
        f"Analysis: {analysis_note} ({analysis_score}/40) | "
        f"Solution: {solution_note} ({solution_score}/40) | "
        f"Depth: {depth_note} ({depth_score}/20)"
    )

    return total_score, explanation
