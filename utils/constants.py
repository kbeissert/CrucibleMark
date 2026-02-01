"""
Centralized constants for CrucibleMark.
"""

# Default LLM Settings
DEFAULT_TEMPERATURE = 0.3
DEFAULT_MAX_RETRIES = 3
TOKEN_ESTIMATE_RATIO = 4

# Quality Thresholds (Percentage)
QUALITY_EXCELLENT = 85.0  # Trophy badge (Weltklasse)
QUALITY_GOOD = 70.0  # Star badge (Sehr gut / Brauchbar)
QUALITY_OK = 55.0  # Checkmark badge (OK für einfache Tasks)

# Provider Settings
MAX_TOKENS_ANTHROPIC = 4000
DEFAULT_MISTRAL_MODEL = "mistral-large-latest"


class Colors:
    """ANSI Colors for Terminal Output."""
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"

