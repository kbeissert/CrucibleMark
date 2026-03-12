"""
Constants for Code Quality Module
Single Source of Truth for RegEx patterns, default values, and thresholds.
"""

# Scoring Configuration
DEFAULT_TEMPERATURE = 0.1
TOKEN_MULTIPLIER = 1.3

# Thresholds
MIN_TABLE_COLUMNS = 2
DEFAULT_MIN_TABLE_ROWS = 8  # RESTORED: Default back to strict (Audit recommendation)
DEFAULT_MIN_KEYWORDS = 3
MIN_SENTENCE_LENGTH = 20
SIMILARITY_THRESHOLD = (
    0.78  # HARDENED: Increased from 0.65 to 0.78 to prevent weak semantic matches
)

# Regex Patterns
# Matches markdown code blocks: ```language ... ```
PATTERN_CODE_BLOCK = r"```[\s\S]*?```"
# Matches table rows with pipes
PATTERN_TABLE_ROW = r"\|.*\|"

# Error Messages
ERROR_INVALID_RESPONSE = "No valid response received"
ERROR_TEST_FAILED = "Test execution failed"
ERROR_EMPTY_RESPONSE = "Response is empty after cleaning"

# =======================
# Scoring Categories
# =======================

# Generic categories evaluated in all assets
SCORING_CATEGORIES = ["solution_quality", "formatting", "expertise"]

# Error detection category suffixes
ERROR_CATEGORY_SUFFIXES = ["_issues"]
BONUS_CATEGORY_KEY = "bonus_issues"

# =======================
# Reasoning Model Tags
# =======================

# Tags to strip from reasoning models (DeepSeek R1, o1, etc.)
REASONING_TAGS = ["think", "reasoning", "scratch", "internal"]
