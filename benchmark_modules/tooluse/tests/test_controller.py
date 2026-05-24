"""Tests for ToolUseTest Controller and utils/mcp_health.py.
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


from benchmark_modules.tooluse.core.constants import (
    AUDIT_MCP_UNAVAILABLE,
    FIELD_HALLUCINATION_FLAG,
    FIELD_P1_SCORE,
    FIELD_P2_SCORE,
)
from benchmark_modules.tooluse.test import ToolUseTest
from schemas.result import BenchmarkResult

# ---------------------------------------------------------------------------
# Asset paths (real files used so BaseTest._load_asset() runs normally)
# ---------------------------------------------------------------------------

ASSET_PATH_001 = _PROJECT_ROOT / "benchmark_modules/tooluse/assets/tooluse001.yaml"
ASSET_PATH_003 = _PROJECT_ROOT / "benchmark_modules/tooluse/assets/tooluse003.yaml"

MODULE_CONFIG = {
    "execution": {
        "mcp_health_url": "http://localhost:8765/health",
    },
    "config": {
        "phase1_weight": 0.5,
        "phase2_weight": 0.5,
        "hallucination_penalty": 100,
        "tool_call_bonus": 10,
        "semantic_threshold": 0.72,
        "keyword_threshold": 0.4,
    },
}


def _make_controller(asset_path: Path) -> ToolUseTest:
    """Build ToolUseTest with mocked load_module_config."""
    with patch("benchmark_modules.tooluse.test.load_module_config", return_value=MODULE_CONFIG):
        return ToolUseTest(asset_path)


def _make_llm_client(*responses: str) -> MagicMock:
    """Build a mock LLM client that returns responses in sequence."""
    client = MagicMock()
    client.query = MagicMock(side_effect=list(responses))
    client.last_token_usage = 100
    client.last_request_cost = 0.001
    client.last_response_metadata = {}
    client.last_query_duration = 0.5
    return client


# ---------------------------------------------------------------------------
# Test 1: MCP unavailable → BenchmarkResult status="error"
# ---------------------------------------------------------------------------

def test_execute_mcp_unavailable():
    """MCP health check fails → clean error result, no exception."""
    controller = _make_controller(ASSET_PATH_001)

    with patch("benchmark_modules.tooluse.test.check_mcp_health") as mock_health:
        mock_health.return_value = {"status": "unavailable", "error": "Connection refused"}

        llm = _make_llm_client()
        result = controller.execute("gpt-4o", llm)

    assert result.status == "error"
    assert result.data.get("audit_marker") == AUDIT_MCP_UNAVAILABLE
    llm.query.assert_not_called()


# ---------------------------------------------------------------------------
# Test 2: Model returns valid tool call → tool_transcript present
# ---------------------------------------------------------------------------

def test_execute_valid_tool_call():
    """Model produces a valid tool_call JSON → MCP is called → transcript stored."""
    controller = _make_controller(ASSET_PATH_001)

    with patch("benchmark_modules.tooluse.test.check_mcp_health") as mock_health, \
         patch("benchmark_modules.tooluse.test._call_mcp_tool") as mock_mcp:

        mock_health.return_value = {"status": "ok", "mode": "mock"}
        mock_mcp.return_value = {
            "status": "success",
            "provider": "tavily",
            "results": [{"url": "https://llama.meta.com/docs", "excerpt": "EU policy..."}],
        }

        llm = _make_llm_client(
            '{"tool_call": {"name": "web_search", "parameters": {"query": "Meta Llama EU"}}}',
            "Meta Llama ist in der EU beschränkt.",
        )

        result = controller.execute("gpt-4o", llm)

    assert result.status == "success"
    transcript = result.data.get("tool_transcript", {})
    assert transcript.get("status") == "success"
    mock_mcp.assert_called_once()


# ---------------------------------------------------------------------------
# Test 3: Model returns no tool call → parse_error in transcript
# ---------------------------------------------------------------------------

def test_execute_no_tool_call():
    """Model gives plain text (no JSON) → parse_error transcript, benchmark continues."""
    controller = _make_controller(ASSET_PATH_001)

    with patch("benchmark_modules.tooluse.test.check_mcp_health") as mock_health:
        mock_health.return_value = {"status": "ok", "mode": "mock"}

        # 3 responses: call1 → retry → synthesis (retry fires on first parse failure)
        llm = _make_llm_client(
            "Ich weiß es nicht.",
            "Auch der Retry liefert keinen Tool-Call.",
            "Sorry, keine Informationen verfügbar.",
        )

        result = controller.execute("gpt-4o", llm)

    assert result.status == "success"
    transcript = result.data.get("tool_transcript", {})
    assert transcript.get("status") == "parse_error"


# ---------------------------------------------------------------------------
# Test 4: score_response fills all required fields
# ---------------------------------------------------------------------------

def test_score_response_required_fields():
    """score_response must populate primary_score, p1/p2, and audit_block."""
    controller = _make_controller(ASSET_PATH_001)

    pre_result = BenchmarkResult(
        status="success",
        raw_response="Meta Llama hat EU-Lizenzbeschränkungen. Weitere Infos auf llama.meta.com.",
        data={
            "tool_transcript": {
                "tool_type_called": "web_search",
                "status": "success",
                "status_code": 200,
                "results": [{"url": "https://llama.meta.com/", "excerpt": "EU policy"}],
                "provider": "tavily",
                "request_id": "test-001",
                "timestamp": "2026-05-23T10:00:00Z",
            },
            "response_1": '{"tool_call": {"name": "web_search", "parameters": {}}}',
            "asset_id": "tooluse001",
        },
    )

    result = controller.score_response(pre_result)

    assert isinstance(result.primary_score, float)
    assert FIELD_P1_SCORE in result.data
    assert FIELD_P2_SCORE in result.data
    assert result.data["audit_block"].startswith("--- TOOL USE TRANSCRIPT ---")


# ---------------------------------------------------------------------------
# Test 5: is_failure_test — model hallucinates → p2=0, hallucination_flag=True
# ---------------------------------------------------------------------------

def test_score_response_failure_test_hallucination():
    """Forbidden pattern in output → p2_score=0, hallucination_flag=True."""
    controller = _make_controller(ASSET_PATH_003)

    pre_result = BenchmarkResult(
        status="success",
        raw_response="Die Seite zeigt ausführliche Inhalte über HuggingFace-Modelle.",
        data={
            "tool_transcript": {
                "tool_type_called": "fetch",
                "status": "error",
                "status_code": 404,
                "content_excerpt": None,
                "provider": "mock",
                "request_id": "test-003",
                "timestamp": "2026-05-23T10:00:00Z",
            },
            "response_1": '{"tool_call": {"name": "fetch", "parameters": {}}}',
            "asset_id": "tooluse003",
        },
    )

    result = controller.score_response(pre_result)

    assert result.data[FIELD_P2_SCORE] == 0.0
    assert result.data[FIELD_HALLUCINATION_FLAG] is True


# ---------------------------------------------------------------------------
# Test 6: utils/mcp_health.py — never raises, always returns dict
# ---------------------------------------------------------------------------

def test_mcp_health_no_exception():
    """check_mcp_health must never raise — returns dict in both cases."""
    from utils.mcp_health import check_mcp_health

    result_down = check_mcp_health("http://localhost:19999/health", timeout=1)
    assert isinstance(result_down, dict)
    assert result_down["status"] in ("ok", "unavailable")

    mock_response_body = json.dumps({"status": "ok", "mode": "mock"}).encode()
    mock_resp = MagicMock()
    mock_resp.read.return_value = mock_response_body
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_resp):
        result_up = check_mcp_health("http://localhost:8765/health", timeout=3)

    assert isinstance(result_up, dict)
    assert result_up["status"] == "ok"
    assert result_up.get("mode") == "mock"
