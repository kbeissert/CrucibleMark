"""
Tests for benchmark_modules/tooluse/core/io_manager.py (ToolUseIOManager).
"""

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from schemas.result import BenchmarkResult
from benchmark_modules.tooluse.core.io_manager import ToolUseIOManager
from benchmark_modules.tooluse.core.constants import AUDIT_MCP_UNAVAILABLE


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_ASSET = {"metadata": {"id": "tooluse001", "name": "EU Lizenzrecherche"}}


def _make_result(**overrides) -> BenchmarkResult:
    data = {
        "asset_id": "tooluse001",
        "tool_transcript": {
            "tool_type_called": "web_search",
            "status": "success",
            "provider": "tavily",
            "results": [{"url": "https://llama.meta.com/docs", "excerpt": "EU policy..."}],
        },
        "p1_score": 80.0,
        "p2_score": 70.0,
        "combined_score": 75.0,
        "call1_time_s": 1.8,
        "mcp_latency_s": 0.6,
        "call2_time_s": 2.0,
        "total_time_s": 4.4,
        "call1_tokens": 200,
        "call2_tokens": 212,
        "total_tokens": 412,
        "cost_usd": 0.0,
        "tool_call_attempts": 1,
        "parse_error_flag": False,
        "hallucination_flag": False,
    }
    data.update(overrides)
    return BenchmarkResult(status="success", raw_response="ok", data=data)


# ---------------------------------------------------------------------------
# Test 1: print_asset_result — string contains "P1" and "P2"
# ---------------------------------------------------------------------------

def test_print_asset_result_contains_p1_p2():
    """print_asset_result returns non-empty string with P1 and P2 score lines."""
    output = ToolUseIOManager.print_asset_result(_make_result(), _ASSET)
    assert isinstance(output, str)
    assert "P1" in output
    assert "P2" in output


# ---------------------------------------------------------------------------
# Test 2: _bar(100, 10) → full bar
# ---------------------------------------------------------------------------

def test_bar_full():
    assert ToolUseIOManager._bar(100, 10) == "██████████"


# ---------------------------------------------------------------------------
# Test 3: _bar(0, 10) → empty bar
# ---------------------------------------------------------------------------

def test_bar_empty():
    assert ToolUseIOManager._bar(0, 10) == "░░░░░░░░░░"


# ---------------------------------------------------------------------------
# Test 4: _bar(50, 10) → half bar
# ---------------------------------------------------------------------------

def test_bar_half():
    assert ToolUseIOManager._bar(50, 10) == "█████░░░░░"


# ---------------------------------------------------------------------------
# Test 5: print_asset_result — MCP unavailable → "nicht erreichbar"
# ---------------------------------------------------------------------------

def test_print_asset_result_mcp_unavailable():
    """MCP unavailable marker → output contains 'nicht erreichbar'."""
    result = BenchmarkResult(
        status="error",
        raw_response="",
        data={"audit_marker": AUDIT_MCP_UNAVAILABLE, "asset_id": "tooluse001"},
    )
    output = ToolUseIOManager.print_asset_result(result, _ASSET)
    assert "nicht erreichbar" in output


# ---------------------------------------------------------------------------
# Test 6: print_asset_result — hallucination → "HALLUZINATION"
# ---------------------------------------------------------------------------

def test_print_asset_result_hallucination():
    """hallucination_flag=True → output contains 'HALLUZINATION'."""
    result = _make_result(
        hallucination_flag=True,
        p2_score=0.0,
        combined_score=40.0,
        tool_transcript={
            "tool_type_called": "http_fetch",
            "status": "error",
            "provider": "mock",
        },
    )
    output = ToolUseIOManager.print_asset_result(result, _ASSET)
    assert "HALLUZINATION" in output


# ---------------------------------------------------------------------------
# Test 7: print_run_summary — contains "Combined" and "Empfehlung"
# ---------------------------------------------------------------------------

def test_print_run_summary_key_sections():
    """print_run_summary with results contains 'Combined' and 'Empfehlung'."""
    results = [_make_result(), _make_result()]
    output = ToolUseIOManager.print_run_summary(results, "test-model")
    assert "Combined" in output
    assert "Empfehlung" in output


# ---------------------------------------------------------------------------
# Test 8: print_run_summary — 0 assets → no crash, returns string
# ---------------------------------------------------------------------------

def test_print_run_summary_empty_no_crash():
    """Empty result list → no exception, returns a string."""
    output = ToolUseIOManager.print_run_summary([], "test-model")
    assert isinstance(output, str)
    assert len(output) > 0
