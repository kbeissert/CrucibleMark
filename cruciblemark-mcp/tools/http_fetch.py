"""HTTP fetch tool — whitelist-enforced URL retrieval with mock and live modes."""

import json
import logging
from datetime import datetime, timezone
from urllib import error as urllib_error
from urllib import request as urllib_request
from urllib.parse import urlparse

from tools.mock_provider import mock_http_fetch, new_request_id

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class HttpFetchTool:
    def __init__(self, config: dict, mode: str) -> None:
        cfg = config["http_fetch"]
        self._mode = mode
        self._timeout: int = cfg["timeout_seconds"]
        self._default_max_chars: int = cfg["max_chars"]
        self._whitelist: list[str] = cfg.get("whitelist", [])

    def _is_whitelisted(self, url: str) -> bool:
        host = urlparse(url).hostname or ""
        return any(host == domain or host.endswith(f".{domain}") for domain in self._whitelist)

    def fetch(self, url: str, max_chars: int) -> dict:
        request_id = new_request_id()
        timestamp = _now()

        if not self._is_whitelisted(url):
            result: dict = {
                "status": "blocked",
                "status_code": None,
                "content_excerpt": None,
                "source_url": url,
                "request_id": request_id,
                "timestamp": timestamp,
            }
            logger.info(
                json.dumps({
                    "request_id": request_id,
                    "timestamp": timestamp,
                    "tool_type": "http_fetch",
                    "status": "blocked",
                    "url": url,
                })
            )
            return result

        if self._mode == "mock":
            result = mock_http_fetch(url, max_chars)
            result["request_id"] = request_id
            result["timestamp"] = timestamp
        else:
            result = self._live_fetch(url, max_chars, request_id, timestamp)

        logger.info(
            json.dumps({
                "request_id": request_id,
                "timestamp": timestamp,
                "tool_type": "http_fetch",
                "status": result["status"],
                "status_code": result.get("status_code"),
                "url": url,
            })
        )
        return result

    def _live_fetch(self, url: str, max_chars: int, request_id: str, timestamp: str) -> dict:
        req = urllib_request.Request(url, headers={"User-Agent": "CrucibleMark/1.0"})
        try:
            with urllib_request.urlopen(req, timeout=self._timeout) as resp:
                content = resp.read().decode("utf-8", errors="replace")[:max_chars]
                return {
                    "status": "success",
                    "status_code": resp.status,
                    "content_excerpt": content,
                    "source_url": url,
                    "request_id": request_id,
                    "timestamp": timestamp,
                }
        except urllib_error.HTTPError as exc:
            return {
                "status": "error",
                "status_code": exc.code,
                "content_excerpt": None,
                "source_url": url,
                "request_id": request_id,
                "timestamp": timestamp,
            }
        except Exception as exc:
            logger.error("http_fetch live request failed: %s", exc)
            return {
                "status": "error",
                "status_code": None,
                "content_excerpt": None,
                "source_url": url,
                "request_id": request_id,
                "timestamp": timestamp,
            }
