"""
CLI: make tooluse-leaderboard
Recalculates sovereignty_gap and prints the Tool Use Leaderboard summary.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.core.tooluse_exporter import ToolUseExporter  # noqa: E402
from utils.config_validator import ConfigValidator  # noqa: E402


def main() -> None:
    config = ConfigValidator().config
    exporter = ToolUseExporter(config)

    written = exporter.aggregate_from_benchmark_csvs()
    if written == 0:
        print("No tooluse benchmark results found in benchmark_scores/.")
        print("Run: make tooluse-run MODEL=<model-id>")
        return

    exporter.calculate_sovereignty_gap()
    summary = exporter.get_summary()

    total = summary["total_models"]
    local_count = summary["local_sovereign_count"]
    full_count = summary["full_fleet_count"]
    avg_local = summary["fleet_avg_local"]
    avg_all = summary["fleet_avg_all"]
    gap_val = summary["sovereignty_gap"]
    top_local = summary["top_local_model"] or "—"
    top_overall = summary["top_overall_model"] or "—"

    avg_c1 = summary.get("avg_call1_time_s")
    avg_mcp = summary.get("avg_mcp_latency_s")
    avg_c2 = summary.get("avg_call2_time_s")
    total_tok = summary.get("total_tokens", 0)
    per_rate = summary.get("parse_error_rate")

    border = "═" * 51
    print(border)
    print("  CrucibleMark Tool Use Leaderboard")
    print(border)
    print(f"  Modelle gesamt:       {total:>8}")
    print(f"  Local Sovereign:      {local_count:>8}")
    print(f"  Full Fleet:           {full_count:>8}")
    print()

    if avg_local is not None:
        print(f"  Fleet Avg (Local):    {avg_local:>8.1f}")
    else:
        print("  Fleet Avg (Local):         n/a")

    if avg_all is not None:
        print(f"  Fleet Avg (All):      {avg_all:>8.1f}")
    else:
        print("  Fleet Avg (All):           n/a")

    if gap_val is not None:
        sign = "+" if gap_val >= 0 else ""
        note = "local lead" if gap_val > 0 else ("cloud lead" if gap_val < 0 else "parity")
        print(f"  Sovereignty Gap:      {sign}{gap_val:.1f}  ← {note}")
    else:
        print("  Sovereignty Gap:           n/a")

    print()
    print(f"  Top Local Model:   {top_local}")
    print(f"  Top Overall:       {top_overall}")

    print()
    print("  --- Performance (Ø über alle Modelle) ---")
    if avg_c1 is not None:
        print(f"  Call 1 (Tool-Call):   {avg_c1:>8.2f}s")
    else:
        print("  Call 1 (Tool-Call):        n/a")
    if avg_mcp is not None:
        print(f"  MCP-Latenz:           {avg_mcp:>8.2f}s")
    else:
        print("  MCP-Latenz:                n/a")
    if avg_c2 is not None:
        print(f"  Call 2 (Synthese):    {avg_c2:>8.2f}s")
    else:
        print("  Call 2 (Synthese):         n/a")
    print(f"  Tokens gesamt:        {total_tok:>8}")
    if per_rate is not None:
        print(f"  Parse-Error-Rate:     {per_rate:>7.1f}%")
    else:
        print("  Parse-Error-Rate:          n/a")

    print(border)


if __name__ == "__main__":
    main()
