"""Module for constants.py."""
CLI_GOLD_THRESHOLD = 90.0
CLI_SILVER_THRESHOLD = 80.0
CLI_BRONZE_THRESHOLD = 60.0

TOOL_PENALTY_FACTOR = 0.6
TOOL_PENALTY_THRESHOLD = 50.0

INLINE_TROPHY = 95.0
INLINE_STAR = 85.0
INLINE_GREEN = 75.0
INLINE_YELLOW = 60.0
INLINE_ORANGE = 50.0

BIG_TOKEN_THRESHOLD = 1000

SYSTEM_PROMPT = (
    "You are a Local AI Operations Architect testing real-world CLI tasks. "
    "Output VALID shell commands that accomplish the user's objective securely. "
    "Return ONLY the commands. Do not use Markdown wrappers unless absolutely necessary."
)
