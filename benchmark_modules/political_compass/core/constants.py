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

# Run configuration
PC_DEFAULT_NUM_RUNS = 2
PC_MAX_REFUSAL_RETRIES = 2
PC_RETRY_TEMPERATURES: tuple[float, ...] = (0.1, 0.4, 0.7)
PC_SLEEP_BETWEEN_REQUESTS = 1.2   # seconds between requests within a block
PC_SLEEP_AFTER_RESPONSE = 1.5     # seconds after receiving a response
PC_QUERY_TIMEOUT = 120.0          # per-request timeout in seconds

# PC v3: Format-Erinnerung für FORMAT_DEVIATION-Re-Ask (kein Anti-Refusal-Text —
# der Vanilla-Lauf bleibt methodisch sauber, vgl. Plan Entscheidung 3).
PC_FORMAT_REMINDER_APPEND = (
    "\n\n[FORMAT REMINDER: Respond with exactly one letter (A, B, C, or D) "
    "as the first character of your final answer.]"
)

# PC v3: Truncation-Re-Ask-Faktor (Budget × 2, z.B. 800 → 1600).
PC_TRUNCATION_REASK_MULTIPLIER = 2

# PC v3: Provider-Präfixe mit per-Request Thinking-Toggle (chat_template_kwargs).
# llama.cpp: enable_thinking ist Server-Start-Flag (--reasoning on), KEIN
# Request-Parameter (SSoT: memory-bank/systemPatterns.md) → degradiert auf
# Budget-Eskalation. Cloud-Connectoren haben keinen trivialen per-Request-Disable.
PC_THINKING_OFF_PROVIDER_PREFIXES: tuple[str, ...] = ("vllm",)

# PC v3: Batch-Cache-Key (SSoT). Synthetischer Asset-Key für den Batch-Cache
# (llamacpp_batch._add_political_compass_rows / _is_batch_module_done) und
# clean_results.get_module_asset_ids — NICHT identisch mit der CSV-asset_id
# ("political_compass"). Bump = bewusste Cache-Invalidierung: Bei Methodik-
# wechsel müssen alle Modelle neu gemessen werden.
PC_BATCH_ID = "political_compass_v4"
