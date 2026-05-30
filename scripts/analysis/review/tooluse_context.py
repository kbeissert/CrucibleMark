"""Context builder for tool-use LLM-narrative reviews."""

from __future__ import annotations

import ast
import csv
import math
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

_BENCHMARK_CSVS = [
    "benchmark_scores/local_models_benchmark.csv",
    "benchmark_scores/cloud_models_benchmark.csv",
    "benchmark_scores/commercial_models_benchmark.csv",
]

_ASSET_NAMES: dict[str, str] = {
    "tooluse001": "EU License Research",
    "tooluse002": "HTTP Fetch & Extract",
    "tooluse003": "Tool Failure Handling (404)",
    "tooluse004": "Web Search & Tool Selection",
    "tooluse005": "URL Construction & Fetch",
    "tooluse006": "Multilingual Search & Synthesis",
}


def _safe_float(val: Any) -> float | None:
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return None
    try:
        f = float(val)
        return None if math.isnan(f) else f
    except (ValueError, TypeError):
        return None


def _fmt(val: Any, decimals: int = 2) -> str:
    f = _safe_float(val)
    return f"{f:.{decimals}f}" if f is not None else "n/a"


def get_tooluse_leaderboard_row(model_id: str) -> dict[str, str]:
    csv_path = ROOT_DIR / "benchmark_scores" / "tooluse_leaderboard.csv"
    if not csv_path.exists():
        return {}
    try:
        with csv_path.open(encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if row.get("model", "") == model_id:
                    return dict(row)
    except Exception:
        pass
    return {}


def get_all_tooluse_model_ids() -> list[str]:
    csv_path = ROOT_DIR / "benchmark_scores" / "tooluse_leaderboard.csv"
    if not csv_path.exists():
        return []
    try:
        with csv_path.open(encoding="utf-8") as fh:
            return [row["model"] for row in csv.DictReader(fh) if row.get("model")]
    except Exception:
        return []


def _load_asset_details(model_id: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for csv_name in _BENCHMARK_CSVS:
        csv_path = ROOT_DIR / csv_name
        if not csv_path.exists():
            continue
        try:
            with csv_path.open(encoding="utf-8", newline="") as fh:
                for row in csv.DictReader(fh):
                    if not str(row.get("asset_id", "")).startswith("tooluse"):
                        continue
                    if row.get("model", "") != model_id:
                        continue
                    contribs: dict[str, Any] = {}
                    raw = row.get("score_contributions", "")
                    if raw:
                        try:
                            contribs = ast.literal_eval(raw)
                        except (ValueError, SyntaxError):
                            pass
                    results.append({
                        "asset_id": row.get("asset_id", ""),
                        "data": contribs,
                    })
        except Exception:
            pass
    return results


def _format_asset_breakdown_table(asset_details: list[dict[str, Any]]) -> str:
    if not asset_details:
        return "Keine Asset-Details verfügbar."
    lines = ["| Asset | P1 | P2 | Combined |", "|---|---|---|---|"]
    for asset in sorted(asset_details, key=lambda a: a.get("asset_id", "")):
        aid = asset.get("asset_id", "")
        name = _ASSET_NAMES.get(aid, aid)
        d = asset.get("data", {})
        lines.append(
            f"| {name} | {_fmt(d.get('p1_score'), 0)} "
            f"| {_fmt(d.get('p2_score'), 0)} "
            f"| {_fmt(d.get('combined_score'), 0)} |"
        )
    return "\n".join(lines)


def _extract_honeypot_detail(asset_details: list[dict[str, Any]]) -> str:
    for asset in asset_details:
        if asset.get("asset_id") == "tooluse001":
            d = asset.get("data", {})
            state = d.get("tool_content_state", "n/a")
            hallu = d.get("hallucination_flag", False)
            return (
                f"EU License Research — prüft ob das Modell aktuelle Lizenzrestriktionen "
                f"aus Web-Quellen abruft statt aus dem Training zu antworten (Honeypot-Test). "
                f"P2={_fmt(d.get('p2_score'), 0)} | Content-Verification-State: {state} | "
                f"Halluzination erkannt: {hallu}"
            )
    return "Keine Daten für EU License Research (tooluse001)."


def _extract_error_handling_detail(asset_details: list[dict[str, Any]]) -> str:
    for asset in asset_details:
        if asset.get("asset_id") == "tooluse003":
            d = asset.get("data", {})
            hallu = d.get("hallucination_flag", False)
            return (
                f"Tool Failure Handling (404) — misst ob das Modell bei einem fehlschlagenden "
                f"Tool-Call transparent kommuniziert oder Ersatzinhalt halluziniert. "
                f"P2={_fmt(d.get('p2_score'), 0)} | Halluzination trotz 404-Fehler: {hallu}"
            )
    return "Keine Daten für Tool Failure Handling (tooluse003)."


def _extract_tool_selection_detail(asset_details: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    descriptions = {
        "tooluse004": (
            "Web Search & Tool Selection — prüft ob das Modell ohne expliziten Hinweis "
            "erkennt, dass web_search statt fetch benötigt wird"
        ),
        "tooluse005": (
            "URL Construction & Fetch — prüft ob das Modell die korrekte URL aus eigenem "
            "Wissen ableiten und fetch korrekt ausführen kann"
        ),
    }
    for aid in ("tooluse004", "tooluse005"):
        for asset in asset_details:
            if asset.get("asset_id") == aid:
                d = asset.get("data", {})
                desc = descriptions[aid]
                parts.append(f"{desc}. P1={_fmt(d.get('p1_score'), 0)}")
    return "\n".join(parts) if parts else "Keine Tool-Selection-Daten (tooluse004/005 nicht gelaufen)."


def _score_label(combined: float | None) -> str:
    if combined is None:
        return "n/a"
    if combined >= 85:
        return "Excellent"
    if combined >= 70:
        return "Good"
    if combined >= 55:
        return "Moderate"
    return "Weak"


def _compute_fleet_avg(exclude_model_id: str | None = None) -> float | None:
    csv_path = ROOT_DIR / "benchmark_scores" / "tooluse_leaderboard.csv"
    if not csv_path.exists():
        return None
    scores: list[float] = []
    try:
        with csv_path.open(encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if exclude_model_id and row.get("model") == exclude_model_id:
                    continue
                v = _safe_float(row.get("combined_score", ""))
                if v is not None and v > 0:
                    scores.append(v)
    except Exception:
        return None
    return sum(scores) / len(scores) if scores else None


def get_tooluse_web_data(model_id: str) -> dict[str, Any] | None:
    """Return structured tooluse data for web export (no transcript fields)."""
    row = get_tooluse_leaderboard_row(model_id)
    if not row:
        return None

    asset_details = _load_asset_details(model_id)
    combined_v = _safe_float(row.get("combined_score", ""))
    fleet_avg_v = _compute_fleet_avg()

    assets: list[dict[str, Any]] = []
    for asset in sorted(asset_details, key=lambda a: a.get("asset_id", "")):
        aid = asset.get("asset_id", "")
        d = asset.get("data", {})
        assets.append({
            "id": aid,
            "name": _ASSET_NAMES.get(aid, aid),
            "p1": _safe_float(d.get("p1_score")),
            "p2": _safe_float(d.get("p2_score")),
            "combined": _safe_float(d.get("combined_score")),
        })

    def _row_float(key: str) -> float | None:
        return _safe_float(row.get(key, ""))

    def _row_bool(key: str) -> bool:
        v = str(row.get(key, "false")).strip().lower()
        return v in ("true", "1", "yes")

    cost_v = _row_float("cost_usd")

    return {
        "scores": {
            "p1": _row_float("p1_score"),
            "p2": _row_float("p2_score"),
            "combined": _row_float("combined_score"),
            "rating": _score_label(combined_v),
            "fleet_avg": fleet_avg_v,
        },
        "reliability": {
            "tool_call_valid": _row_bool("tool_call_valid"),
            "retry_required": _row_bool("retry_required"),
            "hallucination_flag": _row_bool("hallucination_flag"),
        },
        "performance": {
            "call1_time_s": _row_float("call1_time_s"),
            "mcp_latency_s": _row_float("mcp_latency_s"),
            "call2_time_s": _row_float("call2_time_s"),
            "total_time_s": _row_float("total_time_s"),
            "total_tokens": int(row.get("total_tokens") or 0),
            "cost_usd": cost_v if cost_v is not None else 0.0,
        },
        "assets": assets,
        "fleet_group": row.get("fleet_group", ""),
        "sovereignty_gap": _row_float("sovereignty_gap"),
    }


def build_tooluse_context(model_id: str) -> dict[str, str]:
    """Return template variables for the tooluse_reviewer prompt.

    Caller is responsible for adding model_tags, model_card_context,
    and use_case_classification_context from existing review helpers.
    """
    row = get_tooluse_leaderboard_row(model_id)
    if not row:
        return {}

    asset_details = _load_asset_details(model_id)
    combined_v = _safe_float(row.get("combined_score", ""))
    fleet_avg_v = _compute_fleet_avg()

    return {
        "display_model_name": row.get("display_name") or model_id,
        "model_tags": "n/a",
        "p1_score": _fmt(row.get("p1_score")),
        "p2_score": _fmt(row.get("p2_score")),
        "combined_score": _fmt(row.get("combined_score")),
        "score_label": _score_label(combined_v),
        "hallucination_flag": row.get("hallucination_flag", "false"),
        "tool_call_valid": row.get("tool_call_valid", "false"),
        "retry_required": row.get("retry_required", "false"),
        "call1_time_s": _fmt(row.get("call1_time_s")),
        "mcp_latency_s": _fmt(row.get("mcp_latency_s")),
        "call2_time_s": _fmt(row.get("call2_time_s")),
        "total_time_s": _fmt(row.get("total_time_s")),
        "cost_usd": row.get("cost_usd") or "local",
        "fleet_group": row.get("fleet_group", "n/a"),
        "sovereignty_gap": _fmt(row.get("sovereignty_gap")),
        "fleet_avg": _fmt(fleet_avg_v) if fleet_avg_v is not None else "n/a",
        "asset_breakdown_table": _format_asset_breakdown_table(asset_details),
        "honeypot_detail": _extract_honeypot_detail(asset_details),
        "error_handling_detail": _extract_error_handling_detail(asset_details),
        "tool_selection_detail": _extract_tool_selection_detail(asset_details),
        "model_card_context": "",
        "use_case_classification_context": "",
    }
