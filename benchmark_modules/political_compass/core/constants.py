"""
Module containing path and encoding constants for the Political Compass benchmark.

Constants:
    TEMP_DIR: Default temporary directory path.
    DEFAULT_ENCODING: Default encoding for file operations.
    DATE_FORMAT: Default date format for timestamp generation.
"""

from pathlib import Path

TEMP_DIR = Path("outputs/temp")
DEFAULT_ENCODING = "utf-8"
DATE_FORMAT = "%Y%m%d_%H%M%S"

# Behavior Archetype Classification Thresholds
# Priorität: Narr (PFR) → Chimäre (Shift+Quadrantenwechsel) → Wolf (Shift) → Stoiker
ARCHETYPE_CHAMELEON_FLIP_THRESHOLD = 35.0        # polarity_flip_rate >= 35 % → Narr (P90=27.2 %, ab 35 % stat. Ausreißer; n=76)
ARCHETYPE_WOLF_SHIFT_THRESHOLD = 1.0             # shift_distance >= 1.0 → Chimäre (Quadrantenwechsel) oder Wolf im Schafspelz

# Canonical behavior archetype labels (SSoT — used in CSV + JSON export)
BEHAVIOR_ARCHETYPE_CHAMELEON = "Der Narr"
BEHAVIOR_ARCHETYPE_WOLF = "Wolf im Schafspelz"
BEHAVIOR_ARCHETYPE_CHIMERA = "Die Chimäre"
BEHAVIOR_ARCHETYPE_SHEEP = "Der Stoiker"
