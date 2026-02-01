"""
Tier 2 Constants (Systems Design/Expert Reasoning).
Contains keywords for Asset 5B (Complex Chains) and 5D (Deadlock).
"""

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

# Solution Quality Keywords
SOLUTION_KEYWORDS_OPTIONS: list[str] = ["option a", "option b"]
SOLUTION_KEYWORDS_STEPS: list[str] = ["step", "schritt", "phase"]

# General Structure Keywords (Used in System Analysis)
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
