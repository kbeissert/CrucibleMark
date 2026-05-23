"""Granular scoring rubrics for Reasoning Logic benchmark (v2.0).

Extracted from evaluators.py to satisfy SSOT/Anti-God-Script rules.
Imported by evaluators.py via the constants package.
"""

from __future__ import annotations

# Keyword match-ratio thresholds for calculate_dimension_score().
# Each entry: (ratio_threshold, score_multiplier)
# Evaluated top-to-bottom; first match wins.
DIMENSION_SCORE_THRESHOLDS: tuple[tuple[float, float], ...] = (
    (0.70, 1.00),   # High saturation  → full weight
    (0.45, 0.80),   # Good saturation  → 80 %
    (0.20, 0.50),   # Minimum viable   → 50 %
    (0.01, 0.25),   # Single match     → 25 %
)

RUBRICS: dict[str, dict] = {
    "reasoning_5a_001": {
        "error_detection": {
            "weight": 40,
            "description": "Identifies the infinite loop",
            "keywords": [
                r"infinite.*loop",
                r"hangs?",
                r"freez",
                r"forever",
                r"current_index",
                r"not.*increment",
            ],
        },
        "root_cause_analysis": {
            "weight": 30,
            "description": "Locates the bug (increment inside if-block)",
            "keywords": [r"inside.*if", r"indentation", r"scope", r"else.*block"],
        },
        "solution_quality": {
            "weight": 30,
            "description": "Proposes correct fix and alternatives",
            "keywords": [
                r"\+= 1",
                r"increment",
                r"outside",
                r"move.*line",
                r"alternative",
                r"cleaner",
                r"continue",
                r"skip",
            ],
        },
    },
    "reasoning_5c_001": {
        "problem_recognition": {
            "weight": 20,
            "description": "Identifies constraints (3 meetings, 2 time slots)",
            "keywords": [
                r"three.*meetings",
                r"two.*hours",
                r"impossible",
                r"deficit",
                r"2.*hour.*3.*hour",
            ],
        },
        "logical_analysis": {
            "weight": 25,
            "description": "Explains WHY it's impossible",
            "keywords": [
                r"fit",
                r"insufficient",
                r"duration",
                r"conflict",
                r"mathematically",
                r"pigeonhole",
            ],
        },
        "appropriate_refusal": {
            "weight": 40,
            "description": "Refuses invalid request instead of forcing solution",
            "keywords": [
                r"cannot",
                r"impossible",
                r"unable",
                r"not feasible",
                r"refuse",
                r"no way",
            ],
        },
        "alternative_proposal": {
            "weight": 15,
            "description": "Suggests workarounds",
            "keywords": [
                r"alternative",
                r"reschedule",
                r"overlap",
                r"shorten",
                r"extend",
                r"remove",
            ],
        },
    },
    "reasoning_5b_001": {
        "problem_identification": {
            "weight": 20,
            "description": "Identifies the root cause domain",
            "keywords": ["database", "query", "cpu", "slow"],
        },
        "cross_domain_analysis": {
            "weight": 30,
            "description": "Traces issue across layers",
            "keywords": ["root", "cause", "underlying", "layer"],
        },
        "solution_quality": {
            "weight": 30,
            "description": "Proposes correct fix",
            "keywords": ["index", "cache", "optimize", "performance"],
        },
        "reasoning_depth": {
            "weight": 20,
            "description": "Explains WHY solution works",
            "keywords": ["reduce", "improve", "faster", "efficient"],
        },
    },
    "reasoning_5d_001": {
        "deadlock_recognition": {
            "weight": 30,
            "description": "Identifies circular dependency",
            "keywords": [
                "deadlock",
                "circular",
                "cycle",
                "mutual wait",
                "circular dependency",
            ],
        },
        "resource_identification": {
            "weight": 25,
            "description": "Names the conflicting resources (locks, threads)",
            "keywords": ["lock", "thread", "resource", "process", "mutex", "monitor"],
        },
        "causality_explanation": {
            "weight": 25,
            "description": "Explains HOW deadlock forms",
            "keywords": ["holds", "waits for", "depends on", "blocked", "waiting for"],
        },
        "solution_proposal": {
            "weight": 20,
            "description": "Suggests fix (timeout, ordering, detection)",
            "keywords": [
                "timeout",
                "order",
                "priority",
                "detect",
                "break cycle",
                "ordering",
            ],
        },
    },
    "reasoning_5e_001": {
        "paradox_recognition": {
            "weight": 25,
            "description": "Identifies the inherent conflict in requirements",
            "keywords": [
                "paradox",
                "contradiction",
                "impossible",
                "conflict",
                "requirement",
            ],
        },
        "architecture_design": {
            "weight": 30,
            "description": "Proposes a 3-phase or async architecture",
            "keywords": ["phase", "transaction", "commit", "async", "manager", "queue"],
        },
        "tradeoff_analysis": {
            "weight": 25,
            "description": "Analyzes impacts of relaxing constraints",
            "keywords": ["tradeoff", "impact", "relax", "requirement", "consequence"],
        },
        "feasibility_assessment": {
            "weight": 20,
            "description": "Assesses feasibility of the solution",
            "keywords": ["feasible", "possible", "scale", "assessment", "rating"],
        },
    },
    "reasoning_metacog_004": {
        "iterative_refinement": {
            "weight": 20,
            "description": "Shows internal thought process",
            "keywords": [r"<thought>", r"initially", r"at first", r"reconsider"],
        },
        "problem_understanding": {
            "weight": 20,
            "description": "Understands the Monty Hall setup",
            "keywords": [r"door", r"goat", r"car", r"host", r"monty"],
        },
        "probability_calculation": {
            "weight": 30,
            "description": "Correctly calculates probabilities",
            "keywords": [r"1/3", r"2/3", r"0\.66", r"66%", r"33%", r"0\.33"],
        },
        "switch_recommendation": {
            "weight": 20,
            "description": "Recommends switching doors",
            "keywords": [r"switch", r"higher.*chance", r"maximize", r"advantage"],
        },
        "explanation_quality": {
            "weight": 10,
            "description": "Explains the reasoning",
            "keywords": [
                r"reveal",
                r"information",
                r"update",
                r"\|.*\|",
                r"table",
                r"scenario",
            ],
        },
    },
}
