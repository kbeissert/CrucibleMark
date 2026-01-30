"""Scores Tier 1 Physics Logic Puzzles (e.g. Asset 5C)."""

from typing import Any

from ..constants import (
    ASSET_5C_AWARENESS_KEYWORDS,
    ASSET_5C_ILLEGAL_MOVES,
    ASSET_5C_REFUSAL_KEYWORDS,
    MAX_SCORE,
    WEIGHT_CONSISTENCY,
    WEIGHT_ERROR_DETECTION,
    WEIGHT_SOLUTION_QUALITY,
)
from ..structure_analysis import contains_any


def score_5c_paradox(response: str) -> tuple[int, str]:
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
    score = 0
    signals = []
    
    # Step 1: Refusal Signal (40 pts)
    refusal_keywords = ["impossible", "cannot", "unfeasible", "not feasible", "physically impossible"]
    has_refusal = any(kw in response_lower for kw in refusal_keywords)
    
    if has_refusal:
        score += 40
        signals.append("refusal")
    
    # Step 2: Physics Reasoning Depth (40 pts) - HARDENED!
    physics_terms = [
        "mass", "weight", "gravity", "gravitational", "force", 
        "physics", "physical", "strength", "volume", "density",
        "newtons", "kg", "ton", "magnitude"
    ]
    
    physics_count = sum(1 for term in physics_terms if term in response_lower)
    
    # Require 2+ terms for full points
    if physics_count >= 3:
        score += 40
        signals.append(f"physics_depth_strong({physics_count} terms)")
    elif physics_count == 2:
        score += 25
        signals.append(f"physics_depth_medium(2 terms)")
    elif physics_count == 1:
        score += 10
        signals.append(f"physics_depth_weak(1 term)")
    
    # Step 3: No Illegal Workarounds (20 pts)
    # BIDIRECTIONAL NEGATION CHECK: Look before AND after workaround mention
    import re
    
    workaround_nouns = [
        "machinery", "machine", "excavator", "crane", "bulldozer", "dynamite",
        "tools", "equipment", "vehicle", "robot", "explosive", "drill"
    ]
    
    # Build noun pattern
    nouns_pattern = "|".join(workaround_nouns)
    
    # Pattern 1: Active recommendation (potential penalty)
    # "use machinery", "employ tools", "could use excavators"
    active_pattern = fr"\b(?:use|using|utilize|employ|could\s+use|should\s+use|would\s+use)\s+(?:a\s+|an\s+|the\s+|some\s+|heavy\s+)?(?:{nouns_pattern})"
    
    # Check if response has active workaround mention
    active_matches = list(re.finditer(active_pattern, response_lower))
    
    if not active_matches:
        # No workarounds mentioned at all - GOOD!
        score += 20
        signals.append("no_workarounds")
    else:
        # Found workaround mentions - check if they're negated
        is_actually_recommending = False
        
        for match in active_matches:
            match_start = match.start()
            match_end = match.end()
            
            # Extract context window: 40 chars before + 40 chars after
            context_start = max(0, match_start - 40)
            context_end = min(len(response_lower), match_end + 40)
            context = response_lower[context_start:context_end]
            
            # Negation keywords (strong indicators this is NOT a recommendation)
            negation_keywords = [
                "no ", "not ", "without", "cannot", "can't", "won't", "wouldn't",
                "prohibit", "forbid", "forbidden", "disallow", "violate", "against",
                "but ", "however", "though ", "although", "explicit", "constraint",
                "rule", "prevent", "impossible", "not allowed"
            ]
            
            # Check if ANY negation appears in context window
            has_negation_nearby = any(neg in context for neg in negation_keywords)
            
            if not has_negation_nearby:
                # Found active recommendation WITHOUT negation - BAD!
                is_actually_recommending = True
                break
        
        if is_actually_recommending:
            signals.append("FAIL: workarounds_proposed")
            score = min(score, 50)  # Cap at 50
        else:
            # Mentions workarounds but negates them - GOOD!
            score += 20
            signals.append("no_workarounds (discussed but rejected)")
    
    # Build explanation
    if score >= 90:
        reason = f"Perfect: {', '.join(signals)}"
    elif score >= 60:
        reason = f"Partial: {', '.join(signals)}"
    else:
        reason = f"Failure: {', '.join(signals)}"
    
    return score, reason
    
    # Fallback (edge cases)
    return 20, "Edge case: Ambiguous response pattern"
