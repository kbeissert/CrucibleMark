from __future__ import annotations

from datetime import datetime, UTC
from html.parser import HTMLParser
from pathlib import Path
import platform
import re
from urllib.parse import quote_plus, unquote
from urllib.request import Request, urlopen

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("local-web-research")
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
}


class _VisibleTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self._chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            text = data.strip()
            if text:
                self._chunks.append(text)

    def text(self) -> str:
        joined = "\n".join(self._chunks)
        return re.sub(r"\n{2,}", "\n\n", joined).strip()


def _http_get(url: str, timeout: float = 15.0) -> str:
    req = Request(url=url, headers=DEFAULT_HEADERS)
    with urlopen(req, timeout=timeout) as response:
        encoding = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(encoding, errors="replace")


def _strip_html(html: str) -> str:
    parser = _VisibleTextExtractor()
    parser.feed(html)
    return parser.text()


def _normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _is_allowed_url(url: str) -> bool:
    return url.startswith("https://") or url.startswith("http://")


@mcp.tool()
def ping(message: str = "pong") -> str:
    """Simple health check for MCP connectivity."""
    return f"MCP alive: {message}"


@mcp.tool()
def now_iso() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(UTC).isoformat()


@mcp.tool()
def system_info() -> dict[str, str]:
    """Return basic local machine and workspace information."""
    return {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "hostname": platform.node(),
        "workspace_root": str(WORKSPACE_ROOT),
    }


@mcp.tool()
def list_workspace_entries(limit: int = 30) -> list[str]:
    """List top-level files and folders from the workspace root."""
    safe_limit = max(1, min(limit, 200))
    entries = sorted(p.name for p in WORKSPACE_ROOT.iterdir())
    return entries[:safe_limit]


@mcp.tool()
def web_search(query: str, max_results: int = 5) -> list[dict[str, str]]:
    """Search the public web via DuckDuckGo HTML results (no API key required)."""
    cleaned_query = _normalize_whitespace(query)
    if not cleaned_query:
        return [{"error": "query must not be empty"}]

    safe_limit = max(1, min(max_results, 10))
    search_url = f"https://duckduckgo.com/html/?q={quote_plus(cleaned_query)}"

    try:
        html = _http_get(search_url)
    except Exception as exc:  # noqa: BLE001
        return [{"error": f"search request failed: {exc}"}]

    pattern = re.compile(
        r'<a[^>]+class="result__a"[^>]+href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>',
        re.IGNORECASE | re.DOTALL,
    )

    results: list[dict[str, str]] = []
    for match in pattern.finditer(html):
        raw_href = match.group("href")
        title_html = match.group("title")

        href = unquote(raw_href)
        redirect_match = re.search(r"uddg=([^&]+)", href)
        if redirect_match:
            href = unquote(redirect_match.group(1))

        if not _is_allowed_url(href):
            continue

        title = _normalize_whitespace(re.sub(r"<[^>]+>", "", title_html))
        if not title:
            title = href

        results.append({"title": title, "url": href})
        if len(results) >= safe_limit:
            break

    if not results:
        return [{"error": "no results parsed from search response"}]

    return results


@mcp.tool()
def fetch_url(url: str, max_chars: int = 12000) -> dict[str, str]:
    """Fetch and return readable text content from a web page URL."""
    if not _is_allowed_url(url):
        return {"error": "url must start with http:// or https://"}

    safe_limit = max(500, min(max_chars, 60000))
    try:
        html = _http_get(url)
        text = _strip_html(html)
    except Exception as exc:  # noqa: BLE001
        return {"error": f"fetch failed: {exc}", "url": url}

    if not text:
        return {
            "url": url,
            "content": "",
            "note": "No visible text content extracted from page.",
        }

    trimmed = text[:safe_limit]
    return {
        "url": url,
        "content": trimmed,
        "truncated": "true" if len(text) > safe_limit else "false",
    }


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
