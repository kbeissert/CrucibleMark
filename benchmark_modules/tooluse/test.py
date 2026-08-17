"""ToolUse Test Controller (v1.1)
==============================
Zwei-Schritt-Flow:
  execute()       → MCP-Call + Modell-Call → BenchmarkResult (kein Scoring)
  score_response() → ToolUseEvaluator aufrufen → BenchmarkResult mit Scores

Architektur-Invariante:
  execute()       enthält keine Scoring-Logik.
  score_response() enthält keine Netzaufrufe.
"""

from __future__ import annotations

import json
import logging
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from schemas.result import BenchmarkResult

try:
    from benchmark_modules.base_test import BaseTest
except ImportError:
    class BaseTest:  # type: ignore[no-redef]
        def __init__(self, asset_path: Path) -> None:
            self.asset_path = asset_path

from benchmark_modules.tooluse.core.constants import (
    AUDIT_MCP_UNAVAILABLE,
    FIELD_COMBINED_SCORE,
    FIELD_CONTENT_VERIFICATION,
    FIELD_HALLUCINATION_FLAG,
    FIELD_P1_SCORE,
    FIELD_P2_SCORE,
    FIELD_TOOL_CONTENT_STATE,
    TOOL_HTTP_FETCH,
    TOOL_WEB_SEARCH,
)
from benchmark_modules.tooluse.core.diagnostics import PipelineDiagnostician
from benchmark_modules.tooluse.core.evaluators import ToolUseEvaluator
from benchmark_modules.tooluse.core.io_manager import ToolUseIOManager
from benchmark_modules.tooluse.core.tool_adapter_audit import ToolAdapterAudit, _load_scoring_caps
from utils.mcp_health import check_mcp_health, mcp_base_url
from utils.module_registry import load_module_config
from utils.scoring.llm_judge.judge_config import LLMJudgeConfig
from utils.scoring.llm_judge.judge_runner import JudgeRunner
from utils.scoring.exceptions import JudgeUnavailableError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Judge rubric helper
# ---------------------------------------------------------------------------

# Rubric-Sektionen (key → Label) — Refactoring 2026-08-15 (Review):
# CC=13 → Sektions-Rendering in eigene Funktion ausgelagert, Output unverändert.
_RUBRIC_SECTIONS: tuple[tuple[str, str], ...] = (
    ("tool_usage", "Tool Usage"),
    ("factuality", "Factuality"),
    ("hallucination_risk", "Hallucination Risk"),
    ("uncertainty_handling", "Uncertainty Handling"),
    ("url_precision", "URL Precision"),
    ("language_consistency", "Language Consistency"),
    ("search_strategy", "Search Strategy"),
)


def _append_rubric_section(
    lines: list[str], rubric_key: str, section_label: str, section: dict[str, Any]
) -> None:
    """Rendert eine phase2_rubric-Sektion in Markdown-Zeilen."""
    # Language consistency: emit target language in the section header
    if rubric_key == "language_consistency" and section.get("target_language"):
        lang = section["target_language"].upper()
        lines.append(f"\n### {section_label} (Target Language: {lang})")
    else:
        # Header is implicit — emitted per sub-section below
        pass

    must_include = section.get("must_include") or []
    must_not_include = section.get("must_not_include") or []
    red_flags = section.get("red_flags") or []
    acceptable = section.get("acceptable_patterns") or section.get("acceptable") or []
    unacceptable = section.get("unacceptable") or []
    scoring_note = section.get("scoring_note") or ""

    if must_include:
        lines.append(f"\n### Must Include ({section_label})")
        lines.extend(f"- {item}" for item in must_include)
    if must_not_include:
        lines.append(f"\n### Must NOT Include ({section_label})")
        lines.extend(f"- {item}" for item in must_not_include)
    if red_flags:
        lines.append(f"\n### {section_label} Red Flags (trigger hallucination_detected: true)")
        lines.extend(f"- {flag}" for flag in red_flags)
    if acceptable:
        lines.append(f"\n### Acceptable Patterns ({section_label})")
        lines.extend(f"- {p}" for p in acceptable)
    if unacceptable:
        lines.append(f"\n### NOT Acceptable ({section_label})")
        lines.extend(f"- {item}" for item in unacceptable)
    if scoring_note:
        lines.append(f"\n> **{section_label} Note:** {scoring_note.strip()}")


def _build_rubric_override(phase2_rubric: dict[str, Any]) -> str | None:
    """Converts a phase2_rubric YAML dict into a structured rubric_override string.

    Returns None when the dict is empty or yields no content.
    The output replaces the generic scale rubric in the judge user prompt.
    Score-level definitions (1–5) remain in the judge system prompt and are
    not repeated here.
    """
    if not phase2_rubric:
        return None

    lines: list[str] = ["## Asset-Specific Evaluation Criteria"]

    weights = phase2_rubric.get("weights")
    if weights:
        lines.append("\n### Scoring Weights")
        for dim, w in weights.items():
            pct = round(float(w) * 100) if float(w) <= 1.0 else int(w)
            lines.append(f"- {dim.replace('_', ' ').title()}: {pct}%")

    for rubric_key, section_label in _RUBRIC_SECTIONS:
        section = phase2_rubric.get(rubric_key, {})
        if not section:
            continue
        _append_rubric_section(lines, rubric_key, section_label, section)

    result = "\n".join(lines)
    return result if len(result) > len("## Asset-Specific Evaluation Criteria") else None

# ---------------------------------------------------------------------------
# Tool schemas injected into the system prompt
# ---------------------------------------------------------------------------

TOOL_SCHEMA_WEB_SEARCH: dict[str, Any] = {
    "name": "web_search",
    "description": "Sucht im Web nach aktuellen Informationen.",
    "parameters": {
        "query": {
            "type": "string",
            "description": "Der Suchbegriff",
        },
        "max_results": {
            "type": "integer",
            "description": "Anzahl der Ergebnisse (max. 3)",
            "default": 3,
        },
    },
}

TOOL_SCHEMA_HTTP_FETCH: dict[str, Any] = {
    "name": "fetch",
    "description": "Lädt den Inhalt einer URL.",
    "parameters": {
        "url": {
            "type": "string",
            "description": "Die zu ladende URL",
        },
        "max_chars": {
            "type": "integer",
            "description": "Maximale Zeichenanzahl des Ergebnisses",
            "default": 3000,
        },
    },
}

_TOOL_SCHEMAS: dict[str, dict[str, Any]] = {
    TOOL_WEB_SEARCH: TOOL_SCHEMA_WEB_SEARCH,
    TOOL_HTTP_FETCH: TOOL_SCHEMA_HTTP_FETCH,
}

SYSTEM_PROMPT_TEMPLATE = (
    "Du bist ein präziser Assistent mit Zugang zu externen Tools.\n"
    "Verfügbares Tool:\n"
    "{tool_schema_json}\n\n"
    "Wenn du das Tool nutzen möchtest, antworte AUSSCHLIESSLICH mit diesem JSON-Format:\n"
    '{{"tool_call": {{"name": "<tool_name>", "parameters": {{<parameter>}}}}}}\n\n'
    "Sobald du ein Tool-Ergebnis erhältst, beantworte die Aufgabe auf Basis dieses Ergebnisses.\n"
    "Erfinde keine Inhalte die nicht aus dem Tool-Ergebnis stammen."
)

FOLLOWUP_PROMPT_TEMPLATE = (
    "Tool-Ergebnis ({tool_name}):\n"
    "{tool_content}\n\n"
    "{original_task}"
)

RETRY_PROMPT = (
    "Deine letzte Antwort enthielt keinen gültigen Tool-Call.\n"
    "Antworte AUSSCHLIESSLICH mit diesem JSON-Format — kein weiterer Text:\n"
    '{{"tool_call": {{"name": "<tool_name>", "parameters": {{...}}}}}}\n\n'
    "Aufgabe: {task_prompt}"
)

SYNTHESIS_SYSTEM_PROMPT = (
    "Du bist ein präziser Assistent.\n"
    "Beantworte die Aufgabe ausschließlich auf Basis des bereitgestellten Tool-Ergebnisses.\n"
    "Erfinde keine Inhalte die nicht aus dem Tool-Ergebnis stammen."
)


class ToolUseTest(BaseTest):
    """Controller für das tooluse Benchmark-Modul.
    Orchestriert: MCP-Health → Tool-Schema-Injection → Erster Modell-Call →
    MCP-Tool-Call → Zweiter Modell-Call (Synthese) → Scoring.
    """

    def __init__(self, asset_path: Path) -> None:
        super().__init__(asset_path)
        self.config = load_module_config(Path(__file__).parent)

    # ------------------------------------------------------------------
    # Public: execute  # noqa: ERA001
    # ------------------------------------------------------------------

    def execute(self, model: str, llm_client: Any, **kwargs: Any) -> BenchmarkResult:
        """MCP-Call + Modell-Call. Kein Scoring."""
        provider = kwargs.get("provider")

        # 1. MCP health check
        health_url: str = (
            self.config.get("execution", {}).get("mcp_health_url", "http://localhost:8765/health")
        )
        health = check_mcp_health(health_url)
        if health["status"] != "ok":
            return BenchmarkResult(
                status="error",
                raw_response="",
                data={
                    "error": "MCP server unavailable",
                    "audit_marker": AUDIT_MCP_UNAVAILABLE,
                    "health_detail": health.get("error", ""),
                },
            )

        # 2. Tool schema selection
        tool_available: str = self.asset.get("input", {}).get("tool_available", TOOL_WEB_SEARCH)
        schema = _TOOL_SCHEMAS.get(tool_available, TOOL_SCHEMA_WEB_SEARCH)
        task_prompt: str = self.asset.get("prompt", "")

        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            tool_schema_json=json.dumps(schema, ensure_ascii=False, indent=2),
        )

        # 3. First model call (with optional retry on parse failure)
        call1_start = time.time()
        response_1: str = llm_client.query(
            model=model,
            prompt=task_prompt,
            system=system_prompt,
            provider=provider,
            **{k: v for k, v in kwargs.items() if k != "provider"},
        ) or ""
        call1_tokens: int = getattr(llm_client, "last_token_usage", 0) or 0
        call1_cost: float = getattr(llm_client, "last_request_cost", 0.0) or 0.0
        call1_input_tokens: int = getattr(llm_client, "last_input_tokens", 0) or 0
        call1_output_tokens: int = getattr(llm_client, "last_output_tokens", 0) or 0

        response_1_clean = _clean_reasoning(response_1)
        tool_call_dict, _parse_error = _parse_tool_call(response_1_clean)

        tool_call_attempts = 1
        parse_error_flag = False

        if not tool_call_dict:
            parse_error_flag = True
            tool_call_attempts = 2
            retry_p = RETRY_PROMPT.format(task_prompt=task_prompt)
            response_1 = llm_client.query(
                model=model,
                prompt=retry_p,
                system=system_prompt,
                provider=provider,
                **{k: v for k, v in kwargs.items() if k != "provider"},
            ) or ""
            call1_tokens += getattr(llm_client, "last_token_usage", 0) or 0
            call1_cost += getattr(llm_client, "last_request_cost", 0.0) or 0.0
            call1_input_tokens += getattr(llm_client, "last_input_tokens", 0) or 0
            call1_output_tokens += getattr(llm_client, "last_output_tokens", 0) or 0
            response_1_clean = _clean_reasoning(response_1)
            tool_call_dict, _parse_error = _parse_tool_call(response_1_clean)

        call1_time = time.time() - call1_start

        tool_name: str = tool_available
        tool_parameters: dict[str, Any] = {}

        if tool_call_dict:
            raw_tool_name = tool_call_dict.get("name", tool_available)
            normalized_name, is_anomaly = ToolAdapterAudit.normalize_tool_name(raw_tool_name)
            tool_name = normalized_name
            tool_parameters = tool_call_dict.get("parameters", {})

            if is_anomaly:
                logger.warning(
                    "Tool name normalized: '%s' → '%s'", raw_tool_name, normalized_name,
                )
        else:
            # Both attempts failed — proceed to synthesis with parse_error transcript
            tool_transcript: dict[str, Any] = {
                "status": "parse_error",
                "error": "Model did not produce valid tool call",
                "raw_response": response_1,
                "tool_type_called": tool_available,
            }
            mcp_latency = 0.0
            call2_start = time.time()
            response_2 = _run_synthesis(
                llm_client, model, provider, tool_name, tool_transcript,
                task_prompt, kwargs,
            )
            call2_time = time.time() - call2_start
            call2_tokens: int = getattr(llm_client, "last_token_usage", 0) or 0
            call2_cost: float = getattr(llm_client, "last_request_cost", 0.0) or 0.0
            call2_input_tokens: int = getattr(llm_client, "last_input_tokens", 0) or 0
            call2_output_tokens: int = getattr(llm_client, "last_output_tokens", 0) or 0
            return _build_result(
                response_2, call1_time + call2_time, tool_transcript,
                tool_call_dict, response_1, self.asset, llm_client=llm_client,
                call1_time_s=call1_time, mcp_latency_s=mcp_latency,
                call2_time_s=call2_time, total_time_s=call1_time + call2_time,
                call1_tokens=call1_tokens, call2_tokens=call2_tokens,
                input_tokens=call1_input_tokens + call2_input_tokens,
                output_tokens=call1_output_tokens + call2_output_tokens,
                cost_usd=call1_cost + call2_cost,
                tool_call_attempts=tool_call_attempts, parse_error_flag=parse_error_flag,
            )

        # 5. Call MCP server
        base_url = mcp_base_url(health_url)
        mcp_start = time.time()
        tool_transcript = _call_mcp_tool(base_url, tool_name, tool_parameters)
        mcp_latency = time.time() - mcp_start
        tool_transcript["tool_type_called"] = tool_name

        # 6. Second model call: synthesis based on tool result
        call2_start = time.time()
        response_2 = _run_synthesis(
            llm_client, model, provider, tool_name, tool_transcript,
            task_prompt, kwargs,
        )
        call2_time = time.time() - call2_start
        call2_tokens = getattr(llm_client, "last_token_usage", 0) or 0
        call2_cost = getattr(llm_client, "last_request_cost", 0.0) or 0.0
        call2_input_tokens = getattr(llm_client, "last_input_tokens", 0) or 0
        call2_output_tokens = getattr(llm_client, "last_output_tokens", 0) or 0

        total_time = call1_time + mcp_latency + call2_time
        execution_time = call1_time + call2_time

        # 7. Build BenchmarkResult
        return _build_result(
            response_2, execution_time, tool_transcript,
            tool_call_dict, response_1, self.asset, llm_client=llm_client,
            call1_time_s=call1_time, mcp_latency_s=mcp_latency,
            call2_time_s=call2_time, total_time_s=total_time,
            call1_tokens=call1_tokens, call2_tokens=call2_tokens,
            input_tokens=call1_input_tokens + call2_input_tokens,
            output_tokens=call1_output_tokens + call2_output_tokens,
            cost_usd=call1_cost + call2_cost,
            tool_call_attempts=tool_call_attempts, parse_error_flag=parse_error_flag,
        )

    # ------------------------------------------------------------------
    # Public: score_response  # noqa: ERA001
    # ------------------------------------------------------------------

    def score_response(self, result: BenchmarkResult) -> BenchmarkResult:
        """Scoring via ToolUseEvaluator. Kein Netzaufruf."""
        evaluator = ToolUseEvaluator(self.config.get("config", {}))

        tool_transcript: dict[str, Any] = result.data.get("tool_transcript", {})
        model_output: str = result.raw_response
        tool_call_parsed: dict[str, Any] = result.data.get("tool_call_parsed", {})

        excerpt_quality: str = tool_transcript.get("excerpt_quality", "empty")
        parse_attempts: int = result.data.get("tool_call_attempts", result.data.get("parse_attempts", 1))

        p1 = evaluator.score_phase1(
            tool_transcript, self.asset,
            excerpt_quality=excerpt_quality,
            parse_attempts=parse_attempts,
        )
        p2_raw = evaluator.score_phase2(model_output, tool_transcript, self.asset)

        # Content Verification Gate — computes CV state (caps only for B1 and C now)
        caps = _load_scoring_caps()
        p2_cv, cv_block = ToolAdapterAudit.run_content_verification(
            tool_transcript, model_output, self.asset, p1, p2_raw, caps,
        )

        # Derive tool_content for judge: full tool text or search excerpts
        tool_content = _derive_tool_content(tool_transcript)
        tool_content_quality = cv_block.get("state", "A")

        # LLM Judge: replace rule-based P2 with judge score when judge is available
        judge_result, p2, hallucination_detected = self._run_llm_judge(
            result, model_output, tool_content, tool_content_quality, p2_cv,
        )

        # Hallucination cap — zweistufig: Schwere bestimmt sich am P2 vor der Kappung.
        # P2 <= threshold_severe → cap_hard (Fabrication); > threshold → cap_moderate (mild).
        if hallucination_detected and judge_result is not None:
            hal_cap = float(ToolAdapterAudit.load_hallucination_cap_tiered(p2))
            p2 = min(p2, hal_cap)

        # Determine if tool call was valid (used for combined score guardrail)
        # For failure tests the expected outcome is an error — status check is inverted
        is_failure_test = self.asset.get("is_failure_test", False)
        if is_failure_test:
            tool_call_valid = p1 >= 40.0
        else:
            tool_call_valid = tool_transcript.get("status") == "success" and p1 >= 40.0

        combined = evaluator.combined_score(
            p1, p2, tool_call_valid=tool_call_valid,
            asset_id=self.asset.get("metadata", {}).get("id", ""),
            benchmarks_config=self.config.get("benchmarks", []),
        )

        audit = evaluator.build_audit_block_with_output(
            p1, p2, combined, tool_transcript, self.asset, model_output,
        )

        # Pipeline diagnostics (instrument MCP/Parser/Search quality)
        diag = PipelineDiagnostician.build_diagnostic(
            asset_id=self.asset.get("metadata", {}).get("id", "unknown"),
            model_id=result.meta.get("model_id", "unknown"),
            scenario="mcp_flow",  # Always actual flow; reference/stub tested separately
            tool_call_valid=tool_call_valid,
            tool_transcript=tool_transcript,
            raw_response=result.data.get("response_1", ""),
            cleaned_response=result.data.get("response_1", ""),
            parse_attempts=result.data.get("tool_call_attempts", 1),
            p1_score=p1,
            p2_score=p2,
            combined_score=combined,
            json_error=None,
        )
        PipelineDiagnostician.log_diagnostic(diag)

        # Tool adapter audit (diagnose tool-name/format anomalies)
        tool_adapter_audit = None
        if p1 == 0.0:  # Hard fail — worth auditing
            tool_adapter_audit = ToolAdapterAudit.diagnose_p1_zero_case(
                tool_call_parsed, tool_transcript, self.asset, p1,
            )
            ToolAdapterAudit.log_audit(
                tool_adapter_audit,
                context=f"{self.asset.get('metadata', {}).get('id')} — p1=0",
            )

        result.primary_score = combined
        result.rendered_value = f"{combined:.1f}"
        result.data[FIELD_P1_SCORE] = p1
        result.data[FIELD_P2_SCORE] = p2
        result.data[FIELD_COMBINED_SCORE] = combined
        result.data["audit_block"] = audit
        result.data[FIELD_HALLUCINATION_FLAG] = (
            hallucination_detected or (p2 == 0.0 and self.asset.get("is_failure_test", False))
        )
        result.data[FIELD_CONTENT_VERIFICATION] = cv_block
        result.data[FIELD_TOOL_CONTENT_STATE] = cv_block["state"]
        result.data["pipeline_diagnostic"] = {
            "asset_id": diag.asset_id,
            "scenario": diag.scenario,
            "tool_call_valid": diag.tool_call_valid,
            "output_quality": diag.output_metrics.excerpt_quality,
            "parse_attempts": diag.parse_metrics.parse_attempts,
            "is_expected": diag.is_expected,
        }
        if tool_adapter_audit:
            result.data["tool_adapter_audit"] = tool_adapter_audit
        if judge_result is not None:
            result.data["llm_judge"] = {
                "score": judge_result.score,
                "parse_success": judge_result.parse_success,
                "hallucination_detected": judge_result.hallucination_detected,
                "content_grounding": judge_result.judge_content_grounding,
                "provider": judge_result.judge_provider_used,
                "model": judge_result.judge_model_used,
                "latency_ms": judge_result.judge_latency_ms,
            }

        # Anomaly callouts for per-asset audit logs.
        _callouts = _build_anomaly_callouts(
            hallucination_detected, tool_transcript, cv_block,
        )
        if _callouts:
            result.data["anomaly_callouts"] = _callouts

        ToolUseIOManager.print_asset_result(result, self.asset)
        return result


    def _run_llm_judge(
        self,
        result: BenchmarkResult,
        model_output: str,
        tool_content: str | None,
        tool_content_quality: str,
        p2_cv: float,
    ) -> tuple[Any, float, bool]:
        """LLM-Judge-Aufruf; Fallback auf CV-gated rule-based P2.

        Refactoring 2026-08-15 (Review): aus score_response (CC=18) ausgelagert.
        Kein Ersatz-Judge — bei Judge-Ausfall greift der regelbasierte P2-Score.
        """
        judge_result = None
        p2 = p2_cv  # fallback to CV-gated rule-based score
        hallucination_detected: bool = False
        try:
            from utils.config_validator import ConfigValidator
            _global_cfg = ConfigValidator().config
            judge_cfg_dict = _global_cfg.get("llm_judge", {})
            if judge_cfg_dict and judge_cfg_dict.get("enabled", False):
                judge_config = LLMJudgeConfig.from_dict(judge_cfg_dict)
                runner = JudgeRunner(judge_config)
                task_prompt_str: str = self.asset.get("prompt", "")
                golden_answer: str = (
                    self.asset.get("evaluation", {})
                    .get("phase2", {})
                    .get("golden_answer", "")
                )
                phase2_rubric = (
                    self.asset.get("evaluation", {}).get("phase2_rubric")
                )
                rubric_text = _build_rubric_override(phase2_rubric) if phase2_rubric else None
                judge_result = runner.score(
                    task_prompt=task_prompt_str,
                    model_response=model_output,
                    golden_standard=golden_answer,
                    module_id="tooluse",
                    tested_model_id=result.meta.get("model_id"),
                    tested_model_provider=result.meta.get("provider"),
                    tool_content=tool_content,
                    tool_content_quality=tool_content_quality,
                    rubric_override=rubric_text,
                )
                if judge_result.parse_success and judge_result.score is not None:
                    scale = judge_config.scoring.scale
                    p2 = round((judge_result.score / scale) * 100.0, 2)
                    p2 = min(p2, 100.0)
                if judge_result.hallucination_detected is not None:
                    hallucination_detected = judge_result.hallucination_detected
        except JudgeUnavailableError:
            logger.warning("LLM Judge unavailable for tooluse; using rule-based P2", exc_info=True)
            result.data["judge_fallback"] = True
        except Exception:  # pylint: disable=broad-exception-caught
            # Review 2026-08-15: vorher `except (JudgeUnavailableError, Exception)`
            # — redundant und verschluckte auch Programmierfehler still. Getrennt
            # behandelt, beide Pfade loggen mit exc_info.
            logger.warning("LLM Judge failed for tooluse; using rule-based P2", exc_info=True)
            result.data["judge_fallback"] = True
        return judge_result, p2, hallucination_detected


def _derive_tool_content(tool_transcript: dict[str, Any]) -> str | None:
    """Full tool text (http_fetch) oder Search-Excerpts (web_search)."""
    tool_content: str | None = None
    _tc_raw = tool_transcript.get("content")
    if isinstance(_tc_raw, list) and _tc_raw:
        tool_content = _tc_raw[0].get("text") if isinstance(_tc_raw[0], dict) else None
    if not tool_content:
        # web_search: build content from results list
        _results = tool_transcript.get("results") or []
        if _results:
            tool_content = "\n\n".join(
                f"{r.get('title', '')}\n{r.get('url', '')}\n{r.get('excerpt', '')}"
                for r in _results if isinstance(r, dict)
            ) or None
    return tool_content


def _build_anomaly_callouts(
    hallucination_detected: bool,
    tool_transcript: dict[str, Any],
    cv_block: dict[str, Any],
) -> list[str]:
    """Anomaly callouts für per-asset Audit-Logs (GitHub-Alert-Blöcke).

    generate_audit_log() prepended diese Blöcke, damit generate_review.py
    sie via Regex aufnehmen kann.
    """
    _callouts: list[str] = []
    if hallucination_detected:
        _callouts.append(
            "> [!WARNING]\n"
            "> **Halluzination erkannt:** Das Modell hat auf diesem Asset Inhalte generiert, die\n"
            "> nicht aus dem abgerufenen Tool-Ergebnis stammen, sondern erfunden wurden.\n"
            "> P2-Score wurde durch Halluzinations-Cap begrenzt. Für content-kritische Tasks\n"
            "> (Recherche, Faktenberichte) ist dieses Verhalten ein disqualifizierendes Signal."
        )
    if tool_transcript.get("status") == "parse_error":
        _callouts.append(
            "> [!CAUTION]\n"
            "> **Parse-Fehler beim Tool-Call:** Das Modell hat auf diesem Asset keinen auswertbaren\n"
            "> MCP-Tool-Call erzeugt. Mögliche Ursache: Das Modell verwendet ein proprietäres\n"
            "> natives Tool-Format statt des CrucibleMark-Custom-JSON-Schemas (z. B.\n"
            "> `{\"tool_call\": {\"name\": ..., \"parameters\": ...}}` statt `{\"name\": ..., \"input\": ...}`).\n"
            "> Über die native API (SDK-Level) ist das Modell vollständig tool-use-fähig."
        )
    # State C: model completely ignored tool-use instruction
    if cv_block.get("state") == "C":
        _callouts.append(
            "> [!ERROR]\n"
            "> **Kein Tool-Call — vollständig parametrische Antwort:** Das Modell hat die\n"
            "> Tool-Use-Instruktion auf diesem Asset ignoriert und stattdessen ausschließlich\n"
            "> aus Trainingswissen geantwortet (Content-Verification-State C, P1=0).\n"
            "> P2 ist auf max. 20 Punkte gekappt. Für agentic Workflows, die den aktiven\n"
            "> Tool-Einsatz voraussetzen, ist dieses Modell auf diesem Aufgabentyp nicht geeignet."
        )
    # State B2 with usable content: model got good data but answered from training knowledge
    if cv_block.get("tool_result_ignored") and not hallucination_detected:
        _callouts.append(
            "> [!CAUTION]\n"
            "> **Tool-Ergebnis ignoriert:** Das MCP-Tool lieferte verwertbaren Content, aber das\n"
            "> Modell antwortete ohne erkennbaren Bezug zum abgerufenen Inhalt\n"
            "> (Content-Verification-State B2, `tool_result_ignored: true`). Die Antwort stammt\n"
            "> vermutlich aus Trainingswissen statt aus den Tool-Ergebnissen. Subtiler als\n"
            "> Halluzination: Der Output kann inhaltlich korrekt wirken, ist aber nicht gegrounded."
        )
    return _callouts


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

_TOOL_CALL_RE = re.compile(
    r'\{[^{}]*"tool_call"[^{}]*\{[^{}]*\}[^{}]*\}',
    re.DOTALL,
)


def _parse_tool_call(text: str) -> tuple[dict[str, Any] | None, str | None]:
    """Extracts {"tool_call": {...}} from model output.
    JSON may be embedded in markdown code blocks or prose.
    Returns (tool_call_dict, None) on success, (None, error_string) on failure.
    """
    # Strip markdown code fences
    stripped = re.sub(r"```(?:json)?\s*", "", text)
    stripped = stripped.replace("```", "")

    # Try to find any JSON object containing "tool_call"
    candidates = re.findall(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)?\}", stripped, re.DOTALL)
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            if "tool_call" in parsed and isinstance(parsed["tool_call"], dict):
                return parsed["tool_call"], None
        except (json.JSONDecodeError, ValueError):
            continue

    # Broader fallback: find outermost JSON object
    depth = 0
    start = None
    for i, ch in enumerate(stripped):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                fragment = stripped[start : i + 1]
                try:
                    parsed = json.loads(fragment)
                    if "tool_call" in parsed and isinstance(parsed["tool_call"], dict):
                        return parsed["tool_call"], None
                except (json.JSONDecodeError, ValueError):
                    pass
                start = None

    return None, "No valid tool_call JSON found"


def _call_mcp_tool(base_url: str, tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
    """POST JSON-RPC 2.0 tools/call to MCP server. Returns transcript dict. Never raises."""
    body = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": params,
        },
    }).encode("utf-8")
    req = urllib.request.Request(
        base_url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            rpc_response = json.loads(resp.read().decode("utf-8"))
        if "error" in rpc_response:
            err = rpc_response["error"]
            return {"status": "error", "status_code": err.get("code"), "error": err.get("message", "JSON-RPC error")}
        return rpc_response.get("result", {})
    except urllib.error.HTTPError as exc:
        return {"status": "error", "status_code": exc.code, "error": str(exc)}
    except urllib.error.URLError as exc:
        return {"status": "error", "status_code": None, "error": str(exc.reason)}
    except Exception as exc:  # noqa: BLE001 — pylint: disable=broad-exception-caught
        return {"status": "error", "status_code": None, "error": str(exc)}


def _extract_tool_content(transcript: dict[str, Any]) -> str:
    """Extract clean text content from MCP transcript.

    Priority order:
    1. content[0].text  — standard MCP agent format
    2. results[]        — web_search structured results (formatted as readable text)
    3. content_excerpt  — legacy fallback (may be raw HTML in live mode)
    4. Error summary    — if tool failed
    """
    content_list = transcript.get("content")
    if content_list and isinstance(content_list, list):
        for item in content_list:
            if isinstance(item, dict) and item.get("type") == "text":
                text = item.get("text", "").strip()
                if text:
                    return text

    results = transcript.get("results")
    if results and isinstance(results, list):
        parts = []
        for r in results:
            if not isinstance(r, dict):
                continue
            title = r.get("title", "")
            url = r.get("url", "")
            excerpt = r.get("excerpt") or r.get("content", "")
            line = "\n".join(filter(None, [title, url, excerpt]))
            if line.strip():
                parts.append(line.strip())
        if parts:
            return "\n\n".join(parts)

    excerpt = transcript.get("content_excerpt")
    if excerpt:
        return str(excerpt)

    status = transcript.get("status", "unknown")
    error = transcript.get("error", "")
    return f"[Tool status: {status}]" + (f" — {error}" if error else "")


def _run_synthesis(
    llm_client: Any,
    model: str,
    provider: str | None,
    tool_name: str,
    tool_transcript: dict[str, Any],
    task_prompt: str,
    kwargs: dict[str, Any],
    system_prompt: str = SYNTHESIS_SYSTEM_PROMPT,
) -> str:
    followup = FOLLOWUP_PROMPT_TEMPLATE.format(
        tool_name=tool_name,
        tool_content=_extract_tool_content(tool_transcript),
        original_task=task_prompt,
    )
    return llm_client.query(
        model=model,
        prompt=followup,
        system=system_prompt,
        provider=provider,
        **{k: v for k, v in kwargs.items() if k != "provider"},
    ) or ""


def _build_result(
    response_2: str,
    execution_time: float,
    tool_transcript: dict[str, Any],
    tool_call_dict: dict[str, Any] | None,
    response_1: str,
    asset: dict[str, Any],
    llm_client: Any = None,
    call1_time_s: float = 0.0,
    mcp_latency_s: float = 0.0,
    call2_time_s: float = 0.0,
    total_time_s: float = 0.0,
    call1_tokens: int = 0,
    call2_tokens: int = 0,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cost_usd: float = 0.0,
    tool_call_attempts: int = 1,
    parse_error_flag: bool = False,
) -> BenchmarkResult:
    meta = {}
    if llm_client is not None:
        meta = getattr(llm_client, "last_response_metadata", {})

    return BenchmarkResult(
        status="success",
        primary_score=None,
        raw_response=response_2,
        execution_time=execution_time,
        tokens_used=call1_tokens + call2_tokens,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost_usd,
        meta=meta,
        data={
            "tool_transcript": tool_transcript,
            "tool_call_parsed": tool_call_dict,
            "response_1": response_1,
            "asset_id": asset.get("metadata", {}).get("id", "unknown"),
            "call1_time_s": call1_time_s,
            "mcp_latency_s": mcp_latency_s,
            "call2_time_s": call2_time_s,
            "total_time_s": total_time_s,
            "call1_tokens": call1_tokens,
            "call2_tokens": call2_tokens,
            "total_tokens": call1_tokens + call2_tokens,
            "cost_usd": cost_usd,
            "tool_call_attempts": tool_call_attempts,
            "retry_required": parse_error_flag,
        },
    )


def _clean_reasoning(text: str) -> str:
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    return cleaned.strip()
