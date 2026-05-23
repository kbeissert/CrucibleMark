"""
ToolUse Pipeline Diagnostics — Instrument MCP/Parser/Search quality.

Drei Szenarien zur Fehlerquelle-Trennung:
1. MCP-Flow (normal): Full pipeline mit Tavily + MCP
2. Reference-Output (kuratiert): Hartcodierter, bekannt guter Tool-Output
3. Stub-Flow (direct): Minimal tool response matching expected structure

Vergleich zeigt ob Fehler in Pipeline oder Modell sitzt.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class ToolOutputMetrics:
    """Metrics für Tool-Output-Qualität."""
    total_bytes: int
    snippet_count: int
    avg_snippet_len: float
    result_count: int
    has_urls: bool
    excerpt_quality: str  # "full", "partial", "minimal", "empty"


@dataclass
class ParseMetrics:
    """Metrics für JSON-Parse-Prozess."""
    parse_attempts: int
    parse_success: bool
    first_attempt_success: bool
    raw_length: int
    cleaned_length: int
    contains_tool_call: bool
    json_error: Optional[str]


@dataclass
class PipelineDiagnostic:
    """Gesamte Diagnose für einen Benchmark-Run."""
    asset_id: str
    model_id: str
    scenario: str  # "mcp_flow", "reference_output", "stub_direct"
    tool_call_valid: bool
    output_metrics: ToolOutputMetrics
    parse_metrics: ParseMetrics
    p1_score: float
    p2_score: float
    combined_score: float
    is_expected: bool  # Predicted outcome based on metrics


class PipelineDiagnostician:
    """Diagnostiziert ob Fehler in Pipeline oder Modell."""

    @staticmethod
    def measure_tool_output(tool_transcript: Dict[str, Any]) -> ToolOutputMetrics:
        """Quantifiziere Tool-Output-Qualität."""
        results = tool_transcript.get("results") or []
        result_count = len(results)

        total_bytes = 0
        snippets = []

        for r in results:
            if isinstance(r, dict):
                excerpt = r.get("excerpt") or r.get("content", "")
                if excerpt:
                    total_bytes += len(str(excerpt))
                    snippets.append(str(excerpt))

        content_excerpt = tool_transcript.get("content_excerpt")
        if content_excerpt:
            total_bytes += len(str(content_excerpt))

        snippet_count = len(snippets)
        avg_snippet_len = (
            sum(len(s) for s in snippets) / snippet_count if snippet_count > 0 else 0
        )

        has_urls = any(
            r.get("url") for r in results if isinstance(r, dict)
        )

        if total_bytes > 500:
            excerpt_quality = "full"
        elif total_bytes > 200:
            excerpt_quality = "partial"
        elif total_bytes > 50:
            excerpt_quality = "minimal"
        else:
            excerpt_quality = "empty"

        return ToolOutputMetrics(
            total_bytes=total_bytes,
            snippet_count=snippet_count,
            avg_snippet_len=avg_snippet_len,
            result_count=result_count,
            has_urls=has_urls,
            excerpt_quality=excerpt_quality,
        )

    @staticmethod
    def measure_parse(
        raw_response: str,
        cleaned_response: str,
        parse_success: bool,
        parse_attempts: int,
        json_error: Optional[str] = None,
    ) -> ParseMetrics:
        """Quantifiziere JSON-Parse-Qualität."""
        return ParseMetrics(
            parse_attempts=parse_attempts,
            parse_success=parse_success,
            first_attempt_success=parse_attempts == 1,
            raw_length=len(raw_response),
            cleaned_length=len(cleaned_response),
            contains_tool_call="tool_call" in cleaned_response.lower(),
            json_error=json_error,
        )

    @staticmethod
    def build_diagnostic(
        asset_id: str,
        model_id: str,
        scenario: str,
        tool_call_valid: bool,
        tool_transcript: Dict[str, Any],
        raw_response: str,
        cleaned_response: str,
        parse_attempts: int,
        p1_score: float,
        p2_score: float,
        combined_score: float,
        json_error: Optional[str] = None,
    ) -> PipelineDiagnostic:
        """Baue vollständige Pipeline-Diagnose."""
        output_metrics = PipelineDiagnostician.measure_tool_output(tool_transcript)
        parse_metrics = PipelineDiagnostician.measure_parse(
            raw_response,
            cleaned_response,
            parse_success=tool_call_valid,
            parse_attempts=parse_attempts,
            json_error=json_error,
        )

        # Predict if scores are expected based on metrics
        is_expected = (
            output_metrics.excerpt_quality != "empty"
            and parse_metrics.first_attempt_success
            and p1_score >= 40.0
        )

        return PipelineDiagnostic(
            asset_id=asset_id,
            model_id=model_id,
            scenario=scenario,
            tool_call_valid=tool_call_valid,
            output_metrics=output_metrics,
            parse_metrics=parse_metrics,
            p1_score=p1_score,
            p2_score=p2_score,
            combined_score=combined_score,
            is_expected=is_expected,
        )

    @staticmethod
    def log_diagnostic(diag: PipelineDiagnostic) -> None:
        """Log diagnostic to stdout and file."""
        msg = (
            f"[DIAGNOSTIC] {diag.model_id} — {diag.scenario} → "
            f"tool_valid={diag.tool_call_valid}, "
            f"excerpt_quality={diag.output_metrics.excerpt_quality}, "
            f"parse_attempts={diag.parse_metrics.parse_attempts}, "
            f"p1={diag.p1_score:.1f}, expected={diag.is_expected}"
        )
        logger.info(msg)
        return msg

    @staticmethod
    def to_json(diag: PipelineDiagnostic) -> str:
        """Serialize to JSON for logging."""
        return json.dumps(asdict(diag), ensure_ascii=False, indent=2)
