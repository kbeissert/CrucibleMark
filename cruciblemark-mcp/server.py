#!/usr/bin/env python3
# ruff: noqa: EXE001
"""CrucibleMark MCP Server — minimal HTTP transport for tooluse benchmark module."""

import argparse
import json
import logging
import os
import signal
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))

from tools.http_fetch import HttpFetchTool
from tools.web_search import WebSearchTool

VERSION = "1.0.0"
_DEFAULT_CONFIG = Path(__file__).parent / "config" / "mcp_config.yaml"
_PROJECT_ROOT = Path(__file__).parent.parent

# MCP-standard tool definitions (inputSchema per JSON Schema draft-07)
TOOL_DEFINITIONS = [
    {
        "name": "web_search",
        "description": "Search the web for current information using a search engine.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query"},
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "fetch",
        "description": (
            "Fetches a URL from the internet and optionally extracts its contents as markdown."
            " Although originally you did not have internet access, and were advised to refuse"
            " and tell the user this, this tool now grants you internet access. Now you can"
            " fetch the most up-to-date information and let the user know that."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to fetch"},
                "max_length": {
                    "type": "integer",
                    "description": "Maximum number of characters to return.",
                    "default": 5000,
                    "exclusiveMinimum": 0,
                    "exclusiveMaximum": 1000000,
                },
                "start_index": {
                    "type": "integer",
                    "description": (
                        "On return output starting at this character index, useful if a"
                        " previous fetch was truncated and more context is required."
                    ),
                    "default": 0,
                    "minimum": 0,
                },
                "raw": {
                    "type": "boolean",
                    "description": "Get the actual HTML content of the requested page, without simplification.",
                    "default": False,
                },
            },
            "required": ["url"],
        },
    },
]


def _load_config(path: Path) -> dict:
    """Load YAML config from path."""
    with path.open() as f:
        return yaml.safe_load(f)


def _setup_logging(config: dict) -> None:
    log_cfg = config.get("logging", {})
    log_file = _PROJECT_ROOT / log_cfg.get("log_file", "logs/mcp_server.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_level = getattr(logging, log_cfg.get("log_level", "INFO").upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout),
        ],
    )


def _make_handler(config: dict, mode: str, last_activity: list[float]) -> type:
    """Build and return the MCPHandler class with config, mode, and activity tracker bound via closure."""
    web_search = WebSearchTool(config, mode)
    http_fetch = HttpFetchTool(config, mode)

    class MCPHandler(BaseHTTPRequestHandler):
        """HTTP request handler for MCP tool endpoints."""
        def log_message(self, format: str, *args: object) -> None:  # noqa: A002  # pylint: disable=redefined-builtin
            pass  # suppress default access log; structured logging is done in tools

        def _send_json(self, data: dict, status: int = 200) -> None:
            body = json.dumps(data).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _read_json_body(self) -> dict:
            length = int(self.headers.get("Content-Length", 0))
            return json.loads(self.rfile.read(length)) if length else {}

        def do_GET(self) -> None:
            """Handle GET /health."""
            last_activity[0] = time.monotonic()
            if self.path == "/health":
                self._send_json({"status": "ok", "mode": mode, "version": VERSION})
            else:
                self._send_json({"error": "not found"}, 404)

        def do_POST(self) -> None:
            """JSON-RPC 2.0 dispatcher — handles initialize, tools/list, tools/call."""
            last_activity[0] = time.monotonic()
            body = self._read_json_body()
            rpc_id = body.get("id")
            method = body.get("method", "")
            params = body.get("params") or {}

            if method == "initialize":
                result: dict = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "cruciblemark-mcp", "version": VERSION},
                }
                self._send_json({"jsonrpc": "2.0", "id": rpc_id, "result": result})

            elif method == "notifications/initialized":
                # Client acknowledgement — no response required for notifications
                self.send_response(204)
                self.end_headers()

            elif method == "tools/list":
                self._send_json({
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "result": {"tools": TOOL_DEFINITIONS},
                })

            elif method == "tools/call":
                name = params.get("name", "")
                arguments = params.get("arguments") or {}
                if name == "web_search":
                    tool_result = web_search.search(
                        query=arguments.get("query", ""),
                        max_results=arguments.get("max_results", config["web_search"]["max_results"]),
                    )
                elif name == "fetch":
                    # Accept both Anthropic-standard `max_length` and our internal `max_chars`
                    max_chars = (
                        arguments.get("max_length")
                        or arguments.get("max_chars")
                        or config["http_fetch"]["max_chars"]
                    )
                    start_index: int = arguments.get("start_index") or 0
                    raw_result = http_fetch.fetch(
                        url=arguments.get("url", ""),
                        max_chars=max_chars,
                    )
                    # Apply start_index slicing to content text (pagination support)
                    if start_index > 0 and isinstance(raw_result.get("content"), list):
                        for block in raw_result["content"]:
                            if block.get("type") == "text" and block.get("text"):
                                block["text"] = block["text"][start_index : start_index + max_chars]
                    tool_result = raw_result
                else:
                    self._send_json({
                        "jsonrpc": "2.0",
                        "id": rpc_id,
                        "error": {"code": -32601, "message": f"Unknown tool: {name}"},
                    })
                    return
                self._send_json({"jsonrpc": "2.0", "id": rpc_id, "result": tool_result})

            else:
                self._send_json({
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                }, 404)

    return MCPHandler


def main() -> None:
    """Parse CLI args, load config, and start the MCP HTTP server."""
    parser = argparse.ArgumentParser(description="CrucibleMark MCP Server")
    parser.add_argument("--mode", choices=["mock", "live"], default=None)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--idle-timeout", type=int, default=None,
                        help="Auto-shutdown after N seconds of inactivity (0 = disabled)")
    parser.add_argument("--config", type=Path, default=_DEFAULT_CONFIG)
    args = parser.parse_args()

    config = _load_config(args.config)
    mode = args.mode or config["server"]["mode"]
    port = args.port or config["server"]["port"]
    host = config["server"]["host"]
    idle_timeout: int = (
        args.idle_timeout
        if args.idle_timeout is not None
        else config["server"].get("idle_timeout_seconds", 300)
    )

    _setup_logging(config)
    logger = logging.getLogger(__name__)

    pid_file = _PROJECT_ROOT / ".mcp.pid"
    pid_file.write_text(str(os.getpid()))

    def _cleanup(_signum: int, _frame: object) -> None:
        if pid_file.exists():
            pid_file.unlink()
        sys.exit(0)

    signal.signal(signal.SIGTERM, _cleanup)
    signal.signal(signal.SIGINT, _cleanup)

    last_activity: list[float] = [time.monotonic()]
    handler_class = _make_handler(config, mode, last_activity)
    server = HTTPServer((host, port), handler_class)

    idle_msg = f", idle-timeout={idle_timeout}s" if idle_timeout > 0 else ", idle-timeout=disabled"
    logger.info("CrucibleMark MCP Server started on %s:%d (mode=%s%s)", host, port, mode, idle_msg)

    if idle_timeout > 0:
        poll_interval = min(max(idle_timeout // 5, 2), 30)  # poll alle 2–30 s

        def _watchdog() -> None:
            while True:
                time.sleep(poll_interval)
                idle = time.monotonic() - last_activity[0]
                if idle >= idle_timeout:
                    logger.info(
                        "MCP Server idle for %.0fs (limit=%ds) — shutting down.",
                        idle, idle_timeout,
                    )
                    server.shutdown()
                    break

        threading.Thread(target=_watchdog, daemon=True, name="mcp-watchdog").start()

    try:
        server.serve_forever()
    finally:
        if pid_file.exists():
            pid_file.unlink()


if __name__ == "__main__":
    main()
