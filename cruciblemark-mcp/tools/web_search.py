"""Web search tool — Tavily (primary) and DuckDuckGo (fallback) implementations."""

import json
import logging
import os
from datetime import datetime, timezone
from urllib import request as urllib_request
from urllib.parse import urlencode

from tools.mock_provider import mock_web_search, new_request_id

logger = logging.getLogger(__name__)

_EXCERPT_MAX_CHARS = 300
_TITLE_MAX_CHARS = 80


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class WebSearchTool:
    """Executes web searches via Tavily (primary) or DuckDuckGo (fallback)."""

    def __init__(self, config: dict, mode: str) -> None:
        cfg = config["web_search"]
        self._mode = mode
        self._provider: str = cfg["provider"]
        self._fallback_provider: str = cfg.get("fallback_provider", "duckduckgo")
        self._timeout: int = cfg["timeout_seconds"]
        self._default_max: int = cfg["max_results"]
        self._api_key_env: str = cfg.get("api_key_env", "")
        self._search_depth: str = cfg.get("search_depth", "basic")

    def search(self, query: str, max_results: int) -> dict:
        """Run a search query and return structured results dict."""
        request_id = new_request_id()
        timestamp = _now()

        if self._mode == "mock":
            result = mock_web_search(query, max_results, self._provider)
            result["request_id"] = request_id
            result["timestamp"] = timestamp
        else:
            result = self._live_search(query, max_results, request_id, timestamp)

        logger.info(
            json.dumps({
                "request_id": request_id,
                "timestamp": timestamp,
                "tool_type": "web_search",
                "status": result["status"],
                "provider": result.get("provider", self._provider),
                "query": query,
            }),
        )
        return result

    def _live_search(self, query: str, max_results: int, request_id: str, timestamp: str) -> dict:
        if self._provider == "tavily":
            api_key = os.environ.get(self._api_key_env, "") if self._api_key_env else ""
            if api_key:
                return self._tavily_search(query, max_results, api_key, request_id, timestamp)
            logger.warning("[MCP] Tavily key not found, falling back to DuckDuckGo")
        return self._duckduckgo_search(query, max_results, request_id, timestamp)

    def _tavily_search(
        self, query: str, max_results: int, api_key: str, request_id: str, timestamp: str,
    ) -> dict:
        payload = json.dumps({
            "api_key": api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": self._search_depth,
            "include_answer": False,
            "include_raw_content": False,
        }).encode()
        req = urllib_request.Request(
            "https://api.tavily.com/search",
            data=payload,
            headers={"Content-Type": "application/json", "User-Agent": "CrucibleMark/1.0"},
            method="POST",
        )
        try:
            with urllib_request.urlopen(req, timeout=self._timeout) as resp:  # noqa: S310
                data = json.loads(resp.read().decode())
        except Exception:
            logger.exception("Tavily search failed")
            return {
                "status": "error",
                "results": [],
                "request_id": request_id,
                "provider": "tavily",
                "timestamp": timestamp,
            }

        results = [
            {
                "url": item.get("url", ""),
                "title": item.get("title", ""),
                "excerpt": item.get("content", "")[:_EXCERPT_MAX_CHARS],
            }
            for item in data.get("results", [])[:max_results]
        ]
        return {
            "status": "success",
            "results": results,
            "request_id": request_id,
            "provider": "tavily",
            "timestamp": timestamp,
        }

    def _duckduckgo_search(
        self, query: str, max_results: int, request_id: str, timestamp: str,
    ) -> dict:
        params = urlencode({
            "q": query,
            "format": "json",
            "no_html": "1",
            "skip_disambig": "1",
        })
        req = urllib_request.Request(
            f"https://api.duckduckgo.com/?{params}",
            headers={"User-Agent": "CrucibleMark/1.0"},
        )
        try:
            with urllib_request.urlopen(req, timeout=self._timeout) as resp:  # noqa: S310
                data = json.loads(resp.read().decode())
        except Exception:
            logger.exception("DuckDuckGo search failed")
            return {
                "status": "error",
                "results": [],
                "request_id": request_id,
                "provider": "duckduckgo",
                "timestamp": timestamp,
            }

        results: list[dict] = []
        for item in data.get("RelatedTopics", []):
            if "FirstURL" not in item or "Text" not in item:
                continue
            text: str = item["Text"]
            results.append({
                "url": item["FirstURL"],
                "title": text[:_TITLE_MAX_CHARS],
                "excerpt": text[:_EXCERPT_MAX_CHARS],
            })
            if len(results) >= max_results:
                break

        return {
            "status": "success",
            "results": results,
            "request_id": request_id,
            "provider": "duckduckgo",
            "timestamp": timestamp,
        }
