"""
Constants for UX Writing benchmarks.
Includes thresholds, configuration defaults, and ratio mappings.
"""

from typing import Dict

# Tier Calculation Thresholds
TIER_S_THRESHOLD: float = 95.0
TIER_A_THRESHOLD: float = 85.0
TIER_B_THRESHOLD: float = 70.0
TIER_C_THRESHOLD: float = 50.0

# Evaluator Constants
MIN_SENTENCE_LENGTH: int = 15
SIMILARITY_THRESHOLD: float = 0.78
MIN_TABLE_COLUMNS: int = 2
MAX_BUTTON_LENGTH: int = 50
MAX_STEP_WORDS: int = 80
DEFAULT_MIN_REGEX_MATCHES: int = 4

# Asset-specific Required Ratios
ASSET_REQUIRED_RATIOS: Dict[str, float] = {
    "ux_writing_003": 0.5,  # Onboarding (Softer)
    "ux_writing_004": 1.0,  # A11y (Harder)
    "ux_writing_005": 0.4,  # Microcopy (Reset to Original)
}

DEFAULT_REQUIRED_RATIO: float = 0.6
