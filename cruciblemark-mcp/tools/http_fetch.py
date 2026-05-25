"""HTTP fetch tool — whitelist-enforced URL retrieval with mock and live modes."""

import json
import logging
import re
from datetime import datetime, timezone
from urllib import error as urllib_error
from urllib import request as urllib_request
from urllib.parse import urlparse

from tools.mock_provider import mock_http_fetch, new_request_id

logger = logging.getLogger(__name__)

try:
    import trafilatura
    _TRAFILATURA_AVAILABLE = True
except ImportError:
    _TRAFILATURA_AVAILABLE = False
    logger.warning("trafilatura not installed — falling back to regex HTML extraction")

# Maximum raw HTML bytes to read before passing to trafilatura (1 MB)
_RAW_FETCH_MAX_BYTES = 1_000_000

# Fallback: blocks containing no useful body text
_BLOCK_RE = re.compile(
    r"<(head|script|style|noscript|nav|footer|header|svg)[^>]*>.*?</\1>",
    re.DOTALL | re.IGNORECASE,
)

_HTML_ENTITY = {
    "&amp;": "&", "&lt;": "<", "&gt;": ">",
    "&nbsp;": " ", "&quot;": '"', "&#39;": "'",
}


def _extract_text(html: str, max_chars: int) -> str:
    """Extract readable plain text from HTML.

    Tries trafilatura first (handles Wikipedia, news, JS-heavy sites).
    Falls back to regex stripping if trafilatura returns nothing.
    """
    if _TRAFILATURA_AVAILABLE:
        extracted = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=True,
            no_fallback=False,
        )
        if extracted and len(extracted.strip()) >= 80:
            return extracted[:max_chars]

    # Fallback: strip block elements, then all tags
    text = _BLOCK_RE.sub(" ", html)
    text = re.sub(r"<[^>]+>", " ", text)
    for entity, replacement in _HTML_ENTITY.items():
        text = text.replace(entity, replacement)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class HttpFetchTool:
    """Fetches URL content with whitelist enforcement in mock or live mode."""

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
        """Fetch URL content, enforcing whitelist. Returns structured result dict."""
        request_id = new_request_id()
        timestamp = _now()

        if not self._is_whitelisted(url):
            error_text = f"Error: URL not allowed by policy — {url}"
            result: dict = {
                "status": "blocked",
                "status_code": None,
                "content_excerpt": None,
                "content": [{"type": "text", "text": error_text}],
                "isError": True,
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
                }),
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
            }),
        )
        return result

    def _live_fetch(self, url: str, max_chars: int, request_id: str, timestamp: str) -> dict:
        req = urllib_request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; CrucibleMark/1.0; +https://github.com/CrucibleMark)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            },
        )
        try:
            with urllib_request.urlopen(req, timeout=self._timeout) as resp:  # noqa: S310
                raw_html = resp.read(_RAW_FETCH_MAX_BYTES).decode("utf-8", errors="replace")
                clean_text = _extract_text(raw_html, max_chars)
                content_text = f"Contents of {url}:\n{clean_text}"
                return {
                    "status": "success",
                    "status_code": resp.status,
                    "content_excerpt": clean_text[:200] if clean_text else None,
                    "content": [{"type": "text", "text": content_text}],
                    "isError": False,
                    "source_url": url,
                    "request_id": request_id,
                    "timestamp": timestamp,
                }
        except urllib_error.HTTPError as exc:
            error_text = f"Error fetching {url}: HTTP {exc.code}"
            return {
                "status": "error",
                "status_code": exc.code,
                "content_excerpt": None,
                "content": [{"type": "text", "text": error_text}],
                "isError": True,
                "source_url": url,
                "request_id": request_id,
                "timestamp": timestamp,
            }
        except Exception as exc:
            logger.exception("http_fetch live request failed")
            error_text = f"Error fetching {url}: {exc}"
            return {
                "status": "error",
                "status_code": None,
                "content_excerpt": None,
                "content": [{"type": "text", "text": error_text}],
                "isError": True,
                "source_url": url,
                "request_id": request_id,
                "timestamp": timestamp,
            }
