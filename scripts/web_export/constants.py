# ruff: noqa: E402
from __future__ import annotations

import sys
from pathlib import Path

_ROOT_DIR = Path(__file__).resolve().parents[2]
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))


class LdbCols:
    """Kanonische Spaltennamen der benchmark_leaderboard_detailed.csv."""
    MODEL_NAME = "Model Name"
    MODEL_ID = "Model ID"
    BADGE = "Badge"
    SIZE_CLASS = "Size Class"
    SPEED_PROFILE = "Speed Profile"
    PERFORMANCE_TIER = "Performance Tier"
    TYPE = "Type"
    TOTAL_SCORE = "Total Score"
    ROUTINE_SCORE = "Routine Score"
    REASONING_SCORE = "Reasoning Score"
    TOKENS_PER_S = "Tokens/s"
    AVG_TASK_DURATION = "Avg Task Duration (s)"
    P95_TIME = "P95 Time (s)"
    P95_LEGACY = "P95"
    MAX_TIME = "Max Time (s)"
    TIMEOUT_COUNT = "Timeout Count"
    TOKENS_TOTAL = "Tokens Total"
    COST_PER_1K = "Cost per 1K (USD)"
    BENCHMARK_COST = "Benchmark Cost (USD)"
    LLM_JUDGE_RAW = "LLM Judge Avg (raw)"
    LLM_JUDGE_DISPLAY = "LLM Judge Avg"
    LLM_JUDGE_COVERAGE = "LLM Judge Coverage"
    TESTS_RUN = "Tests Run"
    COVERAGE_RATIO = "coverage_ratio"
    VERSION = "Version"
    PROVIDER_CODE = "Provider Code"
    HARDWARE_PROFILE = "Hardware Profile"
    THINKING_MODE = "Thinking Mode"
    CODE_QUALITY = "Code Quality Audit"
    CLI_BADGE = "CLI Badge"
    UX_WRITING = "UX Writing & Microcopy"
    DOCUMENTATION_QUALITY = "Documentation Quality"
    CONTENT_TRANSFORMATION = "Content Transformation & Adaption"
    CULTURAL_INTELLIGENCE = "Cultural Intelligence"
    LOGICAL_REASONING = "Logical Reasoning"
    SYNTHESIS_QUALITY = "Synthesis Quality"
    TOOL_EXECUTION = "Tool Execution"


_SCORE_COLUMN_TO_KEY: dict[str, str] = {
    LdbCols.CODE_QUALITY: "code_quality",
    LdbCols.CLI_BADGE: "cli_benchmark",
    LdbCols.UX_WRITING: "ux_writing",
    LdbCols.DOCUMENTATION_QUALITY: "documentation_quality",
    LdbCols.CONTENT_TRANSFORMATION: "content_transformation",
    LdbCols.CULTURAL_INTELLIGENCE: "cultural_intelligence",
    LdbCols.LOGICAL_REASONING: "logical_reasoning",
    LdbCols.SYNTHESIS_QUALITY: "synthesis_quality",
    LdbCols.TOOL_EXECUTION: "tool_execution",
}
_SCORES_CONTRACT_KEYS: tuple[str, ...] = tuple(_SCORE_COLUMN_TO_KEY.values())
_BLACKLIST_PATH = _ROOT_DIR / "config" / "web_export_blacklist.yaml"
