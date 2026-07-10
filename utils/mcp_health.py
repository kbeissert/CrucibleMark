"""
MCP Server Health Check Utility — CrucibleMark
Wiederverwendbar für alle Module mit requires_mcp: true.
"""

import json
import urllib.request
import urllib.error


def check_mcp_health(health_url: str, timeout: int = 3) -> dict:
    """
    Gibt {"status": "ok", "mode": "mock"|"live"} zurück
    oder {"status": "unavailable", "error": "..."} bei Fehler.
    Wirft keine Exceptions.
    """
    try:
        req = urllib.request.Request(health_url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            data = json.loads(body)
            return {
                "status": "ok",
                "mode": data.get("mode", "unknown"),
                "raw": data,
            }
    except urllib.error.URLError as exc:
        return {"status": "unavailable", "error": str(exc.reason)}
    except OSError as exc:
        return {"status": "unavailable", "error": str(exc)}
    except Exception as exc:  # pylint: disable=broad-exception-caught
        return {"status": "unavailable", "error": str(exc)}


def mcp_base_url(health_url: str) -> str:
    """Derives the MCP base URL from the health endpoint URL."""
    # "http://localhost:8765/health" → "http://localhost:8765"
    from urllib.parse import urlparse
    parsed = urlparse(health_url)
    return f"{parsed.scheme}://{parsed.netloc}"
