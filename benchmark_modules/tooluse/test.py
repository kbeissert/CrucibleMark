"""
ToolUse Test Controller (v1.1)
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
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional

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
    FIELD_HALLUCINATION_FLAG,
    FIELD_P1_SCORE,
    FIELD_P2_SCORE,
    TOOL_HTTP_FETCH,
    TOOL_WEB_SEARCH,
)
from benchmark_modules.tooluse.core.evaluators import ToolUseEvaluator
from benchmark_modules.tooluse.core.io_manager import ToolUseIOManager
from utils.mcp_health import check_mcp_health, mcp_base_url
from utils.module_registry import load_module_config

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tool schemas injected into the system prompt
# ---------------------------------------------------------------------------

TOOL_SCHEMA_WEB_SEARCH: Dict[str, Any] = {
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

TOOL_SCHEMA_HTTP_FETCH: Dict[str, Any] = {
    "name": "http_fetch",
    "description": "Lädt den Inhalt einer URL.",
    "parameters": {
        "url": {
            "type": "string",
            "description": "Die zu ladende URL",
        },
        "max_chars": {
            "type": "integer",
            "description": "Maximale Zeichenanzahl des Ergebnisses",
            "default": 500,
        },
    },
}

_TOOL_SCHEMAS: Dict[str, Dict[str, Any]] = {
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
    "{tool_result_json}\n\n"
    "{original_task}"
)

RETRY_PROMPT = (
    "Deine letzte Antwort enthielt keinen gültigen Tool-Call.\n"
    "Antworte AUSSCHLIESSLICH mit diesem JSON-Format — kein weiterer Text:\n"
    '{{"tool_call": {{"name": "<tool_name>", "parameters": {{...}}}}}}\n\n'
    "Aufgabe: {task_prompt}"
)


class ToolUseTest(BaseTest):
    """
    Controller für das tooluse Benchmark-Modul.
    Orchestriert: MCP-Health → Tool-Schema-Injection → Erster Modell-Call →
    MCP-Tool-Call → Zweiter Modell-Call (Synthese) → Scoring.
    """

    def __init__(self, asset_path: Path) -> None:
        super().__init__(asset_path)
        self.config = load_module_config(Path(__file__).parent)

    # ------------------------------------------------------------------
    # Public: execute
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
            tool_schema_json=json.dumps(schema, ensure_ascii=False, indent=2)
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
            response_1_clean = _clean_reasoning(response_1)
            tool_call_dict, _parse_error = _parse_tool_call(response_1_clean)

        call1_time = time.time() - call1_start

        tool_name: str = tool_available
        tool_parameters: Dict[str, Any] = {}

        if tool_call_dict:
            tool_name = tool_call_dict.get("name", tool_available)
            tool_parameters = tool_call_dict.get("parameters", {})
        else:
            # Both attempts failed — proceed to synthesis with parse_error transcript
            tool_transcript: Dict[str, Any] = {
                "status": "parse_error",
                "error": "Model did not produce valid tool call",
                "raw_response": response_1,
                "tool_type_called": tool_available,
            }
            mcp_latency = 0.0
            call2_start = time.time()
            response_2 = _run_synthesis(
                llm_client, model, provider, tool_name, tool_transcript,
                task_prompt, kwargs
            )
            call2_time = time.time() - call2_start
            call2_tokens: int = getattr(llm_client, "last_token_usage", 0) or 0
            call2_cost: float = getattr(llm_client, "last_request_cost", 0.0) or 0.0
            return _build_result(
                response_2, call1_time + call2_time, tool_transcript,
                tool_call_dict, response_1, self.asset, llm_client=llm_client,
                call1_time_s=call1_time, mcp_latency_s=mcp_latency,
                call2_time_s=call2_time, total_time_s=call1_time + call2_time,
                call1_tokens=call1_tokens, call2_tokens=call2_tokens,
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
            task_prompt, kwargs
        )
        call2_time = time.time() - call2_start
        call2_tokens = getattr(llm_client, "last_token_usage", 0) or 0
        call2_cost = getattr(llm_client, "last_request_cost", 0.0) or 0.0

        total_time = call1_time + mcp_latency + call2_time
        execution_time = call1_time + call2_time

        # 7. Build BenchmarkResult
        return _build_result(
            response_2, execution_time, tool_transcript,
            tool_call_dict, response_1, self.asset, llm_client=llm_client,
            call1_time_s=call1_time, mcp_latency_s=mcp_latency,
            call2_time_s=call2_time, total_time_s=total_time,
            call1_tokens=call1_tokens, call2_tokens=call2_tokens,
            cost_usd=call1_cost + call2_cost,
            tool_call_attempts=tool_call_attempts, parse_error_flag=parse_error_flag,
        )

    # ------------------------------------------------------------------
    # Public: score_response
    # ------------------------------------------------------------------

    def score_response(self, result: BenchmarkResult) -> BenchmarkResult:
        """Scoring via ToolUseEvaluator. Kein Netzaufruf."""
        evaluator = ToolUseEvaluator(self.config.get("config", {}))

        tool_transcript: Dict[str, Any] = result.data.get("tool_transcript", {})
        model_output: str = result.raw_response

        p1 = evaluator.score_phase1(tool_transcript, self.asset)
        p2 = evaluator.score_phase2(model_output, tool_transcript, self.asset)
        combined = evaluator.combined_score(p1, p2)

        audit = evaluator.build_audit_block_with_output(
            p1, p2, combined, tool_transcript, self.asset, model_output
        )

        result.primary_score = combined
        result.rendered_value = f"{combined:.1f}"
        result.data[FIELD_P1_SCORE] = p1
        result.data[FIELD_P2_SCORE] = p2
        result.data[FIELD_COMBINED_SCORE] = combined
        result.data["audit_block"] = audit
        result.data[FIELD_HALLUCINATION_FLAG] = (
            p2 == 0.0 and self.asset.get("is_failure_test", False)
        )
        ToolUseIOManager.print_asset_result(result, self.asset)
        return result


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

_TOOL_CALL_RE = re.compile(
    r'\{[^{}]*"tool_call"[^{}]*\{[^{}]*\}[^{}]*\}',
    re.DOTALL,
)


def _parse_tool_call(text: str) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Extracts {"tool_call": {...}} from model output.
    JSON may be embedded in markdown code blocks or prose.
    Returns (tool_call_dict, None) on success, (None, error_string) on failure.
    """
    # Strip markdown code fences
    stripped = re.sub(r"```(?:json)?\s*", "", text)
    stripped = stripped.replace("```", "")

    # Try to find any JSON object containing "tool_call"
    candidates = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)?\}', stripped, re.DOTALL)
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


def _call_mcp_tool(base_url: str, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """POST to MCP server. Returns transcript dict. Never raises."""
    endpoint = f"{base_url}/tools/{tool_name}"
    body = json.dumps(params).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return {"status": "error", "status_code": exc.code, "error": str(exc)}
    except urllib.error.URLError as exc:
        return {"status": "error", "status_code": None, "error": str(exc.reason)}
    except Exception as exc:  # pylint: disable=broad-exception-caught
        return {"status": "error", "status_code": None, "error": str(exc)}


def _run_synthesis(
    llm_client: Any,
    model: str,
    provider: Optional[str],
    tool_name: str,
    tool_transcript: Dict[str, Any],
    task_prompt: str,
    kwargs: Dict[str, Any],
) -> str:
    followup = FOLLOWUP_PROMPT_TEMPLATE.format(
        tool_name=tool_name,
        tool_result_json=json.dumps(tool_transcript, ensure_ascii=False, indent=2),
        original_task=task_prompt,
    )
    return llm_client.query(
        model=model,
        prompt=followup,
        provider=provider,
        **{k: v for k, v in kwargs.items() if k != "provider"},
    ) or ""


def _build_result(
    response_2: str,
    execution_time: float,
    tool_transcript: Dict[str, Any],
    tool_call_dict: Optional[Dict[str, Any]],
    response_1: str,
    asset: Dict[str, Any],
    llm_client: Any = None,
    call1_time_s: float = 0.0,
    mcp_latency_s: float = 0.0,
    call2_time_s: float = 0.0,
    total_time_s: float = 0.0,
    call1_tokens: int = 0,
    call2_tokens: int = 0,
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
            "parse_error_flag": parse_error_flag,
        },
    )


def _clean_reasoning(text: str) -> str:
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    return cleaned.strip()
