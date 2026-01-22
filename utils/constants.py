"""
Centralized constants for CrucibleMark.
"""

# Default LLM Settings
DEFAULT_TEMPERATURE = 0.3
DEFAULT_MAX_RETRIES = 3
TOKEN_ESTIMATE_RATIO = 4

# Quality Thresholds (Percentage)
QUALITY_EXCELLENT = 85.0  # Trophy badge (Weltklasse)
QUALITY_GOOD = 70.0       # Star badge (Sehr gut / Brauchbar)
QUALITY_OK = 55.0         # Checkmark badge (OK für einfache Tasks)

# Provider Settings
MAX_TOKENS_ANTHROPIC = 4000
DEFAULT_MISTRAL_MODEL = 'mistral-large-latest'
