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
SIMILARITY_THRESHOLD = 0.78  # HARDENED: Increased from 0.65 to 0.78 to prevent weak semantic matches

# Regex Patterns
# Matches markdown code blocks: ```language ... ```
PATTERN_CODE_BLOCK = r"```[\s\S]*?```"
# Matches table rows with pipes
PATTERN_TABLE_ROW = r"\|.*\|"

# Error Messages
ERROR_INVALID_RESPONSE = "Keine gültige Response erhalten"
ERROR_TEST_FAILED = "Test konnte nicht ausgeführt werden"
