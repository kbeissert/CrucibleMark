"""
Tool Adapter Audit — Diagnose Tool-Name und Call-Format Mismatches.

Problem bei tooluse002 & Claude Sonnet 4.6:
- Model returned: {"tool_call": {"name": "fetch", ...}}
- Expected: {"tool_call": {"name": "http_fetch", ...}}
- MCP routed to: /tools/fetch (wrong endpoint)
- Result: p1 = 0.0 (hard fail)

Diese Audit prüft:
1. Tool-Name Normalisierung (fetch → http_fetch)
2. Tool-Call-Format Validierung
3. MCP Endpoint Routing
4. Response Structure Mapping
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Authorized tool names in CrucibleMark
AUTHORIZED_TOOLS = {
    "web_search": ["web_search", "search", "websearch", "web-such-tool", "web_such_tool"],
    "http_fetch": ["http_fetch", "fetch", "http", "fetch_url", "get_url", "http_fetch_and_extract", "fetch_http", "http-fetch-tool", "http_fetch_tool"],
}

# Canonical tool names (what we expect)
CANONICAL_TOOLS = {
    "web_search": "web_search",
    "http_fetch": "http_fetch",
}


class ToolAdapterAudit:
    """Audit Tool-Adapter layer for name/format mismatches."""

    @staticmethod
    def normalize_tool_name(raw_name: str) -> Tuple[str, bool]:
        """
        Normalize raw tool name from model to canonical form.

        Returns: (canonical_name, is_anomaly)
        - is_anomaly = True if raw_name needed normalization
        """
        raw_lower = str(raw_name).lower().strip()

        for canonical, variants in AUTHORIZED_TOOLS.items():
            if raw_lower in variants:
                is_anomaly = raw_lower != canonical
                return canonical, is_anomaly

        # Unknown tool
        return raw_lower, True

    @staticmethod
    def validate_tool_call(tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize tool call structure.

        Returns audit dict with findings.
        """
        audit = {
            "raw_name": tool_call.get("name", "unknown"),
            "canonical_name": "unknown",
            "is_anomaly": False,
            "format_valid": False,
            "has_parameters": False,
            "error": None,
        }

        # Validate structure
        if not isinstance(tool_call, dict):
            audit["error"] = "tool_call is not a dict"
            return audit

        if "name" not in tool_call:
            audit["error"] = "tool_call missing 'name' field"
            return audit

        # Normalize name
        canonical, is_anomaly = ToolAdapterAudit.normalize_tool_name(
            tool_call.get("name")
        )
        audit["canonical_name"] = canonical
        audit["is_anomaly"] = is_anomaly

        # Validate parameters
        params = tool_call.get("parameters", {})
        audit["has_parameters"] = isinstance(params, dict) and len(params) > 0

        # Format valid if canonical name found and has parameters
        audit["format_valid"] = (
            canonical in CANONICAL_TOOLS.values()
            and audit["has_parameters"]
        )

        if is_anomaly:
            audit["warning"] = (
                f"Tool name normalized: '{tool_call.get('name')}' → '{canonical}'"
            )

        return audit

    @staticmethod
    def audit_mcp_routing(
        tool_name: str,
        tool_transcript: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Audit MCP routing layer.

        Checks if tool_transcript indicates routing anomalies.
        """
        audit = {
            "tool_name": tool_name,
            "mcp_endpoint": f"/tools/{tool_name}",
            "transcript_status": tool_transcript.get("status"),
            "has_error": tool_transcript.get("status") in ("error", "blocked"),
            "status_code": tool_transcript.get("status_code"),
            "anomalies": [],
        }

        # Check for routing anomalies
        if "source_url" in tool_transcript:
            source = tool_transcript.get("source_url")
            if source is None or source == "n/a":
                audit["anomalies"].append(
                    f"source_url missing (expected for successful {tool_name})"
                )

        if tool_transcript.get("status") == "error" and not tool_transcript.get(
            "error"
        ):
            audit["anomalies"].append(
                "error status but no error message in transcript"
            )

        # Check for empty results
        results = tool_transcript.get("results")
        if isinstance(results, list) and len(results) == 0:
            audit["anomalies"].append("results array is empty")

        return audit

    @staticmethod
    def diagnose_p1_zero_case(
        tool_call_dict: Optional[Dict[str, Any]],
        tool_transcript: Dict[str, Any],
        asset: Dict[str, Any],
        p1_score: float,
    ) -> Dict[str, Any]:
        """
        Diagnose why P1 = 0.0 occurred.

        Returns diagnostic findings.
        """
        diagnosis = {
            "p1_score": p1_score,
            "is_hard_fail": p1_score == 0.0,
            "likely_cause": "unknown",
            "audit_details": {},
        }

        if not diagnosis["is_hard_fail"]:
            return diagnosis

        # Audit tool call
        if tool_call_dict:
            tool_audit = ToolAdapterAudit.validate_tool_call(tool_call_dict)
            diagnosis["audit_details"]["tool_call"] = tool_audit

            if tool_audit["is_anomaly"]:
                diagnosis["likely_cause"] = "tool_name_normalization"

        # Audit MCP routing
        if "tool_type_called" in tool_transcript:
            tool_name = tool_transcript["tool_type_called"]
            routing_audit = ToolAdapterAudit.audit_mcp_routing(
                tool_name, tool_transcript
            )
            diagnosis["audit_details"]["mcp_routing"] = routing_audit

            if routing_audit["anomalies"]:
                if diagnosis["likely_cause"] == "unknown":
                    diagnosis["likely_cause"] = "mcp_routing_issue"

        # Check for sandbox violation
        if tool_transcript.get("status") == "blocked":
            diagnosis["likely_cause"] = "sandbox_violation"

        # Check expected tool type
        expected_tool = asset.get("evaluation", {}).get("phase1", {}).get("expected_tool")
        actual_tool = tool_transcript.get("tool_type_called")

        if expected_tool and actual_tool and expected_tool != actual_tool:
            diagnosis["audit_details"]["tool_mismatch"] = {
                "expected": expected_tool,
                "actual": actual_tool,
            }
            if diagnosis["likely_cause"] == "unknown":
                diagnosis["likely_cause"] = "tool_type_mismatch"

        return diagnosis

    @staticmethod
    def log_audit(audit: Dict[str, Any], context: str = "") -> None:
        """Log audit findings."""
        msg = f"[TOOL_ADAPTER_AUDIT] {context} — {json.dumps(audit, ensure_ascii=False)}"
        if audit.get("anomalies") or audit.get("is_anomaly"):
            logger.warning(msg)
        else:
            logger.debug(msg)
