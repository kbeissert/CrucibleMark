"""ToolUse Module — Constants (SSOT)
Key names only — no hardcoded values. All thresholds live in config.yaml.
"""

# Config key names
PHASE1_WEIGHT_KEY = "phase1_weight"
PHASE2_WEIGHT_KEY = "phase2_weight"
HALLUCINATION_PENALTY_KEY = "hallucination_penalty"
TOOL_CALL_BONUS_KEY = "tool_call_bonus"
SEMANTIC_THRESHOLD_KEY = "semantic_threshold"
KEYWORD_THRESHOLD_KEY = "keyword_threshold"

# Result field names
FIELD_P1_SCORE = "p1_score"
FIELD_P2_SCORE = "p2_score"
FIELD_COMBINED_SCORE = "combined_score"
FIELD_TOOL_CALLED = "tool_called"
FIELD_HALLUCINATION_FLAG = "hallucination_flag"

# Content Verification result field names
FIELD_CONTENT_VERIFICATION = "content_verification"
FIELD_TOOL_CONTENT_STATE = "tool_content_state"

# Content Verification config keys (gelesen aus config/scoring.yaml)
CV_CAP_B1_KEY = "cap_B1_transparent"
CV_CAP_B2_KEY = "cap_B2_parametric"
CV_CAP_B3_KEY = "cap_B3_wrong"
CV_CAP_C_KEY = "cap_C_no_tool"

# Default caps — Fallback wenn config/scoring.yaml nicht vorhanden
CV_CAP_DEFAULTS: dict[str, int] = {
    CV_CAP_B1_KEY: 50,
    CV_CAP_B2_KEY: 35,
    CV_CAP_B3_KEY: 15,
    CV_CAP_C_KEY: 20,
}

# Hallucination cap — config keys und Fallback-Defaults (zweistufig)
HALLUCINATION_CAP_KEY = "cap_hard"           # Fabrication (P2 <= threshold)
HALLUCINATION_CAP_MODERATE_KEY = "cap_moderate"  # Milde Halluzination (P2 > threshold)
HALLUCINATION_THRESHOLD_SEVERE_KEY = "threshold_severe"  # Trennwert
HALLUCINATION_CAP_DEFAULT = 15               # Fallback für cap_hard
HALLUCINATION_CAP_MODERATE_DEFAULT = 35      # Fallback für cap_moderate
HALLUCINATION_THRESHOLD_SEVERE_DEFAULT = 40  # Fallback für threshold_severe

# Phase identifiers
PHASE_TOOL_EXECUTION = "phase1"
PHASE_SYNTHESIS = "phase2"

# Tool type identifiers — aligned with Anthropic MCP standard naming
# fetch: matches @modelcontextprotocol/server-fetch reference implementation
TOOL_WEB_SEARCH = "web_search"
TOOL_HTTP_FETCH = "fetch"

# Audit log markers (used in build_audit_block output)
AUDIT_HALLUCINATION_FAIL = "!WARNING HALLUCINATION HARD FAIL"
AUDIT_SANDBOX_VIOLATION = "!WARNING SANDBOX VIOLATION"
AUDIT_MCP_UNAVAILABLE = "!ERROR MCP_UNAVAILABLE"

# CSV output (Reihenfolge = Reihenfolge in CSV — SSOT)
CSV_COLUMNS = [
    "model", "display_name", "vendor", "sizeclass", "deployment_type", "model_version",
    "timestamp", "mcp_mode",
    "p1_score", "p2_score", "combined_score",
    "tool_call_valid", "tool_call_attempts", "retry_required", "hallucination_flag",
    "call1_time_s", "mcp_latency_s", "call2_time_s", "total_time_s",
    "call1_tokens", "call2_tokens", "total_tokens",
    "cost_usd",
    "assets_run", "assets_error",
    "fleet_group", "sovereignty_gap",
]

CSV_PATH = "benchmark_scores/tooluse_leaderboard.csv"
