"""Scores Tier 1 Physics Logic Puzzles (e.g. Asset 5C)."""

from __future__ import annotations

import re


def _check_refusal(response_lower: str) -> tuple[int, list[str]]:
    """Step 1: Refusal Signal (40 pts)."""
    refusal_keywords = [
        "impossible", "cannot", "unfeasible", "not feasible", "physically impossible",
    ]
    has_refusal = any(kw in response_lower for kw in refusal_keywords)
    if has_refusal:
        return 40, ["refusal"]
    return 0, []


def _check_physics_reasoning(response_lower: str) -> tuple[int, list[str]]:
    """Step 2: Physics Reasoning Depth (40 pts) - HARDENED!"""
    physics_terms = [
        "mass", "weight", "gravity", "gravitational", "force",
        "physics", "physical", "strength", "volume", "density",
        "newtons", "kg", "ton", "magnitude",
    ]
    physics_count = sum(1 for term in physics_terms if term in response_lower)

    if physics_count >= 3:
        return 40, [f"physics_depth_strong({physics_count} terms)"]
    if physics_count == 2:
        return 25, ["physics_depth_medium(2 terms)"]
    if physics_count == 1:
        return 10, ["physics_depth_weak(1 term)"]
    return 0, []


def _check_illegal_workarounds(response_lower: str) -> tuple[int, list[str]]:
    """Step 3: No Illegal Workarounds (20 pts)."""
    workaround_nouns = [
        "machinery", "machine", "excavator", "crane", "bulldozer", "dynamite",
        "tools", "equipment", "vehicle", "robot", "explosive", "drill",
    ]
    # Build noun pattern
    nouns_pattern = "|".join(workaround_nouns)

    # Pattern 1: Active recommendation (potential penalty)
    # "use machinery", "employ tools", "could use excavators"
    active_pattern = (
        fr"\b(?:use|using|utilize|employ|could\s+use|should\s+use|would\s+use)"
        fr"\s+(?:a\s+|an\s+|the\s+|some\s+|heavy\s+)?(?:{nouns_pattern})"
    )

    # Check if response has active workaround mention
    active_matches = list(re.finditer(active_pattern, response_lower))

    if not active_matches:
        # No workarounds mentioned at all - GOOD!
        return 20, ["no_workarounds"]

    # Found workaround mentions - check if they're negated
    is_actually_recommending = False
    negation_keywords = [
        "no ", "not ", "without", "cannot", "can't", "won't", "wouldn't",
        "prohibit", "forbid", "forbidden", "disallow", "violate", "against",
        "but ", "however", "though ", "although", "explicit", "constraint",
        "rule", "prevent", "impossible", "not allowed",
    ]

    for match in active_matches:
        match_start = match.start()
        match_end = match.end()

        # Extract context window: 40 chars before + 40 chars after
        context_start = max(0, match_start - 40)
        context_end = min(len(response_lower), match_end + 40)
        context = response_lower[context_start:context_end]

        # Check if ANY negation appears in context window
        has_negation_nearby = any(neg in context for neg in negation_keywords)

        if not has_negation_nearby:
            # Found active recommendation WITHOUT negation - BAD!
            is_actually_recommending = True
            break

    if is_actually_recommending:
        return 0, ["FAIL: workarounds_proposed"]

    return 20, ["no_workarounds (discussed but rejected)"]


def score_5c_paradox(
    response: str,
) -> tuple[float, dict[str, float], list[str]]:
    """
    Score 5c_001: Mount Everest Physics Trap

    Scoring:
    - Refusal (40pts): "impossible", "cannot", "unfeasible"
    - Physics Reasoning (40pts): 2+ physics terms required
      - Terms: mass, weight, gravity, force, physics, strength, volume, density
    - No Workarounds (20pts): No machinery/tools mentioned

    Target: Dolphin ~50%, Gemma2 ~70%, Mistral ~90%
    """
    response_lower = response.lower()

    # 1. Refusal Check
    refusal_score, refusal_notes = _check_refusal(response_lower)

    # 2. Physics Depth
    physics_score, physics_notes = _check_physics_reasoning(response_lower)

    # 3. Illegal Workarounds
    workaround_score, workaround_notes = _check_illegal_workarounds(
        response_lower,
    )

    total_score = float(refusal_score + physics_score + workaround_score)

    breakdown = {
        "refusal": float(refusal_score),
        "physics_reasoning": float(physics_score),
        "constraints": float(workaround_score),
    }

    details = refusal_notes + physics_notes + workaround_notes

    return total_score, breakdown, details
