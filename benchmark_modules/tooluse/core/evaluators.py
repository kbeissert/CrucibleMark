"""
ToolUse Module — Evaluators (v1.0)
Zwei-Phasen-Scoring: Phase 1 (Tool Execution) + Phase 2 (Synthesis Quality).

Architektur-Invariante:
  - Keine LLM-Calls, keine MCP-Calls, keine Netzaufrufe.
  - Bewertet ausschließlich bereits vorhandene Daten:
      tool_transcript (MCP-Server-Response), model_output (Modellantwort), asset (YAML)
  - Alle Schwellenwerte kommen aus config — keine Magic Numbers.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, Optional

from utils.similarity import SemanticSimilarity

from .constants import (
    AUDIT_HALLUCINATION_FAIL,
    AUDIT_SANDBOX_VIOLATION,
    FIELD_COMBINED_SCORE,
    FIELD_P1_SCORE,
    FIELD_P2_SCORE,
    KEYWORD_THRESHOLD_KEY,
    PHASE1_WEIGHT_KEY,
    PHASE2_WEIGHT_KEY,
    SEMANTIC_THRESHOLD_KEY,
    TOOL_HTTP_FETCH,
    TOOL_WEB_SEARCH,
)

logger = logging.getLogger(__name__)

# Regex for detecting list items (-, •, 1. 2. 3. style)
_LIST_ITEM_RE = re.compile(
    r"^(?:[-•*]|\d+[.)])\s+\S",
    re.MULTILINE,
)


class ToolUseEvaluator:
    """
    Scores tool transcripts and model outputs across two phases.

    Phase 1 — Tool Execution: did the model actually call the right tool correctly?
    Phase 2 — Synthesis Quality: is the produced text accurate, sourced, and complete?
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        """
        config = content of config.yaml['config'] section.
        All thresholds are read from here via constants.py key names.
        """
        self.config = config

    # ------------------------------------------------------------------
    # Phase 1: Tool Execution Scoring
    # ------------------------------------------------------------------

    def score_phase1(
        self,
        tool_transcript: Dict[str, Any],
        asset: Dict[str, Any],
    ) -> float:
        """Score the MCP tool call. Returns 0–100."""
        # Hard fail: sandbox/whitelist violation
        if tool_transcript.get("status") == "blocked":
            logger.debug("Phase 1: sandbox violation — hard fail")
            return 0.0

        evaluation = asset.get("evaluation", {})
        phase1 = evaluation.get("phase1", {})
        expected_tool = phase1.get("expected_tool", "")
        is_failure_test = asset.get("is_failure_test", False)

        # Cascade fail for failure tests where the tool unexpectedly succeeded
        if is_failure_test and tool_transcript.get("status") == "success":
            logger.debug("Phase 1: failure test not triggered (unexpected success) — hard fail")
            return 0.0

        score = 0.0

        # 1. Correct tool type called? (40 pts)
        actual_tool = tool_transcript.get("tool_type_called", "")
        if actual_tool == expected_tool:
            score += 40.0

        # 2. Call result as expected? (40 pts)
        if expected_tool == TOOL_WEB_SEARCH:
            results = tool_transcript.get("results") or []
            if len(results) >= 1:
                score += 40.0
        elif expected_tool == TOOL_HTTP_FETCH:
            status_code = tool_transcript.get("status_code")
            if is_failure_test:
                if (
                    tool_transcript.get("status") == "error"
                    and status_code == 404
                ):
                    score += 40.0
            else:
                expected_code = phase1.get("expected_status_code", 200)
                if status_code == expected_code:
                    score += 40.0

        # 3. Relevant source domain identified? (20 pts — web_search only)
        # http_fetch: domain criterion not applicable — no pts added (not neutral)
        if expected_tool == TOOL_WEB_SEARCH:
            golden_domains = phase1.get("golden_source_domains", [])
            if golden_domains:
                results = tool_transcript.get("results") or []
                urls = [r.get("url", "") for r in results if isinstance(r, dict)]
                hit = any(
                    any(domain in url for domain in golden_domains)
                    for url in urls
                )
                if hit:
                    score += 20.0
            else:
                # No golden domains configured → neutral (20 pts)
                score += 20.0

        return min(score, 100.0)

    # ------------------------------------------------------------------
    # Phase 2: Synthesis Quality Scoring
    # ------------------------------------------------------------------

    def score_phase2(
        self,
        model_output: str,
        tool_transcript: Dict[str, Any],
        asset: Dict[str, Any],
    ) -> float:
        """Score the model's generated text. Returns 0–100."""
        is_failure_test = asset.get("is_failure_test", False)
        evaluation = asset.get("evaluation", {})
        phase2 = evaluation.get("phase2", {})

        # 1. Hallucination hard-fail (only for failure tests)
        if is_failure_test:
            forbidden_patterns = asset.get("forbidden_patterns", [])
            output_lower = model_output.lower()
            for pattern in forbidden_patterns:
                if pattern.lower() in output_lower:
                    logger.debug("Phase 2: hallucination hard fail — pattern '%s'", pattern)
                    return 0.0

        score = 0.0

        # 2. Keyword score (30 pts)
        keywords: list = phase2.get("keywords", [])
        keyword_score = 0.0
        if keywords:
            output_lower = model_output.lower()
            found = sum(1 for kw in keywords if str(kw).lower() in output_lower)
            ratio = found / len(keywords)
            threshold = self.config.get(KEYWORD_THRESHOLD_KEY, 0.4)
            if ratio >= threshold:
                keyword_score = ratio * 30.0
            # Below threshold → 0 pts for this component
        else:
            keyword_score = 30.0  # no keywords defined → neutral
        score += keyword_score

        # 3. Semantic score (50 pts)
        golden_answer: str = phase2.get("golden_answer", "")
        semantic_score = 0.0
        if golden_answer and model_output.strip():
            similarity = SemanticSimilarity.calculate_similarity(
                model_output, golden_answer
            )
            semantic_threshold = self.config.get(SEMANTIC_THRESHOLD_KEY, 0.72)
            if similarity >= semantic_threshold:
                semantic_score = similarity * 50.0
            else:
                # Below threshold: half value (no hard zero)
                semantic_score = similarity * 25.0
        else:
            semantic_score = 50.0  # no golden answer → neutral
        score += semantic_score

        # 4. Structural requirements (20 pts)
        requires_url = phase2.get("requires_url_citation", False)
        requires_structured = phase2.get("requires_structured_output", False)

        if requires_url or requires_structured:
            structural_score = 0.0
            if requires_url:
                if "http" in model_output.lower():
                    structural_score += 10.0
            else:
                structural_score += 10.0  # not required → neutral

            if requires_structured:
                list_items = _LIST_ITEM_RE.findall(model_output)
                if len(list_items) >= 3:
                    structural_score += 10.0
            else:
                structural_score += 10.0  # not required → neutral
        else:
            # Neither declared → neutral 20 pts
            structural_score = 20.0

        score += structural_score

        # 5. min_length penalty (20% penalty on total after all other scoring)
        min_length = phase2.get("min_length", 0)
        word_count = len(model_output.split())
        if min_length and word_count < min_length:
            score *= 0.80

        return min(round(score, 2), 100.0)

    # ------------------------------------------------------------------
    # Combined Score
    # ------------------------------------------------------------------

    def combined_score(self, p1: float, p2: float) -> float:
        w1 = self.config.get(PHASE1_WEIGHT_KEY, 0.5)
        w2 = self.config.get(PHASE2_WEIGHT_KEY, 0.5)
        return round(p1 * w1 + p2 * w2, 2)

    # ------------------------------------------------------------------
    # Audit Block
    # ------------------------------------------------------------------

    def build_audit_block(
        self,
        p1: float,
        p2: float,
        combined: float,
        tool_transcript: Dict[str, Any],
        asset: Dict[str, Any],
    ) -> str:
        """Build a CrucibleMark-format audit log block."""
        evaluation = asset.get("evaluation", {})
        phase1 = evaluation.get("phase1", {})
        phase2 = evaluation.get("phase2", {})
        is_failure_test = asset.get("is_failure_test", False)

        tool_type = phase1.get("expected_tool", "unknown")
        status = tool_transcript.get("status", "unknown")
        status_code = tool_transcript.get("status_code")
        source_url = tool_transcript.get("source_url") or _first_result_url(tool_transcript)
        provider = tool_transcript.get("provider", "unknown")
        request_id = tool_transcript.get("request_id", "n/a")
        timestamp = tool_transcript.get("timestamp", "n/a")

        # Build excerpt (first 200 chars of content_excerpt or first result excerpt)
        raw_excerpt = _get_excerpt(tool_transcript)

        lines = [
            "--- TOOL USE TRANSCRIPT ---",
            f"Tool Type:      {tool_type}",
            f"Status:         {status}",
            f"Status Code:    {status_code if status_code is not None else 'null'}",
            f"Source URL:     {source_url or 'n/a'}",
            f"Raw Excerpt:    {raw_excerpt}",
            f"Provider:       {provider}",
            f"Request ID:     {request_id}",
            f"Timestamp:      {timestamp}",
            "",
            f"Phase 1 Score:  {p1} / 100",
            f"Phase 2 Score:  {p2} / 100",
            f"Combined Score: {combined} / 100",
        ]

        # Optional warning blocks
        if tool_transcript.get("status") == "blocked":
            lines += [
                "",
                AUDIT_SANDBOX_VIOLATION,
                "Tool call blocked by whitelist policy.",
                "Phase 1 Score overridden to 0.",
            ]

        if is_failure_test and p2 == 0.0:
            forbidden_patterns = asset.get("forbidden_patterns", [])
            output_lower = ""  # caller may inject model_output if needed; default safe
            triggered = _find_triggered_pattern(output_lower, forbidden_patterns)
            lines += [
                "",
                AUDIT_HALLUCINATION_FAIL,
                f'Pattern matched: "{triggered}"',
                "Phase 2 Score overridden to 0.",
            ]

        lines.append("--- END TOOL USE TRANSCRIPT ---")
        return "\n".join(lines)

    def build_audit_block_with_output(
        self,
        p1: float,
        p2: float,
        combined: float,
        tool_transcript: Dict[str, Any],
        asset: Dict[str, Any],
        model_output: str = "",
    ) -> str:
        """Variant that accepts model_output for accurate hallucination pattern reporting."""
        evaluation = asset.get("evaluation", {})
        phase1 = evaluation.get("phase1", {})
        is_failure_test = asset.get("is_failure_test", False)

        tool_type = phase1.get("expected_tool", "unknown")
        status = tool_transcript.get("status", "unknown")
        status_code = tool_transcript.get("status_code")
        source_url = tool_transcript.get("source_url") or _first_result_url(tool_transcript)
        provider = tool_transcript.get("provider", "unknown")
        request_id = tool_transcript.get("request_id", "n/a")
        timestamp = tool_transcript.get("timestamp", "n/a")
        raw_excerpt = _get_excerpt(tool_transcript)

        lines = [
            "--- TOOL USE TRANSCRIPT ---",
            f"Tool Type:      {tool_type}",
            f"Status:         {status}",
            f"Status Code:    {status_code if status_code is not None else 'null'}",
            f"Source URL:     {source_url or 'n/a'}",
            f"Raw Excerpt:    {raw_excerpt}",
            f"Provider:       {provider}",
            f"Request ID:     {request_id}",
            f"Timestamp:      {timestamp}",
            "",
            f"Phase 1 Score:  {p1} / 100",
            f"Phase 2 Score:  {p2} / 100",
            f"Combined Score: {combined} / 100",
        ]

        if tool_transcript.get("status") == "blocked":
            lines += [
                "",
                AUDIT_SANDBOX_VIOLATION,
                "Tool call blocked by whitelist policy.",
                "Phase 1 Score overridden to 0.",
            ]

        if is_failure_test and p2 == 0.0 and model_output:
            forbidden_patterns = asset.get("forbidden_patterns", [])
            triggered = _find_triggered_pattern(model_output.lower(), forbidden_patterns)
            lines += [
                "",
                AUDIT_HALLUCINATION_FAIL,
                f'Pattern matched: "{triggered}"',
                "Phase 2 Score overridden to 0.",
            ]

        lines.append("--- END TOOL USE TRANSCRIPT ---")
        return "\n".join(lines)


# ------------------------------------------------------------------
# Private helpers (module-level, not part of public API)
# ------------------------------------------------------------------

def _first_result_url(transcript: Dict[str, Any]) -> Optional[str]:
    results = transcript.get("results") or []
    if results and isinstance(results[0], dict):
        return results[0].get("url")
    return None


def _get_excerpt(transcript: Dict[str, Any]) -> str:
    raw = transcript.get("content_excerpt")
    if raw:
        return str(raw)[:200]
    results = transcript.get("results") or []
    if results and isinstance(results[0], dict):
        excerpt = results[0].get("excerpt") or results[0].get("content", "")
        return str(excerpt)[:200]
    return "n/a"


def _find_triggered_pattern(text_lower: str, patterns: list) -> str:
    for pattern in patterns:
        if pattern.lower() in text_lower:
            return pattern
    return "unknown"
