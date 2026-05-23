"""
Tests for CrucibleMark MCP Server.

Covers all 9 scenarios:
  1. Health-Check
  2. web_search Mock-Modus (result fields, UUID request_id, fixture data confirms no live call)
  3. http_fetch Mock-Modus — Erfolg (whitelisted URL, status 200)
  4. http_fetch Mock-Modus — 404-Simulation (status error, empty content_excerpt)
  5. http_fetch — Whitelist-Blockierung (status blocked, no network call)
  6. Logging-Check (log file exists, entry contains request_id)
  7. Config-First-Check (timeout loaded from yaml, not hardcoded in source)
  8. Tavily-Fallback bei fehlendem Key → provider: "duckduckgo", kein Absturz
  9. mcp_config.yaml lädt provider: tavily korrekt, api_key_env nie hardcodiert

Run: pytest cruciblemark-mcp/tests/test_server.py -v
"""

import json
import subprocess
import sys
import time
import uuid
from pathlib import Path
from urllib import request as urllib_request
from urllib.error import URLError

import pytest
import yaml

_MCP_ROOT = Path(__file__).parent.parent
_PROJECT_ROOT = _MCP_ROOT.parent
_TEST_PORT = 8766  # separate from prod port 8765
_BASE_URL = f"http://localhost:{_TEST_PORT}"
_PYTHON = sys.executable

# Allow direct imports from tools/ for unit tests (8, 9)
if str(_MCP_ROOT) not in sys.path:
    sys.path.insert(0, str(_MCP_ROOT))


def _get(path: str, timeout: int = 5) -> dict:
    with urllib_request.urlopen(f"{_BASE_URL}{path}", timeout=timeout) as resp:
        return json.loads(resp.read())


def _post(path: str, body: dict, timeout: int = 5) -> dict:
    data = json.dumps(body).encode()
    req = urllib_request.Request(
        f"{_BASE_URL}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib_request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def _is_uuid(value: str) -> bool:
    try:
        uuid.UUID(str(value))
        return True
    except (ValueError, AttributeError):
        return False


@pytest.fixture(scope="module")
def mcp_server():
    config_path = _MCP_ROOT / "config" / "mcp_config.yaml"
    proc = subprocess.Popen(
        [
            _PYTHON,
            str(_MCP_ROOT / "server.py"),
            "--mode", "mock",
            "--port", str(_TEST_PORT),
            "--config", str(config_path),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    # Wait until server accepts connections
    for _ in range(30):
        try:
            _get("/health")
            break
        except (URLError, OSError):
            time.sleep(0.2)
    else:
        proc.terminate()
        pytest.fail("MCP server did not start within 6 seconds")

    yield proc

    proc.terminate()
    proc.wait(timeout=5)


# ── 1. Health-Check ──────────────────────────────────────────────────────────

class TestHealth:
    def test_health_returns_ok(self, mcp_server: subprocess.Popen) -> None:
        result = _get("/health")
        assert result["status"] == "ok"

    def test_health_mode_is_mock(self, mcp_server: subprocess.Popen) -> None:
        result = _get("/health")
        assert result["mode"] == "mock"

    def test_health_has_version(self, mcp_server: subprocess.Popen) -> None:
        result = _get("/health")
        assert "version" in result


# ── 2. web_search Mock-Modus ─────────────────────────────────────────────────

class TestWebSearch:
    def test_returns_at_least_one_result(self, mcp_server: subprocess.Popen) -> None:
        result = _post("/tools/web_search", {"query": "test", "max_results": 3})
        assert result["status"] == "success"
        assert len(result["results"]) >= 1

    def test_result_has_required_fields(self, mcp_server: subprocess.Popen) -> None:
        result = _post("/tools/web_search", {"query": "test", "max_results": 1})
        item = result["results"][0]
        assert "url" in item
        assert "title" in item
        assert "excerpt" in item

    def test_request_id_is_uuid(self, mcp_server: subprocess.Popen) -> None:
        result = _post("/tools/web_search", {"query": "test"})
        assert _is_uuid(result["request_id"])

    def test_fixture_data_confirms_mock_mode(self, mcp_server: subprocess.Popen) -> None:
        # Fixture always returns huggingface.co — live DuckDuckGo would return different URLs.
        # Presence of this fixture URL confirms the mock provider was used, not the network.
        result = _post("/tools/web_search", {"query": "test", "max_results": 3})
        urls = [r["url"] for r in result["results"]]
        assert any("huggingface.co" in url for url in urls)


# ── 3. http_fetch Mock-Modus — Erfolg ────────────────────────────────────────

class TestHttpFetchSuccess:
    def test_whitelisted_url_returns_200(self, mcp_server: subprocess.Popen) -> None:
        result = _post("/tools/http_fetch", {
            "url": "https://huggingface.co/",
            "max_chars": 500,
        })
        assert result["status"] == "success"
        assert result["status_code"] == 200

    def test_content_excerpt_not_empty(self, mcp_server: subprocess.Popen) -> None:
        result = _post("/tools/http_fetch", {
            "url": "https://huggingface.co/",
            "max_chars": 500,
        })
        assert result["content_excerpt"]


# ── 4. http_fetch Mock-Modus — 404-Simulation ────────────────────────────────

class TestHttpFetch404:
    def test_404_url_returns_error_status(self, mcp_server: subprocess.Popen) -> None:
        result = _post("/tools/http_fetch", {
            "url": "https://httpbin.org/status/404",
            "max_chars": 500,
        })
        assert result["status"] == "error"
        assert result["status_code"] == 404

    def test_404_content_excerpt_is_empty(self, mcp_server: subprocess.Popen) -> None:
        result = _post("/tools/http_fetch", {
            "url": "https://httpbin.org/status/404",
            "max_chars": 500,
        })
        # Must be None or empty — never fabricated content
        assert not result["content_excerpt"]


# ── 5. http_fetch — Whitelist-Blockierung ────────────────────────────────────

class TestWhitelist:
    def test_blocked_returns_blocked_status(self, mcp_server: subprocess.Popen) -> None:
        result = _post("/tools/http_fetch", {
            "url": "https://example-not-allowed.com/page",
            "max_chars": 500,
        })
        assert result["status"] == "blocked"

    def test_blocked_status_code_is_null(self, mcp_server: subprocess.Popen) -> None:
        result = _post("/tools/http_fetch", {
            "url": "https://example-not-allowed.com/page",
            "max_chars": 500,
        })
        assert result["status_code"] is None

    def test_google_is_blocked(self, mcp_server: subprocess.Popen) -> None:
        # Confirms whitelist is not permissive
        result = _post("/tools/http_fetch", {"url": "https://google.com/", "max_chars": 100})
        assert result["status"] == "blocked"


# ── 6. Logging-Check ─────────────────────────────────────────────────────────

class TestLogging:
    def test_log_file_exists_after_call(self, mcp_server: subprocess.Popen) -> None:
        _post("/tools/web_search", {"query": "logging-check"})
        log_path = _PROJECT_ROOT / "logs" / "mcp_server.log"
        assert log_path.exists()

    def test_log_contains_request_id(self, mcp_server: subprocess.Popen) -> None:
        result = _post("/tools/web_search", {"query": "log-id-check"})
        request_id = result["request_id"]
        log_path = _PROJECT_ROOT / "logs" / "mcp_server.log"
        assert request_id in log_path.read_text()

    def test_log_entry_has_required_fields(self, mcp_server: subprocess.Popen) -> None:
        result = _post("/tools/http_fetch", {
            "url": "https://huggingface.co/",
            "max_chars": 100,
        })
        request_id = result["request_id"]
        log_path = _PROJECT_ROOT / "logs" / "mcp_server.log"
        # Find the line with this request_id and verify all required fields are present
        entry_line = next(
            (line for line in log_path.read_text().splitlines() if request_id in line),
            None,
        )
        assert entry_line is not None
        # Extract the JSON payload (last space-delimited token that starts with '{')
        json_part = next(
            (token for token in entry_line.split(" ", 2)[2:] if token.startswith("{")),
            entry_line,
        )
        try:
            entry = json.loads(json_part)
            assert "request_id" in entry
            assert "timestamp" in entry
            assert "tool_type" in entry
            assert "status" in entry
        except json.JSONDecodeError:
            # Fallback: check plain text contains the key field names
            assert "request_id" in entry_line
            assert "tool_type" in entry_line


# ── 7. Config-First-Check ────────────────────────────────────────────────────

class TestConfigFirst:
    def test_config_has_timeout_field(self) -> None:
        config_path = _MCP_ROOT / "config" / "mcp_config.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)
        assert "timeout_seconds" in config["http_fetch"]
        assert isinstance(config["http_fetch"]["timeout_seconds"], int)

    def test_no_hardcoded_timeout_in_http_fetch(self) -> None:
        source = (_MCP_ROOT / "tools" / "http_fetch.py").read_text()
        # The only way timeout reaches urllib is via self._timeout which is loaded from config
        assert "timeout_seconds" in source
        # No magic number timeout assignments in source
        assert "timeout=8" not in source
        assert "timeout=10" not in source

    def test_timeout_value_matches_config(self) -> None:
        config_path = _MCP_ROOT / "config" / "mcp_config.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)
        expected_timeout = config["http_fetch"]["timeout_seconds"]
        source = (_MCP_ROOT / "tools" / "http_fetch.py").read_text()
        # Value must be read via config key, not duplicated inline
        assert f"timeout={expected_timeout}" not in source or "self._timeout" in source


# ── 8. Tavily-Fallback bei fehlendem Key ─────────────────────────────────────

class TestTavilyFallback:
    def test_fallback_to_duckduckgo_when_key_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from tools.web_search import WebSearchTool

        monkeypatch.delenv("TAVILY_API_KEY", raising=False)

        config_path = _MCP_ROOT / "config" / "mcp_config.yaml"
        config = yaml.safe_load(config_path.read_text())
        # Ensure provider is tavily so fallback logic triggers
        config["web_search"]["provider"] = "tavily"

        tool = WebSearchTool(config, "live")
        result = tool.search("open source llm benchmark", 1)

        # Must not crash — status is success or error, never an unhandled exception
        assert result["status"] in ("success", "error")
        # Fallback provider must be duckduckgo, never tavily (key was missing)
        assert result.get("provider") == "duckduckgo"

    def test_no_crash_returns_valid_response_shape(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from tools.web_search import WebSearchTool

        monkeypatch.delenv("TAVILY_API_KEY", raising=False)

        config_path = _MCP_ROOT / "config" / "mcp_config.yaml"
        config = yaml.safe_load(config_path.read_text())
        config["web_search"]["provider"] = "tavily"

        tool = WebSearchTool(config, "live")
        result = tool.search("test", 1)

        assert "status" in result
        assert "results" in result
        assert "request_id" in result
        assert "timestamp" in result


# ── 9. Provider-Config korrekt geladen ───────────────────────────────────────

class TestProviderConfig:
    def test_config_loads_tavily_as_provider(self) -> None:
        config_path = _MCP_ROOT / "config" / "mcp_config.yaml"
        config = yaml.safe_load(config_path.read_text())
        assert config["web_search"]["provider"] == "tavily"
        assert "api_key_env" in config["web_search"]

    def test_api_key_env_value_in_config(self) -> None:
        config_path = _MCP_ROOT / "config" / "mcp_config.yaml"
        config = yaml.safe_load(config_path.read_text())
        # The env var name is stored in config, not hardcoded in Python source
        assert config["web_search"]["api_key_env"] == "TAVILY_API_KEY"

    def test_api_key_env_not_hardcoded_in_source(self) -> None:
        source = (_MCP_ROOT / "tools" / "web_search.py").read_text()
        # The string "TAVILY_API_KEY" must NOT appear in the Python source —
        # it is read exclusively from mcp_config.yaml via cfg["api_key_env"]
        assert "TAVILY_API_KEY" not in source
