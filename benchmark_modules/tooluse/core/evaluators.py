"""ToolUse Module — Evaluators (v1.0)
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
from typing import Any

from utils.similarity import SemanticSimilarity

from .constants import (
    AUDIT_HALLUCINATION_FAIL,
    AUDIT_SANDBOX_VIOLATION,
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
    """Scores tool transcripts and model outputs across two phases.

    Phase 1 — Tool Execution: did the model actually call the right tool correctly?
    Phase 2 — Synthesis Quality: is the produced text accurate, sourced, and complete?
    """

    def __init__(self, config: dict[str, Any]) -> None:
        """config = content of config.yaml['config'] section.
        All thresholds are read from here via constants.py key names.
        """
        self.config = config

    # ------------------------------------------------------------------
    # Phase 1: Tool Execution Scoring
    # ------------------------------------------------------------------

    def score_phase1(
        self,
        tool_transcript: dict[str, Any],
        asset: dict[str, Any],
        excerpt_quality: str = "empty",
        parse_attempts: int = 1,
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
            call_status = tool_transcript.get("status", "")
            if len(results) >= 1:
                score += 40.0
            elif call_status == "success":
                # Empty result set despite a successful MCP call: the search
                # backend returned nothing (infrastructure issue, not model
                # fault). Award call-execution points so the model is not
                # penalised for an external API edge case.
                score += 40.0
                logger.debug("Phase 1: web_search status=success but result_count=0 — empty_result state, awarding call-execution pts")
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

        # 3. Source quality (20 pts)
        # web_search: relevant domain in results
        # http_fetch (success): excerpt_quality signal (full=20, partial=12, minimal=6, empty=0)
        # http_fetch (failure): not applicable — no pts added
        if expected_tool == TOOL_WEB_SEARCH:
            results = tool_transcript.get("results") or []
            if len(results) >= 2:
                score += 20.0
            elif len(results) >= 1:
                score += 10.0
            # 0 results → 0 pts
        elif expected_tool == TOOL_HTTP_FETCH and not is_failure_test:
            _quality_map = {"full": 20, "partial": 12, "minimal": 6, "empty": 0}
            score += _quality_map.get(excerpt_quality, 0)

        # 4. parse_attempts penalty
        retry_penalty = float(self.config.get("parse_retry_penalty", 5))
        if parse_attempts >= 2:
            score = max(score - retry_penalty, 0.0)
            logger.debug("Phase 1: parse_attempts=%d → -%.1f penalty", parse_attempts, retry_penalty)

        return min(score, 100.0)

    # ------------------------------------------------------------------
    # Phase 2: Synthesis Quality Scoring
    # ------------------------------------------------------------------

    def score_phase2(
        self,
        model_output: str,
        tool_transcript: dict[str, Any],
        asset: dict[str, Any],
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

        # Per-asset weights from phase2_rubric.weights; fallback to config defaults
        rubric_weights = evaluation.get("phase2_rubric", {}).get("weights", {})
        _default_fact = self.config.get("p2_weight_factuality", 0.50)
        _default_hall = self.config.get("p2_weight_hallucination_risk", 0.30)
        _default_uncert = self.config.get("p2_weight_uncertainty_handling", 0.20)

        # factuality → semantic component
        w_fact = float(rubric_weights.get("factuality", _default_fact))
        # hallucination_risk → keyword component
        w_hall = float(rubric_weights.get("hallucination_risk", _default_hall))
        # uncertainty_handling / url_precision / language_consistency → structural component
        # sum all remaining (non-factuality, non-hallucination_risk) dimensions
        w_struct = sum(
            float(v) for k, v in rubric_weights.items()
            if k not in ("factuality", "hallucination_risk")
        ) if rubric_weights else _default_uncert

        total_w = w_fact + w_hall + w_struct
        if total_w <= 0.0:
            total_w = 1.0

        # 2. Keyword score (0–100 raw, scaled by w_hall)
        keywords: list = phase2.get("keywords", [])
        keyword_raw = 0.0
        if keywords:
            output_lower = model_output.lower()
            found = sum(1 for kw in keywords if str(kw).lower() in output_lower)
            ratio = found / len(keywords)
            threshold = self.config.get(KEYWORD_THRESHOLD_KEY, 0.4)
            if ratio >= threshold:
                keyword_raw = ratio * 100.0
            # Below threshold → 0
        else:
            keyword_raw = 100.0  # no keywords defined → neutral

        # 3. Semantic score (0–100 raw, scaled by w_fact)
        golden_answer: str = phase2.get("golden_answer", "")
        semantic_raw = 0.0
        if golden_answer and model_output.strip():
            similarity = SemanticSimilarity.calculate_similarity(
                model_output, golden_answer,
            )
            semantic_threshold = self.config.get(SEMANTIC_THRESHOLD_KEY, 0.72)
            if similarity >= semantic_threshold:
                semantic_raw = similarity * 100.0
            else:
                # Below threshold: half value (no hard zero)
                semantic_raw = similarity * 50.0
        else:
            semantic_raw = 100.0  # no golden answer → neutral

        # 4. Structural requirements (0–100 raw, scaled by w_struct)
        requires_url = phase2.get("requires_url_citation", False)
        requires_structured = phase2.get("requires_structured_output", False)

        if requires_url or requires_structured:
            structural_raw = 0.0
            if requires_url:
                if "http" in model_output.lower():
                    structural_raw += 50.0
            else:
                structural_raw += 50.0  # not required → neutral

            if requires_structured:
                list_items = _LIST_ITEM_RE.findall(model_output)
                if len(list_items) >= 3:
                    structural_raw += 50.0
            else:
                structural_raw += 50.0  # not required → neutral
        else:
            structural_raw = 100.0  # neither declared → neutral

        # Weighted combination (normalized)
        score = (
            semantic_raw * w_fact
            + keyword_raw * w_hall
            + structural_raw * w_struct
        ) / total_w

        # 5. min_length penalty (20% penalty on total after all other scoring)
        min_length = phase2.get("min_length", 0)
        word_count = len(model_output.split())
        if min_length and word_count < min_length:
            score *= 0.80

        return min(round(score, 2), 100.0)

    # ------------------------------------------------------------------
    # Combined Score
    # ------------------------------------------------------------------

    def combined_score(
        self,
        p1: float,
        p2: float,
        tool_call_valid: bool = True,
        asset_id: str = "",
        benchmarks_config: list[dict[str, Any]] | None = None,
    ) -> float:
        """Berechnet Combined Score mit Safety-Guardrail für Phase 1 Fehler.

        Schwellenmodell:
        - tool_call_valid=False oder p1=0: hard cap at 60 (Tool komplett fehlgeschlagen)
        - p1 < 40: -10 Malus (Tool aufgerufen, aber Status/Domain falsch)
        - p1 < 60: -3 Malus (Tool mäßig erfolgreich)
        - p1 >= 60: kein Malus

        Args:
            p1: Phase 1 Score (Tool Execution, 0-100)
            p2: Phase 2 Score (Synthesis Quality, 0-100)
            tool_call_valid: Ob Tool erfolgreich aufgerufen wurde
            asset_id: Optional asset ID for per-asset weight lookup
            benchmarks_config: Optional list of benchmark dicts from config.yaml

        Returns:
            Combined Score mit angewandtem Guardrail (0-100)
        """
        global_w1 = self.config.get(PHASE1_WEIGHT_KEY, 0.4)
        global_w2 = self.config.get(PHASE2_WEIGHT_KEY, 0.6)

        # Per-asset override from config.yaml benchmarks section
        if asset_id and benchmarks_config:
            asset_cfg = next((b for b in benchmarks_config if b.get("id") == asset_id), {})
            w1 = float(asset_cfg.get("phase1_weight", global_w1))
            w2 = float(asset_cfg.get("phase2_weight", global_w2))
        else:
            w1, w2 = global_w1, global_w2

        base_combined = p1 * w1 + p2 * w2

        # Hard fail: Tool nicht aufgerufen oder komplett gescheitert
        if not tool_call_valid or p1 == 0.0:
            result = min(base_combined, 60.0)
            logger.debug(
                "combined_score: hard fail (tool_call_valid=%s, p1=%.1f) → %.2f",
                tool_call_valid, p1, result,
            )
            return round(result, 2)

        # Gestaffelte Malus für schwache Execution
        malus = 0.0
        if p1 < 40.0:
            malus = 10.0
            logger.debug("combined_score: p1=%.1f < 40 → -10 Malus", p1)
        elif p1 < 60.0:
            malus = 3.0
            logger.debug("combined_score: p1=%.1f < 60 → -3 Malus", p1)

        result = max(base_combined - malus, 0.0)
        return round(result, 2)

    # ------------------------------------------------------------------
    # Audit Block
    # ------------------------------------------------------------------

    def build_audit_block(
        self,
        p1: float,
        p2: float,
        combined: float,
        tool_transcript: dict[str, Any],
        asset: dict[str, Any],
    ) -> str:
        """Build a CrucibleMark-format audit log block."""
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
        tool_transcript: dict[str, Any],
        asset: dict[str, Any],
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

def _first_result_url(transcript: dict[str, Any]) -> str | None:
    results = transcript.get("results") or []
    if results and isinstance(results[0], dict):
        return results[0].get("url")
    return None


def _get_excerpt(transcript: dict[str, Any]) -> str:
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
