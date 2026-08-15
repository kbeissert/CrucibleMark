#!/usr/bin/env python3
"""Diagnostic Scenario Runner — A/B-Test für Pipeline-Fehlerquellen.

Führt ein Modell über 3 Szenarien:
1. MCP-Flow (normal)
2. Reference-Output (bekannt gut)
3. Stub-Direct (minimal)

Vergleich zeigt ob Fehler in Pipeline oder Modell sitzt.

Usage:
  python run_diagnostic_scenarios.py --model claude-haiku-4-5 --assets tooluse001 tooluse002
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from benchmark_modules.tooluse.DIAGNOSTIC_SCENARIOS import (  # noqa: E402
    create_diagnostic_transcript,
    scenario_descriptions,
)

from benchmark_modules.tooluse.core.diagnostics import (  # noqa: E402
    PipelineDiagnostic,
    PipelineDiagnostician,
)
from benchmark_modules.tooluse.core.evaluators import ToolUseEvaluator  # noqa: E402
from utils.module_registry import load_module_config  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def load_asset(asset_id: str) -> dict[str, Any]:
    """Load asset YAML."""
    asset_path = (
        _PROJECT_ROOT
        / "benchmark_modules"
        / "tooluse"
        / "assets"
        / f"{asset_id}.yaml"
    )
    if not asset_path.exists():
        raise FileNotFoundError(f"Asset not found: {asset_path}")

    import yaml

    return yaml.safe_load(asset_path.read_text(encoding="utf-8"))


def run_diagnostic_scenario(
    model_id: str,
    asset_id: str,
    scenario: str,
    evaluator: ToolUseEvaluator,
    asset: dict[str, Any],
) -> PipelineDiagnostic:
    """Run a single diagnostic scenario."""
    # Create tool transcript for scenario
    tool_transcript = create_diagnostic_transcript(asset_id, scenario)

    # Score Phase 1
    p1 = evaluator.score_phase1(tool_transcript, asset)

    # For Phase 2, we need a model output. In diagnostic mode, we use a stub response.
    model_output = f"Based on the tool output, this is a {scenario} response."

    # Score Phase 2
    p2 = evaluator.score_phase2(model_output, tool_transcript, asset)

    # Combined score
    tool_call_valid = (
        tool_transcript.get("status") == "success" and p1 >= 40.0
    )
    combined = evaluator.combined_score(p1, p2, tool_call_valid=tool_call_valid)

    # Build diagnostic
    diag = PipelineDiagnostician.build_diagnostic(
        asset_id=asset_id,
        model_id=model_id,
        scenario=scenario,
        tool_call_valid=tool_call_valid,
        tool_transcript=tool_transcript,
        raw_response=model_output,
        cleaned_response=model_output,
        parse_attempts=1,
        p1_score=p1,
        p2_score=p2,
        combined_score=combined,
    )

    return diag


def generate_report(
    diagnostics: list[PipelineDiagnostic],
    model_id: str,
) -> str:
    """Generate diagnostic report markdown."""
    lines = [
        "# Tool Use Pipeline Diagnostic Report",
        f"**Model:** {model_id}",
        "**Run Date:** 2026-05-23",
        "",
        "## Test Matrix",
        "",
        "| Asset | MCP Flow | Reference | Stub | Gap (MCP-Ref) | Issue Category |",
        "|---|---|---|---|---|---|",
    ]

    # Group by asset
    by_asset: dict[str, dict[str, PipelineDiagnostic]] = {}
    for diag in diagnostics:
        if diag.asset_id not in by_asset:
            by_asset[diag.asset_id] = {}
        by_asset[diag.asset_id][diag.scenario] = diag

    for asset_id in sorted(by_asset.keys()):
        scenarios = by_asset[asset_id]
        mcp = scenarios.get("mcp_flow")
        ref = scenarios.get("reference_output")
        stub = scenarios.get("stub_direct")

        if not mcp or not ref or not stub:
            continue

        gap_mcp_ref = mcp.p1_score - ref.p1_score

        if gap_mcp_ref > 20:
            issue = "🔴 Pipeline Issue (Search/Parse)"
        elif gap_mcp_ref > 10:
            issue = "🟡 Potential Pipeline Issue"
        elif ref.p1_score >= 80 and stub.p1_score >= 80 and mcp.p1_score < 60:
            issue = "🔴 Tavily/MCP Quality"
        elif mcp.p1_score < 40 and ref.p1_score < 40 and stub.p1_score < 40:
            issue = "🔴 Model Limitation"
        else:
            issue = "✅ Within Tolerance"

        lines.append(
            f"| {asset_id} | {mcp.p1_score:.1f} | {ref.p1_score:.1f} | "
            f"{stub.p1_score:.1f} | {gap_mcp_ref:.1f} | {issue} |",
        )

    lines += [
        "",
        "## Scenario Descriptions",
        "",
    ]

    for scenario, desc in scenario_descriptions().items():
        lines.append(f"### {scenario.upper()}")
        lines.append(desc)
        lines.append("")

    lines += [
        "## Interpretation Guide",
        "",
        "- **Gap > 20 pts (MCP vs Reference):** Strong pipeline issue indicator",
        "- **Gap 10-20 pts:** Moderate pipeline quality issue",
        "- **Gap < 5 pts:** Likely model limitation, not pipeline",
        "- **Reference ≥80, Stub ≥80, MCP <60:** Tavily search quality problem",
        "- **All three < 40:** Real model capability issue",
        "",
        "## Detailed Results",
        "",
    ]

    for diag in sorted(
        diagnostics, key=lambda d: (d.asset_id, d.scenario),
    ):
        lines.append(f"### {diag.asset_id} — {diag.scenario}")
        lines.append(json.dumps(
            {
                "p1": f"{diag.p1_score:.1f}",
                "p2": f"{diag.p2_score:.1f}",
                "combined": f"{diag.combined_score:.1f}",
                "output_quality": diag.output_metrics.excerpt_quality,
                "parse_attempts": diag.parse_metrics.parse_attempts,
                "tool_call_valid": diag.tool_call_valid,
            },
            indent=2,
        ))
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Run Tool Use diagnostic scenarios",
    )
    parser.add_argument(
        "--model",
        required=True,
        help="Model ID to test",
    )
    parser.add_argument(
        "--assets",
        nargs="+",
        default=["tooluse001", "tooluse002", "tooluse003"],
        help="Asset IDs to test",
    )
    parser.add_argument(
        "--output",
        default="diagnostic_report.md",
        help="Output file for report",
    )

    args = parser.parse_args()

    # Load config
    config_path = (
        _PROJECT_ROOT / "benchmark_modules" / "tooluse"
    )
    config = load_module_config(config_path).get("config", {})
    evaluator = ToolUseEvaluator(config)

    # Run diagnostics
    diagnostics: list[PipelineDiagnostic] = []

    for asset_id in args.assets:
        try:
            asset = load_asset(asset_id)
        except FileNotFoundError as e:
            logger.exception("Asset not found: %s", e)
            continue

        for scenario in ["mcp_flow", "reference_output", "stub_direct"]:
            logger.info("Running %s — %s...", asset_id, scenario)
            diag = run_diagnostic_scenario(
                args.model, asset_id, scenario, evaluator, asset,
            )
            diagnostics.append(diag)
            logger.info(
                "  P1=%.1f, P2=%.1f, Combined=%.1f",
                diag.p1_score, diag.p2_score, diag.combined_score,
            )

    # Generate report
    report = generate_report(diagnostics, args.model)

    # Save and print
    output_path = Path(args.output)
    output_path.write_text(report, encoding="utf-8")
    logger.info("Report saved to %s", output_path)

    print("\n" + report)


if __name__ == "__main__":
    main()
