"""
Tier 2 Expert Assets - CrucibleMark Reasoning Benchmark v2.2

Expert-level reasoning challenges for top-tier models.
Designed to prevent ceiling effects (no model should easily get 100%).
"""

from typing import Any


def score_5e_nested_paradox(response: str, feasibility: int) -> tuple[int, str]:
    """
    Nested Transaction Paradox - v2.2 NEW EXPERT ASSET
    
    Asset: reasoning_5e_001
    Tests: Multi-layered impossibility recognition + Solution design
    
    Design Philosophy:
    - Multi-dimensional scoring (40 + 40 + 20 = 100 max)
    - High technical depth requirement
    - Even commercial models should struggle for 100%
    
    Dimensions:
    1. Problem Analysis (40pts): Must identify ALL 3 requirements in conflict
    2. Solution Quality (40pts): Must propose modifying Requirement B specifically
    3. Technical Depth (20pts): Bonus for distributed systems knowledge
    
    Args:
        response: LLM response to nested paradox scenario
        feasibility: Feasibility rating (0-10 scale)
    
    Returns:
        (score, explanation)
        - score: 0-100 points
        - explanation: Multi-dimensional breakdown
    """
    
    response_lower = response.lower()
    
    # --- DIMENSION 1: Problem Analysis (40pts max) ---
    # Must identify ALL THREE requirements in conflict
    
    mentions_req_a = any(kw in response_lower for kw in 
                        ["requirement a", "async", "operations complete", "async operations"])
    mentions_req_b = any(kw in response_lower for kw in 
                        ["requirement b", "commit triggers", "cleanup"])
    mentions_req_c = any(kw in response_lower for kw in 
                        ["requirement c", "not block", "non-blocking", "must not block"])
    
    requirements_identified = sum([mentions_req_a, mentions_req_b, mentions_req_c])
    
    # Conflict Recognition (Tiered Keywords)
    conflict_keywords_basic = ["conflict", "impossible", "contradiction", "incompatible"]
    conflict_keywords_advanced = ["circular", "cyclic", "paradox", "deadlock"]
    conflict_keywords_expert = ["a->b->c->a", "dependency cycle", "mutual dependency", 
                                 "circular dependency"]
    
    has_basic_conflict = any(kw in response_lower for kw in conflict_keywords_basic)
    has_advanced_conflict = any(kw in response_lower for kw in conflict_keywords_advanced)
    has_expert_conflict = any(kw in response_lower for kw in conflict_keywords_expert)
    
    # Scoring for Dimension 1
    if requirements_identified == 3 and has_expert_conflict:
        analysis_score = 40
        analysis_note = "Perfect analysis (all reqs + expert notation)"
    elif requirements_identified == 3 and has_advanced_conflict:
        analysis_score = 35
        analysis_note = "Strong analysis (all reqs + advanced conflict)"
    elif requirements_identified >= 2 and has_advanced_conflict:
        analysis_score = 25
        analysis_note = "Partial analysis (2 reqs + conflict)"
    elif requirements_identified >= 2 or has_basic_conflict:
        analysis_score = 15
        analysis_note = "Weak analysis (basic awareness)"
    else:
        analysis_score = 0
        analysis_note = "No conflict recognition"
    
    # --- DIMENSION 2: Solution Quality (40pts max) ---
    # Must propose modifying Requirement B specifically
    
    solution_keywords_req_b = [
        "modify requirement b", "change requirement b", "break requirement b",
        "deferred cleanup", "post-commit cleanup", "async cleanup after",
        "cleanup after commit"
    ]
    solution_keywords_generic = [
        "modify", "change one requirement", "relax constraint",
        "adjust", "break the cycle"
    ]
    solution_keywords_wrong = [
        "modify requirement a", "change requirement a",
        "modify requirement c", "change requirement c",
        "it can work", "here's the architecture"
    ]
    
    has_req_b_solution = any(kw in response_lower for kw in solution_keywords_req_b)
    has_generic_solution = any(kw in response_lower for kw in solution_keywords_generic)
    has_wrong_solution = any(kw in response_lower for kw in solution_keywords_wrong)
    
    # Feasibility alignment check (should rate as impossible/very hard)
    feasibility_correct = feasibility <= 2
    
    # Scoring for Dimension 2
    if has_req_b_solution and feasibility_correct:
        solution_score = 40
        solution_note = "Perfect solution (Req B modification)"
    elif has_generic_solution and feasibility_correct and not has_wrong_solution:
        solution_score = 25
        solution_note = "Partial solution (generic modification)"
    elif feasibility_correct and not has_wrong_solution:
        solution_score = 15
        solution_note = "Recognized impossibility, no clear solution"
    elif has_wrong_solution or feasibility > 5:
        solution_score = 0
        solution_note = "Wrong solution or optimism bias"
    else:
        solution_score = 10
        solution_note = "Minimal solution attempt"
    
    # --- DIMENSION 3: Technical Depth (20pts max) ---
    # Bonus points for distributed systems knowledge
    
    technical_patterns = [
        "saga pattern", "saga", "compensation", "eventual consistency",
        "two-phase commit", "2pc", "three-phase commit", "3pc",
        "choreography", "orchestration", "idempotent",
        "transaction log", "wal", "write-ahead"
    ]
    
    technical_mentions = sum(1 for pattern in technical_patterns if pattern in response_lower)
    
    # Require 2+ patterns for full points (STRICT - Expert level!)
    if technical_mentions >= 2:
        depth_score = 20
        depth_note = "Strong technical depth (2+ patterns)"
    elif technical_mentions == 1:
        depth_score = 10
        depth_note = "Basic technical knowledge (1 pattern)"
    else:
        depth_score = 0
        depth_note = "No technical patterns mentioned"
    
    # --- FINAL SCORE ---
    total_score = analysis_score + solution_score + depth_score
    
    # Comprehensive Explanation
    explanation = (
        f"Analysis: {analysis_note} ({analysis_score}/40) | "
        f"Solution: {solution_note} ({solution_score}/40) | "
        f"Depth: {depth_note} ({depth_score}/20)"
    )
    
    return total_score, explanation
