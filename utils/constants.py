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
MAX_TOKENS_ANTHROPIC = 8192
DEFAULT_MISTRAL_MODEL = "mistral-large-latest"

# Provider / Result Type Strings (SSOT – niemals hardcoden)
MODEL_TYPE_OPEN_WEIGHTS_CLOUD = "open_weights_cloud"
RESULT_TYPE_LOCAL = "local"
RESULT_TYPE_CLOUD = "cloud"
RESULT_TYPE_COMMERCIAL = "commercial"

# Timeout-Werte (Sekunden)
TIMEOUT_OLLAMA_HEALTH = 2       # Schneller Erreichbarkeits-Ping
TIMEOUT_OLLAMA_LIST_FAST = 5    # 'ollama list' im Benchmark-Auto / Unload-Call
TIMEOUT_OLLAMA_LIST = 10        # 'ollama list' für Modell-Metadaten
TIMEOUT_OLLAMA_VERSION = 15     # 'ollama' version/show Abfrage
TIMEOUT_OLLAMA_WARMUP = 120     # Cold-Start-Warmup (großes Modell)
TIMEOUT_HTTP_FETCH = 10         # Allgemeine HTTP-Fetches (LiteLLM Pricing)
TIMEOUT_ANTHROPIC_API = 600.0   # Anthropic SDK: 8000+-Token-Generierungen

# Anthropic-Modelle, die `temperature` nicht unterstützen (Adaptive Thinking)
# Quelle: https://platform.claude.com/docs/en/docs/about-claude/models (Apr 2026)
ANTHROPIC_NO_TEMPERATURE_MODELS: frozenset[str] = frozenset({
    "claude-opus-4-7",
    "claude-sonnet-4-6",
})


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

# Provider Endpoints
OLLAMA_DEFAULT_BASE_URL = "http://localhost:11434"
MS_PER_SECOND = 1000.0

# Legacy Scoring Constants
TOTAL_SCORING_WEIGHT = 100
MAX_PERCENTAGE = 100

# Provider Constants
DEFAULT_UNLOAD_DELAY_MS = 500
