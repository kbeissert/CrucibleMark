"""
Constants and Configuration for Reasoning Logic Benchmark.
Separates data from logic for better maintainability.
"""

# Scoring Configuration
MAX_SCORE = 100.0
WEIGHT_ERROR_DETECTION = 40.0
WEIGHT_SOLUTION_QUALITY = 50.0
WEIGHT_CONSISTENCY = 10.0

# Thresholds
MATCH_THRESHOLD_STRONG = 0.6
MATCH_THRESHOLD_WEAK = 0.4
TOKEN_ESTIMATION_FACTOR = 1.3
SCORE_THRESHOLD_HIGH = 40.0
SCORE_THRESHOLD_MED = 30.0
BONUS_CONSISTENCY = 10.0
MIN_WORD_LENGTH = 3

# Feasibility Scores (Asset 5D)
FEASIBILITY_IMPOSSIBLE = 0
FEASIBILITY_LOW_MAX = 3
FEASIBILITY_HIGH_MIN = 4
FEASIBILITY_HIGH_MAX = 5

# Asset Specific Keywords (Asset 5B - Complex Chains)
ASSET_5B_CORE_KEYWORDS: list[str] = [
    "versioning",
    "deprecation",
    "lifecycle",
    "veraltet",
    "versionierung",
    "api version",
]

ASSET_5B_QUALIFIER_KEYWORDS: list[str] = [
    "inconsistent",
    "strategy",
    "mismatch",
    "conflict",
    "inkonsistent",
    "widersprüchlich",
    "confusion",
    "ambiguity",
]

ASSET_5B_DOMAIN_KEYWORDS: list[str] = [
    "code",
    "docs",
    "documentation",
    "ux",
    "frontend",
    "backend",
]

ASSET_5B_CONCEPT_KEYWORDS: list[str] = [
    "alignment",
    "consistency",
    "reflect",
    "mirror",
    "dependency",
    "abhängigkeit",
    "spiegeln",
    "synchronize",
    "match",
]

ASSET_5B_SOLUTION_KEYWORDS: list[str] = [
    "unified",
    "policy",
    "standard",
    "communication",
    "central",
    "einheitlich",
    "kommunikation",
    "governance",
    "single source",
]

ASSET_5B_PRIO_KEYWORDS: list[str] = [
    "priorit",
    "immediate",
    "short-term",
    "first step",
    "sofort",
    "schritt 1",
]


# Asset Specific Keywords (Asset 5C - Paradox)
ASSET_5C_ILLEGAL_MOVES: list[str] = [
    "tuesday: walls",
    "dienstag: wände",
    "day 2: walls",
    "tag 2: wände",
    "wednesday: walls",
    "mittwoch: wände",
    "day 3: walls",
    "tag 3: wände",
    "concurrent",
    "gleichzeitig",
    "parallel",
    "while drying",
    "während trocknet",
]

ASSET_5C_AWARENESS_KEYWORDS: list[str] = [
    "dry",
    "drying",
    "trockn",
    "harden",
    "cure",
    "wait",
    "warten",
    "schedule",
    "timeline",
    "complex",
    "schwierig",
    "tight",
    "eng",
    "monday",
    "tuesday",
    "wednesday",
]

ASSET_5C_REFUSAL_KEYWORDS: list[str] = [
    "impossible",
    "unmöglich",
    "cannot",
    "can't",
    "verweigere",
    "unable to",
    "contradiction",
    "widerspruch",
    "conflict",
    "konflikt",
    "violation",
    "verletzung",
    "not feasible",
    "nicht machbar",
    "nicht enough time",
    "nicht genug zeit",
    "insufficient time",
    "overlap",
    "überschneidung",
    "5 days",
    "5 tage",
    "five days",
    "failure",
    "fail",
]

# Asset Specific Keywords (Asset 5D - Deadlock)
ASSET_5D_SEQUENCE_INDICATORS: list[str] = [
    "1. alpha",
    "1. beta",
    "1. gamma",
    "step 1:",
    "first start",
    "zuerst",
    "sequence:",
    "order:",
]

ASSET_5D_DETECTION_KEYWORDS: list[str] = [
    "circular",
    "cycle",
    "loop",
    "deadlock",
    "zirkulär",
    "kreis",
    "impossible",
    "unmöglich",
    "cannot start",
    "catch-22",
    "dependency hell",
    "mutual dependency",
]

ASSET_5D_DEADLOCK_KEYWORDS: list[str] = [
    "impossible",
    "deadlock",
    "unsolvable",
    "cannot be implemented",
]

ASSET_5D_CIRCULAR_KEYWORDS: list[str] = [
    "circular dependency",
    "circular reference",
    "mutual exclusion",
    "cycle detected",
]

ASSET_5D_WARNING_KEYWORDS: list[str] = [
    "high risk",
    "complex",
    "race condition",
    "challenging",
    "careful synchronization",
]

# Asset 5D: Binary Choice Tokens
ASSET_5D_POSITIVE_TOKENS: list[str] = ["no", "nein", "false", "falsch", "impossible"]
ASSET_5D_NEGATIVE_TOKENS: list[str] = ["yes", "ja", "true", "wahr", "possible"]

# General Structure Keywords
STRUCTURE_KEYWORDS: list[str] = [
    "integral",
    "united",
    "central",
    "policy",
    "together",
    "integriert",
    "zentral",
    "zusammen",
    "trade-off",
    "tradeoff",
    "abwäg",
    "konflikt",
    "option a",
    "option b",
    "option c",
    "pros",
    "cons",
    "risiko",
    "unsicher",
    "decision",
    "entscheidung",
]

# Consistency Indicators
REASONING_INDICATORS: list[str] = [
    "reasoning",
    "thinking",
    "gedankengang",
    "prozess",
    "warum",
]

CORRECTION_INDICATORS: list[str] = [
    "korrektur",
    "corrected",
    "revidiert",
    "neu",
    "fazit",
]


# Runner Configuration
DEFAULT_TEMPERATURE = 0.6

SYSTEM_PROMPT_REASONING = (
    "You are a logic expert. Solve the given problem step-by-step. "
    "Show your reasoning process clearly ('Chain of Thought'). "
    "Finally, provide the clear Answer."
)

MODEL_REASONING_CAPABILITIES = {
    "deepseek": {"score": 100, "type": "Explicit Reasoning", "match": "r1"},
    "qwen": {"score": 70, "type": "Implicit Reasoning", "match": None},
    "default": {"score": 20, "type": "Pattern Matching", "match": None},
}

# Solution Quality Configuration
SOLUTION_WEIGHT_STRUCTURE = 0.4
SOLUTION_WEIGHT_OPTIONS = 0.2
SOLUTION_WEIGHT_STEPS = 0.2
SOLUTION_KEYWORDS_OPTIONS = ["option a", "option b"]
SOLUTION_KEYWORDS_STEPS = ["step", "schritt", "phase"]

# Tier Configuration
TIER_MAPPING = {
    "Tier 0 (Sanity Check)": ["reasoning_001_river"],
    "Tier 2 (Deep Reasoning)": [
        "reasoning_5a_001",
        "reasoning_5b_001",
        "reasoning_5c_001",
        "reasoning_5d_001",
    ],
}
