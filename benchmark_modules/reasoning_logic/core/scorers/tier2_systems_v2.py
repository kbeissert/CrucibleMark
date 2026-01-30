"""Scores additional Tier 2 Systems Thinking Assets (e.g. 5C-002, 5D-002)."""

import re
from typing import Any

from ..constants import (
    ASSET_5D_CIRCULAR_KEYWORDS,
    MAX_SCORE,
)
from ..structure_analysis import contains_any


def score_5c_multilayer(response: str) -> tuple[float, dict[str, Any], list[str]]:
    """Tier 2: Asset 5C-002 - The Monitoring Paradox (Adversarial).
    
    Scoring Dimensions:
    1. Problem Analysis (30%): Recognize conflict (Policy vs Constraint).
    2. Solution Quality (50%): Propose stub/placeholder strategy.
    3. Technical Depth (20%): Technical details (probes, 200 OK, etc).
    """
    resp_lower = response.lower()
    details = []
    
    # --- 1. Problem Analysis (30 pts) ---
    # Keywords indicating detection of the "chicken-egg" problem or conflict
    analysis_kws = ["contradict", "conflict", "paradox", "impossible", "chicken", "egg", "dependency", "circular", "policy", "constraint"]
    has_analysis = contains_any(resp_lower, analysis_kws)
    
    analysis_pts = 30.0 if has_analysis else 0.0
    if has_analysis:
        details.append("✅ Analysis: Detected dependency conflict.")
    else:
        details.append("❌ Analysis: Failed to explicitly discuss the policy conflict.")

    # --- 2. Solution Quality (50 pts) ---
    # Must propose a placeholder/stub/mock strategy
    solution_kws = ["stub", "placeholder", "mock", "dummy", "blue-green", "canary", "temporary", "health check"]
    has_solution = contains_any(resp_lower, solution_kws)
    
    # Specific trap: If they just say "impossible" and refuse (like in 5c_001), 
    # they fail this part. We check for *constructive* solution keywords.
    solution_pts = 50.0 if has_solution else 0.0
    
    if has_solution:
         details.append("✅ Solution: Proposed valid stub/placeholder strategy.")
    else:
         details.append("❌ Solution: Did not propose a 'stub' workaround.")

    # --- 3. Technical Depth (20 pts) ---
    # Look for k8s/monitoring specifics
    tech_kws = ["liveness", "readiness", "probe", "200", "http", "status code", "endpoint", "yaml", "kubernetes", "k8s"]
    # We require at least 2 distinct concepts or strong keyword match
    # kept simple: contains_any is robust enough for now
    has_tech = contains_any(resp_lower, tech_kws)
    
    tech_pts = 20.0 if has_tech else 0.0
    if has_tech:
        details.append("✅ Depth: Included technical details (probes/endpoints).")
    else:
        details.append("❌ Depth: Lacked technical specifics.")

    # Calculate Total
    total_score = analysis_pts + solution_pts + tech_pts
    
    score_breakdown = {
        "problem_analysis": float(analysis_pts),
        "solution_quality": float(solution_pts),
        "technical_depth": float(tech_pts)
    }
    
    return total_score, score_breakdown, details


def score_5d_subtle(response: str) -> tuple[float, dict[str, Any], list[str]]:
    """Tier 2: Asset 5D-002 - The Subtle Deadlock.
    
    Scoring Dimensions:
    1. Dependency Extraction (40%): Identifies the chain components.
    2. Deadlock Identification (30%): Diagnoses circularity/deadlock.
    3. Solution Proposal (30%): Suggests workaround.
    """
    resp_lower = response.lower()
    details = []
    
    # --- 1. Dependency Extraction (40 pts) ---
    # Need to mention all 3 components in relation to dependencies
    # Or generically "circular", "chain", "cycle" implies extraction
    # Better: check for component pairings like "wallet needs transaction" etc.
    # Simplified: Check for core concepts being linked
    
    # Reuse circular keywords from constants
    has_circular = contains_any(resp_lower, ASSET_5D_CIRCULAR_KEYWORDS + ["cycle", "chain", "loop", "wait for each other"])
    
    dep_pts = 40.0 if has_circular else 0.0
    if has_circular:
        details.append("✅ Dependencies: Identified circular chain.")
    else:
        details.append("❌ Dependencies: Failed to map the dependency circle.")

    # --- 2. Deadlock Identification (30 pts) ---
    # MUST extract Feasibility: 0
    # Regex for feasibility score
    feasibility_match = re.search(r"feasibility:\s*(\d+)", response, re.IGNORECASE)
    feasibility_score = int(feasibility_match.group(1)) if feasibility_match else None
    
    deadlock_pts = 0.0
    if feasibility_score is not None and feasibility_score == 0:
        deadlock_pts = 30.0
        details.append("✅ Identification: Correctly rated Feasibility: 0.")
    elif contains_any(resp_lower, ["deadlock", "impossible", "standstill", "gridlock"]):
         # Fallback if formatting was missed but concept is there
         deadlock_pts = 20.0
         details.append("⚠️ Identification: Detected deadlock but missed 'Feasibility: 0' format.")
    else:
         details.append("❌ Identification: Failed to identify it as a deadlock/impossible.")

    # --- 3. Solution Proposal (30 pts) ---
    # Solution keywords
    sol_kws = ["inject", "bootstrap", "seed", "config", "mock", "breaking the cycle", "workaround", "pre-load", "async", "eventual consistency"]
    has_sol = contains_any(resp_lower, sol_kws)
    
    sol_pts = 30.0 if has_sol else 0.0
    if has_sol:
        details.append("✅ Proposal: Suggested valid workaround/bootstrap.")
    else:
        details.append("❌ Proposal: No valid workaround offered.")

    # Calculate Total
    total_score = dep_pts + deadlock_pts + sol_pts
    
    score_breakdown = {
        "dependency_extraction": float(dep_pts),
        "deadlock_identification": float(deadlock_pts),
        "solution_proposal": float(sol_pts)
    }

    return total_score, score_breakdown, details
