"""
Base Constants for Reasoning Logic Benchmark.
Contains global configuration and tier mappings.
"""

from typing import Dict, List, Any

# Scoring Configuration
MAX_SCORE = 100
WEIGHT_ERROR_DETECTION = 40.0
WEIGHT_SOLUTION_QUALITY = 50.0
WEIGHT_CONSISTENCY = 10.0

# Thresholds (General)
MATCH_THRESHOLD_STRONG = 0.6
MATCH_THRESHOLD_WEAK = 0.4
TOKEN_ESTIMATION_FACTOR = 1.3
SCORE_THRESHOLD_HIGH = 40.0
SCORE_THRESHOLD_MED = 30.0
BONUS_CONSISTENCY = 10.0
MIN_WORD_LENGTH = 3

# Runner Configuration
DEFAULT_TEMPERATURE = 0.6

SYSTEM_PROMPT_REASONING = (
    "You are a logic expert. Solve the given problem step-by-step. "
    "Show your reasoning process clearly ('Chain of Thought'). "
    "Finally, provide the clear Answer."
)

MODEL_REASONING_CAPABILITIES: Dict[str, Dict[str, Any]] = {
    "deepseek": {"score": 100, "type": "Explicit Reasoning", "match": "r1"},
    "qwen": {"score": 70, "type": "Implicit Reasoning", "match": None},
    "default": {"score": 20, "type": "Pattern Matching", "match": None},
}

# Tier Configuration
TIER_MAPPING: Dict[str, List[str]] = {
    "Tier 0 (Sanity Check)": ["reasoning_001_river"],
    "Tier 2 (Deep Reasoning)": [
        "reasoning_5a_001",
        "reasoning_5b_001",
        "reasoning_5c_001",
        "reasoning_5d_001",
    ],
    "Tier 3 (Metacognition)": [
        "reasoning_metacog_001",
        "reasoning_metacog_002",
        "reasoning_metacog_003",
        "reasoning_metacog_004",
        "reasoning_metacog_005",
    ],
}
