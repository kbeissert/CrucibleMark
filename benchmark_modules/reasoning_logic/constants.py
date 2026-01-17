"""
Constants and Configuration for Reasoning Logic Benchmark.
Separates data from logic for better maintainability.
"""

from typing import List

# Scoring Configuration
MAX_SCORE = 100.0
WEIGHT_ERROR_DETECTION = 40.0
WEIGHT_SOLUTION_QUALITY = 50.0
WEIGHT_CONSISTENCY = 10.0

# Thresholds
MATCH_THRESHOLD_STRONG = 0.6
MATCH_THRESHOLD_WEAK = 0.4
TOKEN_ESTIMATION_FACTOR = 1.3

# Asset Specific Keywords (Asset 5C - Paradox)
ASSET_5C_ILLEGAL_MOVES: List[str] = [
    "tuesday: walls", "dienstag: wände", "day 2: walls", "tag 2: wände",
    "wednesday: walls", "mittwoch: wände", "day 3: walls", "tag 3: wände",
    "concurrent", "gleichzeitig", "parallel", "while drying", "während trocknet"
]

ASSET_5C_AWARENESS_KEYWORDS: List[str] = [
    "dry", "drying", "trockn", "harden", "cure", "wait", "warten",
    "schedule", "timeline", "complex", "schwierig", "tight", "eng",
    "monday", "tuesday", "wednesday"
]

ASSET_5C_REFUSAL_KEYWORDS: List[str] = [
    "impossible", "unmöglich", "cannot", "can't", "verweigere", "unable to",
    "contradiction", "widerspruch", "conflict", "konflikt", "violation",
    "verletzung", "not feasible", "nicht machbar", "nicht enough time",
    "nicht genug zeit", "insufficient time", "overlap", "überschneidung",
    "5 days", "5 tage", "five days", "failure", "fail"
]

# Asset Specific Keywords (Asset 5D - Deadlock)
ASSET_5D_SEQUENCE_INDICATORS: List[str] = [
    "1. alpha", "1. beta", "1. gamma", "step 1:", "first start",
    "zuerst", "sequence:", "order:"
]

ASSET_5D_DETECTION_KEYWORDS: List[str] = [
    "circular", "cycle", "loop", "deadlock", "zirkulär", "kreis",
    "impossible", "unmöglich", "cannot start", "catch-22",
    "dependency hell", "mutual dependency"
]

# Asset 5D: Binary Choice Tokens
ASSET_5D_POSITIVE_TOKENS: List[str] = ["no", "nein", "false", "falsch", "impossible"]
ASSET_5D_NEGATIVE_TOKENS: List[str] = ["yes", "ja", "true", "wahr", "possible"]

# General Structure Keywords
STRUCTURE_KEYWORDS: List[str] = [
    "integral", "united", "central", "policy", "together", "integriert",
    "zentral", "zusammen", "trade-off", "tradeoff", "abwäg", "konflikt",
    "option a", "option b", "option c", "pros", "cons", "risiko",
    "unsicher", "decision", "entscheidung"
]

# Consistency Indicators
REASONING_INDICATORS: List[str] = [
    "reasoning", "thinking", "gedankengang", "prozess", "warum"
]

CORRECTION_INDICATORS: List[str] = [
    "korrektur", "corrected", "revidiert", "neu", "fazit"
]
