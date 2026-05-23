"""
Diagnostic Test Scenarios für Tool Use Pipeline.

A/B-Sanity-Check:
1. MCP-Flow: Normal via Tavily + MCP
2. Reference-Output: Hartcodierter, bekannt guter Tool-Output
3. Stub-Direct: Minimal tool response mit exakter erwarteter Struktur

Vergleich der Modell-Performance über 3 Szenarien zeigt ob Fehler
in der Pipeline (Search/Parse/MCP) oder im Modell selbst sitzt.
"""

from __future__ import annotations

import json
from typing import Any, Dict

# Reference outputs (hand-curated, known to be correct)
REFERENCE_OUTPUTS = {
    "tooluse001": {
        "status": "success",
        "provider": "tavily_reference",
        "results": [
            {
                "url": "https://llama.meta.com/docs/llama_use_policy",
                "title": "Meta Llama Use Policy (Reference)",
                "excerpt": (
                    "Meta Llama 3 models are subject to the Acceptable Use Policy and the "
                    "Llama 3 Community License. Commercial use is restricted in certain EU jurisdictions. "
                    "Users must accept the license agreement for production use."
                ),
            },
            {
                "url": "https://huggingface.co/meta-llama/Llama-3-70b",
                "title": "Llama 3 Model Card",
                "excerpt": (
                    "The EU AI Act Restricted Applicability applies to certain use cases. "
                    "Restrictions on high-risk applications and government use must be reviewed."
                ),
            },
        ],
    },
    "tooluse002": {
        "status": "success",
        "provider": "http_reference",
        "content_excerpt": (
            "Gemma 3: A 4-billion parameter model optimized for inference. "
            "Use cases: Summarization, text generation, conversational AI. "
            "Llama 3.1: A 8B/70B production-grade model by Meta. "
            "Mistral 7B: A fast inference model suitable for edge deployment and RAG systems."
        ),
    },
    "tooluse003": {
        "status": "error",
        "status_code": 404,
        "provider": "http_reference",
        "error": "HTTP 404: Resource not found",
    },
}

# Stub outputs (minimal, structurally correct)
STUB_OUTPUTS = {
    "tooluse001": {
        "status": "success",
        "provider": "stub",
        "results": [
            {
                "url": "https://llama.meta.com/",
                "excerpt": "Llama EU policy information available.",
            },
        ],
    },
    "tooluse002": {
        "status": "success",
        "provider": "stub",
        "content_excerpt": "Model comparison and use cases provided.",
    },
    "tooluse003": {
        "status": "error",
        "status_code": 404,
        "provider": "stub",
        "error": "Not found",
    },
}


def create_diagnostic_transcript(
    asset_id: str,
    scenario: str,
) -> Dict[str, Any]:
    """
    Create a tool_transcript for diagnostic testing.

    Args:
        asset_id: 'tooluse001', 'tooluse002', or 'tooluse003'
        scenario: 'mcp_flow', 'reference_output', or 'stub_direct'

    Returns:
        tool_transcript dict
    """
    if scenario == "reference_output":
        base = REFERENCE_OUTPUTS.get(asset_id, {})
    elif scenario == "stub_direct":
        base = STUB_OUTPUTS.get(asset_id, {})
    else:
        # 'mcp_flow' — this would come from real MCP call
        return {}

    transcript = dict(base)
    transcript["tool_type_called"] = (
        "web_search" if asset_id == "tooluse001"
        else "http_fetch"
    )
    transcript["request_id"] = f"diagnostic_{scenario}_{asset_id}"
    transcript["timestamp"] = "2026-05-23T00:00:00Z"

    return transcript


def scenario_descriptions() -> Dict[str, str]:
    """Return descriptions of each diagnostic scenario."""
    return {
        "mcp_flow": (
            "Normal pipeline: Model → MCP → Tavily/HTTP → Tool Output → Synthesis. "
            "Tests full integration; if model fails here but passes in stub, pipeline issue."
        ),
        "reference_output": (
            "Known-good tool output (hand-curated). Model receives vetted data. "
            "If model still fails, it's handling the quality correctly OR has real model issues."
        ),
        "stub_direct": (
            "Minimal tool response with exact expected structure. "
            "Lowest friction scenario. If model fails here, likely hard model limitation."
        ),
    }


def diagnostic_report_template() -> str:
    """Return markdown template for diagnostic report."""
    return """# Tool Use Pipeline Diagnostic Report

## Test Results

| Model | Asset | MCP Flow P1 | Reference P1 | Stub P1 | Gap (MCP-Stub) | Likely Issue |
|---|---|---|---|---|---|---|
| {model_id} | {asset_id} | {mcp_p1:.1f} | {ref_p1:.1f} | {stub_p1:.1f} | {gap:.1f} | {issue} |

## Interpretation

- **Gap > 20 pts:** Strong indicator of pipeline issue (MCP/Search/Parse problem)
- **Gap < 5 pts:** Likely model limitation, not pipeline
- **Reference ≥ 80, Stub ≥ 80, MCP < 60:** Tavily/MCP quality issue
- **All three < 40:** Real model behavior issue

## Recommendations

1. If gaps cluster by scenario → focus on that layer
2. If gaps by model → focus on model configuration/prompt
3. If uniform → re-examine scoring rubric expectations
"""
