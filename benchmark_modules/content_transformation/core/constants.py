"""
Constants for Content Transformation Module
Defines thresholds, schemas, and weightings.
"""
# Constants
TOKEN_MULTIPLIER = 1.3
DEFAULT_TEMPERATURE = 0.7

# Tiered Difficulty Thresholds (Keyword-Matching)
# Audit Fix V4: Expert threshold lowered to 0.20 to support harder keyword sets
TIER_THRESHOLDS = {
    "labeled": 0.40,
    "standard": 0.40,
    "advanced": 0.35,
    "expert": 0.20
}

# NEW: Semantic Similarity Thresholds (per Tier)
# Previously hardcoded in _check_issue_mentioned()
SEMANTIC_THRESHOLDS = {
    "labeled": 0.45,   # Generous (for Dolphin/DeepSeek compatibility)
    "standard": 0.45,  # Generous
    "advanced": 0.50,  # Medium strictness
    "expert": 0.55     # Strict (prevents false positives in Qwen)
}

# NEW: Format-Specific Validation Rules (for Phase 2)
FORMAT_SCHEMAS = {
    "twitter_thread": {
        "pattern": r"^\d+/\d+",  # Regex for "1/5" thread numbering
        "min_tweets": 3,
        "max_chars_per_tweet": 280
    },
    "landing_page": {
        "required_sections": ["headline", "subheadline", "cta"],
        "max_headline_chars": 60
    },
    "json_export": {
        "strict_mode": True,  # Fail on extra keys
        "allow_comments": False  # No JSONC support
    }
}

# Scoring Weights (can be overridden per asset in YAML)
DEFAULT_WEIGHTS = {
    "error_detection": 0.70,  # 70% of total score
    "solution_quality": 0.30  # 30% of total score
}
