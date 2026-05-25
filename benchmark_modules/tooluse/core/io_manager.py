"""ToolUse Terminal I/O Manager — CrucibleMark
Handles all console output for the tooluse benchmark module.
No rich, no tqdm — stdlib only for display.
"""

from __future__ import annotations

import json
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from benchmark_modules.tooluse.core.constants import AUDIT_MCP_UNAVAILABLE
from schemas.result import BenchmarkResult

_ASSET_NAMES: dict[str, str] = {
    "tooluse001": "EU Lizenzrecherche",
    "tooluse002": "HTTP Fetch & Extract",
    "tooluse003": "404 Fehlerbehandlung",
}

_SEP_THIN = "-" * 54
_SEP_THICK = "=" * 54


# ---------------------------------------------------------------------------
# ANSI helpers — colours only in real TTY sessions, no noise in CI logs
# ---------------------------------------------------------------------------

def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if sys.stdout.isatty() else text


def _green(t: str) -> str:  return _c("92", t)
def _yellow(t: str) -> str: return _c("93", t)
def _red(t: str) -> str:    return _c("91", t)


# ---------------------------------------------------------------------------
# Logging — JSON metrics file
# ---------------------------------------------------------------------------

def _log_metrics_to_json(model_id: str, row: dict[str, Any]) -> None:
    """Write model metrics to tooluse_metrics.jsonl for monitoring & debugging."""
    log_file = _ROOT / "outputs" / "tooluse_metrics.jsonl"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        metric = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model_id": model_id,
            "combined_score": float(row.get("combined_score") or 0),
            "p1_score": float(row.get("p1_score") or 0),
            "p2_score": float(row.get("p2_score") or 0),
            "parse_error_rate": float(row.get("parse_error_rate") or 0),
            "tool_call_valid": str(row.get("tool_call_valid", "")).lower() == "true",
            "hallucination_flag": str(row.get("hallucination_flag", "")).lower() == "true",
            "total_tokens": int(row.get("total_tokens") or 0),
            "cost_usd": float(row.get("cost_usd") or 0),
            "fleet_group": row.get("fleet_group", "unknown"),
        }
        with log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(metric, ensure_ascii=False) + "\n")
    except Exception as exc:  # noqa: BLE001 — filesystem/json boundary
        sys.stderr.write(f"[Logging Error] Could not write metrics: {exc}\n")



_THRESHOLDS_DEFAULTS: dict[str, float] = {"excellent": 85.0, "good": 70.0, "moderate": 55.0, "weak": 0.0}


def _load_score_thresholds() -> dict[str, float]:
    try:
        data = yaml.safe_load(
            (_ROOT / "config" / "tooluse_report_config.yaml").read_text(encoding="utf-8"),
        ) or {}
        labels = data.get("report", {}).get("score_labels", {})
        if labels:
            return labels
    except FileNotFoundError:
        pass
    except Exception:  # noqa: BLE001 — yaml/filesystem boundary
        logging.warning("Could not load score thresholds from config", exc_info=True)
    return _THRESHOLDS_DEFAULTS


def _score_label(score: float) -> str:
    th = _load_score_thresholds()
    if score >= th.get("excellent", 85.0):
        return "Excellent"
    if score >= th.get("good", 70.0):
        return "Good"
    if score >= th.get("moderate", 55.0):
        return "Moderate"
    return "Weak"


def _deployment_rec(avg_combined: float, halluc_count: int) -> str:
    th = _load_score_thresholds()
    if halluc_count > 0:
        return "[NOT_RECOMMENDED] — Halluzination erkannt"
    if avg_combined >= th.get("good", 70.0):
        return "[PRODUCTION] Suitable for MCP production"
    if avg_combined >= th.get("moderate", 55.0):
        return "[CAUTION] Conditionally suitable — Synthesequalität prüfen"
    return "[NOT_RECOMMENDED] — Tool-Use-Kompetenz unzureichend"


# ---------------------------------------------------------------------------
# Main I/O Manager — all classmethods, no instance state
# ---------------------------------------------------------------------------

class ToolUseIOManager:
    """Console output for the tooluse benchmark module. Stateless classmethods only."""

    @staticmethod
    def _bar(score: float, width: int = 10) -> str:
        """ASCII progress bar: _bar(75, 10) → '███████░░░'"""
        filled = max(0, min(width, round(score / 100 * width)))
        return "█" * filled + "░" * (width - filled)

    @classmethod
    def print_asset_result(cls, result: BenchmarkResult, asset: dict[str, Any]) -> str:
        """Print per-asset result block. Returns the printed string (ANSI-free in tests)."""
        asset_id: str = (
            result.data.get("asset_id")
            or asset.get("metadata", {}).get("id", "unknown")
        )
        asset_name: str = _ASSET_NAMES.get(
            asset_id, asset.get("metadata", {}).get("name", asset_id),
        )

        lines: list[str] = [
            _SEP_THIN,
            f"  {asset_id} — {asset_name}",
            _SEP_THIN,
        ]

        # ── MCP unavailable ──────────────────────────────────────────────
        if result.data.get("audit_marker") == AUDIT_MCP_UNAVAILABLE:
            lines.append(f"  {_red('[ERROR] MCP Server nicht erreichbar — Asset übersprungen')}")
            lines.append("")
            out = "\n".join(lines)
            print(out)  # noqa: T201 — intentional terminal UI output
            return out

        transcript: dict[str, Any] = result.data.get("tool_transcript", {})
        tool_name: str = transcript.get("tool_type_called", "unknown")
        mcp_status: str = transcript.get("status", "unknown")
        mcp_provider: str = transcript.get("provider", "")
        mcp_latency: float = float(result.data.get("mcp_latency_s") or 0.0)
        attempts: int = int(result.data.get("tool_call_attempts") or 1)
        parse_error: bool = bool(result.data.get("retry_required", False))

        # ── Tool call line ───────────────────────────────────────────────
        if parse_error:
            tc_icon = _yellow("[WARN]")
            retry_note = f"({attempts} Versuche — Retry nötig)"
        else:
            tc_icon = _green("[OK]")
            retry_note = f"({attempts} Versuch)"
        lines.append(f"  Tool Call:     {tc_icon} {tool_name}  {retry_note}")

        # ── MCP status line ──────────────────────────────────────────────
        if mcp_status == "success":
            mcp_icon = _green("[OK]")
        elif mcp_status == "error":
            mcp_icon = _red("[ERROR]")
        else:
            mcp_icon = _yellow("[WARN]")
        provider_part = f" — {mcp_provider}" if mcp_provider else ""
        lines.append(f"  MCP Status:    {mcp_icon} {mcp_status}{provider_part}  [{mcp_latency:.1f}s]")

        # ── Source / content excerpt ─────────────────────────────────────
        results_list = transcript.get("results", [])
        if results_list and isinstance(results_list, list) and results_list[0].get("url"):
            lines.append(f"  Source:        {results_list[0]['url'][:60]}")
        elif transcript.get("content_excerpt"):
            raw = str(transcript["content_excerpt"])
            visible = re.sub(r"<[^>]+>", "", raw).strip()
            display = visible[:60] if visible else f"[HTML, {len(raw)} Zeichen]"
            lines.append(f"  Content:       {display}")

        lines.append("")

        # ── Scores ───────────────────────────────────────────────────────
        p1: float = float(result.data.get("p1_score") or 0)
        p2: float = float(result.data.get("p2_score") or 0)
        combined: float = float(result.data.get("combined_score") or 0)
        hallucination: bool = bool(result.data.get("hallucination_flag", False))

        lines.append(f"  P1 Tool Exec:  {p1:.1f} / 100   {cls._bar(p1)}")

        if hallucination:
            pattern_hint = ""
            audit: str = str(result.data.get("audit_block") or "")
            if audit:
                m = re.search(r"(?:hallucin|halluzi)[^:]*[:\-]\s*(.{5,50})", audit, re.IGNORECASE)
                if m:
                    pattern_hint = f' — Pattern: "{m.group(1).strip()}"'
            lines.append(f"  {_red('[HALLUCINATION] erkannt' + pattern_hint)}")
            lines.append(f"  P2 Synthesis:   {p2:.1f} / 100   {cls._bar(p2)}  [Hard Fail]")
        else:
            lines.append(f"  P2 Synthesis:  {p2:.1f} / 100   {cls._bar(p2)}")

        label = _score_label(combined)
        lines.append(f"  Combined:      {combined:.1f} / 100   {cls._bar(combined)}  [{label}]")
        lines.append("")

        # ── Timing & tokens ──────────────────────────────────────────────
        c1: float = float(result.data.get("call1_time_s") or 0)
        mcp_l: float = float(result.data.get("mcp_latency_s") or 0)
        c2: float = float(result.data.get("call2_time_s") or 0)
        total: float = float(result.data.get("total_time_s") or 0)
        tokens: int = int(result.data.get("total_tokens") or 0)
        cost: float = float(result.data.get("cost_usd") or 0)

        lines.append(
            f"  Time: Call 1: {c1:.1f}s  |  MCP: {mcp_l:.1f}s  |  Call 2: {c2:.1f}s  |  Total: {total:.1f}s",
        )
        lines.append(f"  Tokens: Tokens: {tokens}  |  Cost: ${cost:.6f}")
        lines.append("")

        out = "\n".join(lines)
        print(out)  # noqa: T201 — intentional terminal UI output
        return out

    @classmethod
    def print_run_summary_from_row(cls, row: dict[str, Any], model_id: str) -> str:
        """Print run summary from an aggregated leaderboard row dict. Returns the printed string."""
        lines: list[str] = [
            _SEP_THICK,
            f"  Tool Use Benchmark — {model_id}",
            _SEP_THICK,
        ]

        assets_run = int(row.get("assets_run") or 0)
        assets_error = int(row.get("assets_error") or 0)
        assets_ok = assets_run - assets_error
        ok_icon = _green("[OK]") if assets_error == 0 else _red("[ERR]")
        lines.append(f"  Assets:        {assets_ok}/{assets_run} {ok_icon}  ({assets_error} Fehler)")

        mcp_mode = str(row.get("mcp_mode") or "n/a")
        lines.append(f"  MCP-Modus:     {mcp_mode}")
        lines.append("")

        def _flt(key: str) -> float:
            try:
                return float(row.get(key) or 0)
            except (ValueError, TypeError):
                return 0.0

        avg_p1 = _flt("p1_score")
        avg_p2 = _flt("p2_score")
        avg_combined = _flt("combined_score")

        lines.append(f"  P1  Tool Exec: {avg_p1:.1f}  {cls._bar(avg_p1)}")
        lines.append(f"  P2  Synthesis: {avg_p2:.1f}  {cls._bar(avg_p2)}")
        label = _score_label(avg_combined)
        lines.append(f"  Combined:      {avg_combined:.1f}  {cls._bar(avg_combined)}  [{label}]")
        lines.append("")

        avg_c1 = _flt("call1_time_s")
        avg_mcp_l = _flt("mcp_latency_s")
        avg_c2 = _flt("call2_time_s")
        total_time = _flt("total_time_s")
        try:
            total_tokens = int(row.get("total_tokens") or 0)
        except (ValueError, TypeError):
            total_tokens = 0
        total_cost = _flt("cost_usd")

        lines.append(
            f"  Call 1: {avg_c1:.1f}s | MCP: {avg_mcp_l:.1f}s | Call 2: {avg_c2:.1f}s",
        )
        lines.append(f"  Total: {total_time:.1f}s ({assets_ok} Assets)")
        tok_str = f"{total_tokens:,}".replace(",", ".")
        lines.append(f"  Tokens: {tok_str} | Cost: ${total_cost:.6f}")
        lines.append("")

        tool_call_valid = str(row.get("tool_call_valid", "true")).lower() == "true"
        hallucination = str(row.get("hallucination_flag", "false")).lower() == "true"
        retry_required = str(row.get("retry_required", "false")).lower() == "true"

        v_icon = _green("[OK]") if tool_call_valid else _yellow("[WARN]")
        valid_count = assets_ok if tool_call_valid else 0
        lines.append(f"  Tool Calls:    {v_icon} {valid_count}/{assets_ok} valid")

        r_icon = _green("[NO]") if not retry_required else _yellow("[YES]")
        lines.append(f"  Retry Required:{r_icon}")

        h_str = _green("[NO]") if not hallucination else _red("[YES]")
        lines.append(f"  Hallucination: {h_str}")
        lines.append("")

        halluc_count = 1 if hallucination else 0
        rec = _deployment_rec(avg_combined, halluc_count)
        lines.append(f"  Empfehlung:    {rec}")
        lines.append(_SEP_THICK)

        out = "\n".join(lines)
        try:
            _log_metrics_to_json(model_id, row)
        except Exception:  # noqa: BLE001 — metrics logging must never crash the benchmark
            logging.debug("Metrics logging failed (non-critical)", exc_info=True)
        print(out)  # noqa: T201 — intentional terminal UI output
        return out

    @classmethod
    def print_run_summary(cls, results: list[BenchmarkResult], model_id: str) -> str:
        """Print run summary after all assets complete. Returns the printed string."""
        lines: list[str] = [
            _SEP_THICK,
            f"  Tool Use Benchmark — {model_id}",
            _SEP_THICK,
        ]

        if not results:
            lines.append("  Keine Ergebnisse.")
            lines.append(_SEP_THICK)
            out = "\n".join(lines)
            print(out)  # noqa: T201 — intentional terminal UI output
            return out

        successful = [r for r in results if r.status != "error"]
        n_failed = len(results) - len(successful)
        ok_icon = _green("[OK]") if n_failed == 0 else _red("[ERR]")
        lines.append(f"  Assets:        {len(successful)}/{len(results)} {ok_icon}  ({n_failed} Fehler)")

        # MCP mode from first result with a known provider
        mcp_mode = "n/a"
        for r in successful:
            tc = r.data.get("tool_transcript", {})
            provider = tc.get("provider", "")
            if provider and tc.get("status") == "success":
                mcp_mode = f"live ({provider})"
                break
            elif provider:
                mcp_mode = f"mock ({provider})"
                break
        lines.append(f"  MCP-Modus:     {mcp_mode}")
        lines.append("")

        # ── Aggregated scores ────────────────────────────────────────────
        def _avg(key: str) -> float:
            vals = [
                float(r.data[key]) for r in successful
                if r.data.get(key) not in (None, "")
            ]
            return sum(vals) / len(vals) if vals else 0.0

        avg_p1 = _avg("p1_score")
        avg_p2 = _avg("p2_score")
        avg_combined = _avg("combined_score")

        lines.append(f"  P1  Tool Exec: {avg_p1:.1f}  {cls._bar(avg_p1)}")
        lines.append(f"  P2  Synthesis: {avg_p2:.1f}  {cls._bar(avg_p2)}")
        label = _score_label(avg_combined)
        lines.append(f"  Combined:      {avg_combined:.1f}  {cls._bar(avg_combined)}  [{label}]")
        lines.append("")

        # ── Timing ───────────────────────────────────────────────────────
        avg_c1 = _avg("call1_time_s")
        avg_mcp = _avg("mcp_latency_s")
        avg_c2 = _avg("call2_time_s")
        total_time = sum(float(r.data.get("total_time_s") or 0) for r in successful)
        total_tokens = sum(int(r.data.get("total_tokens") or 0) for r in successful)
        total_cost = sum(float(r.data.get("cost_usd") or 0) for r in successful)

        lines.append(
            f"  Time: Ø Call 1: {avg_c1:.1f}s  |  Ø MCP: {avg_mcp:.1f}s  |  Ø Call 2: {avg_c2:.1f}s",
        )
        lines.append(f"  Time: Total Run: {total_time:.1f}s  ({len(successful)} Assets)")
        tok_str = f"{total_tokens:,}".replace(",", ".")
        lines.append(f"  Tokens: Tokens: {tok_str}  |  Cost: ${total_cost:.6f}")
        lines.append("")

        # ── Reliability ──────────────────────────────────────────────────
        retries = sum(
            max(0, int(r.data.get("tool_call_attempts") or 1) - 1) for r in successful
        )
        valid_count = sum(
            1 for r in successful
            if r.data.get("tool_transcript", {}).get("status")
            not in ("parse_error", "blocked", None, "")
        )
        halluc_count = sum(
            1 for r in successful if bool(r.data.get("hallucination_flag", False))
        )

        v_icon = _green("[OK]") if valid_count == len(successful) else _yellow("[WARN]")
        lines.append(f"  Tool Calls:    {v_icon} {valid_count}/{len(successful)} valide  ({retries} Retries)")

        h_str = _green("✅ Keine") if halluc_count == 0 else _red(f"⚠ {halluc_count} erkannt")
        lines.append(f"  Hallucination: {h_str}")
        lines.append("")

        rec = _deployment_rec(avg_combined, halluc_count)
        lines.append(f"  Empfehlung:    {rec}")
        lines.append(_SEP_THICK)

        out = "\n".join(lines)
        print(out)  # noqa: T201 — intentional terminal UI output
        return out
