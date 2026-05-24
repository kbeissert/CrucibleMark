#!/usr/bin/env python3
"""CrucibleMark MCP Server — minimal HTTP transport for tooluse benchmark module."""

import argparse
import json
import logging
import os
import signal
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from tools.http_fetch import HttpFetchTool
from tools.web_search import WebSearchTool

VERSION = "1.0.0"
_DEFAULT_CONFIG = Path(__file__).parent / "config" / "mcp_config.yaml"
_PROJECT_ROOT = Path(__file__).parent.parent


def _load_config(path: Path) -> dict:
    import yaml

    with open(path) as f:
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


def _make_handler(config: dict, mode: str) -> type:
    web_search = WebSearchTool(config, mode)
    http_fetch = HttpFetchTool(config, mode)

    class MCPHandler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
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
            if self.path == "/health":
                self._send_json({"status": "ok", "mode": mode, "version": VERSION})
            else:
                self._send_json({"error": "not found"}, 404)

        def do_POST(self) -> None:
            body = self._read_json_body()
            if self.path == "/tools/web_search":
                result = web_search.search(
                    query=body.get("query", ""),
                    max_results=body.get("max_results", config["web_search"]["max_results"]),
                )
                self._send_json(result)
            elif self.path == "/tools/http_fetch":
                result = http_fetch.fetch(
                    url=body.get("url", ""),
                    max_chars=body.get("max_chars", config["http_fetch"]["max_chars"]),
                )
                self._send_json(result)
            else:
                self._send_json({"error": "not found"}, 404)

    return MCPHandler


def main() -> None:
    parser = argparse.ArgumentParser(description="CrucibleMark MCP Server")
    parser.add_argument("--mode", choices=["mock", "live"], default=None)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--config", type=Path, default=_DEFAULT_CONFIG)
    args = parser.parse_args()

    config = _load_config(args.config)
    mode = args.mode or config["server"]["mode"]
    port = args.port or config["server"]["port"]
    host = config["server"]["host"]

    _setup_logging(config)
    logger = logging.getLogger(__name__)

    pid_file = _PROJECT_ROOT / ".mcp.pid"
    pid_file.write_text(str(os.getpid()))

    def _cleanup(signum: int, frame: object) -> None:
        if pid_file.exists():
            pid_file.unlink()
        sys.exit(0)

    signal.signal(signal.SIGTERM, _cleanup)
    signal.signal(signal.SIGINT, _cleanup)

    handler_class = _make_handler(config, mode)
    server = HTTPServer((host, port), handler_class)
    logger.info("CrucibleMark MCP Server started on %s:%d (mode=%s)", host, port, mode)

    try:
        server.serve_forever()
    finally:
        if pid_file.exists():
            pid_file.unlink()


if __name__ == "__main__":
    main()
