"""Tool Use Report Generator — CrucibleMark
Reads tooluse_leaderboard.csv + per-asset benchmark CSVs,
produces Markdown reports and JSON web-export data.
No LLM calls, no MCP calls.
"""

from __future__ import annotations

import argparse
import ast
import csv
import json
import logging
import math
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from benchmark_modules.tooluse.core.methodology_notes import get_applicable_notes  # noqa: E402

logger = logging.getLogger(__name__)

# Asset names — SSOT for display
_ASSET_NAMES: dict[str, str] = {
    "tooluse001": "EU Lizenzrecherche",
    "tooluse002": "HTTP Fetch & Extract",
    "tooluse003": "404 Fehlerbehandlung",
}

_BENCHMARK_CSVS = [
    "benchmark_scores/local_models_benchmark.csv",
    "benchmark_scores/cloud_models_benchmark.csv",
    "benchmark_scores/commercial_models_benchmark.csv",
]


# ---------------------------------------------------------------------------
# Module-level rule-based helpers
# ---------------------------------------------------------------------------

def _safe_float(val: Any) -> float | None:
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return None
    try:
        f = float(val)
        return None if math.isnan(f) else f
    except (ValueError, TypeError):
        return None


def _safe_int(val: Any) -> int:
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return 0
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return 0


def _slugify(model_name: str) -> str:
    name = str(model_name).rsplit("/", maxsplit=1)[-1].lower()
    return re.sub(r"[^a-z0-9]+", "-", name).strip("-")


def _score_label(score: float, thresholds: dict[str, float]) -> str:
    if score >= thresholds.get("excellent", 85.0):
        return "Excellent"
    if score >= thresholds.get("good", 70.0):
        return "Good"
    if score >= thresholds.get("moderate", 55.0):
        return "Moderate"
    return "Weak"


def _build_strengths(row: dict[str, Any], asset_details: list[dict[str, Any]]) -> list[str]:
    strengths: list[str] = []
    p1 = _safe_float(row.get("p1_score", ""))
    p2 = _safe_float(row.get("p2_score", ""))
    tool_call_valid = str(row.get("tool_call_valid", "false")).lower() == "true"
    attempts = _safe_int(row.get("tool_call_attempts", 1))
    hallucination = str(row.get("hallucination_flag", "false")).lower() == "true"
    total_time = _safe_float(row.get("total_time_s", ""))

    if p1 is not None and p1 >= 80:
        strengths.append("Formuliert valide Tool-Calls zuverlässig")
    if tool_call_valid and attempts <= 1:
        strengths.append("Direkter valider Tool-Call ohne Retry-Bedarf")
    if p2 is not None and p2 >= 70:
        strengths.append("Solide Synthesequalität nach Tool-Ergebnis")
    if not hallucination:
        has_003 = any(a.get("asset_id") == "tooluse003" for a in asset_details)
        if has_003:
            strengths.append("Korrekte 404-Fehlerbehandlung ohne Halluzination")
    if total_time is not None and total_time <= 5.0:
        strengths.append("Schnelle End-to-End-Ausführung")

    return strengths


def _build_weaknesses(row: dict[str, Any]) -> list[str]:
    weaknesses: list[str] = []
    p2 = _safe_float(row.get("p2_score", ""))
    parse_error = str(row.get("retry_required", "false")).lower() == "true"
    hallucination = str(row.get("hallucination_flag", "false")).lower() == "true"
    total_time = _safe_float(row.get("total_time_s", ""))
    call1_tokens = _safe_int(row.get("call1_tokens", 0))

    if p2 is not None and p2 < 55:
        weaknesses.append("Synthesequalität unter Benchmark-Schwellenwert")
    if parse_error:
        weaknesses.append("Benötigt Retry für validen Tool-Call")
    if hallucination:
        weaknesses.append("⚠ Halluzination bei 404-Test — kritisch für Produktionseinsatz")
    if total_time is not None and total_time > 15.0:
        weaknesses.append("Hohe Gesamtlatenz für Tool-Use-Workflows")
    if call1_tokens > 200:
        weaknesses.append("Hoher Token-Verbrauch für Tool-Call-Formulierung")

    return weaknesses


def _build_deployment_recommendation(row: dict[str, Any]) -> str:
    combined = _safe_float(row.get("combined_score", ""))
    hallucination = str(row.get("hallucination_flag", "false")).lower() == "true"

    if hallucination:
        return "❌ Nicht empfohlen — Halluzination bei Fehlerszenarien"
    if combined is None:
        return "⚠ Keine Bewertung möglich — fehlende Scores"
    if combined >= 70:
        return "✅ Geeignet für MCP-Produktionseinsatz"
    if combined >= 55:
        return "⚠ Bedingt geeignet — Synthesequalität prüfen"
    return "❌ Nicht empfohlen — Tool-Use-Kompetenz unzureichend"


# ---------------------------------------------------------------------------
# Main generator class
# ---------------------------------------------------------------------------

class ToolUseReportGenerator:
    """Reads tooluse_leaderboard.csv and per-asset benchmark CSVs.
    Produces per-model Markdown + JSON and a fleet summary.
    No LLM calls, no MCP calls.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.report_cfg: dict[str, Any] = config.get("report", {})
        self.root = _ROOT

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def load_leaderboard(self) -> pd.DataFrame:
        """Load tooluse_leaderboard.csv. Returns empty DataFrame on missing/empty file."""
        csv_path = self.root / "benchmark_scores" / "tooluse_leaderboard.csv"
        if not csv_path.exists() or csv_path.stat().st_size == 0:
            return pd.DataFrame()
        try:
            return pd.read_csv(csv_path, dtype=str).fillna("")
        except Exception as exc:  # noqa: BLE001 — csv read boundary
            logger.warning("Could not read leaderboard: %s", exc)
            return pd.DataFrame()

    def load_asset_details(self, model_id: str) -> list[dict[str, Any]]:
        """Load per-asset rows for model_id from the 3 main benchmark CSVs."""
        results: list[dict[str, Any]] = []
        for csv_name in _BENCHMARK_CSVS:
            csv_path = self.root / csv_name
            if not csv_path.exists():
                continue
            try:
                with csv_path.open(encoding="utf-8", newline="") as f:
                    for row in csv.DictReader(f):
                        if not str(row.get("asset_id", "")).startswith("tooluse"):
                            continue
                        if row.get("model", "") != model_id:
                            continue
                        data_dict: dict[str, Any] = {}
                        raw = row.get("score_contributions", "")
                        if raw:
                            try:
                                data_dict = ast.literal_eval(raw)
                            except (ValueError, SyntaxError):
                                pass
                        results.append({
                            "asset_id": row.get("asset_id", ""),
                            "asset_name": row.get("asset_name", ""),
                            "status": row.get("status", ""),
                            "raw_response": row.get("raw_response", ""),
                            "data": data_dict,
                        })
            except (OSError, csv.Error) as exc:
                logger.debug("Could not read %s: %s", csv_name, exc)
        return results

    # ------------------------------------------------------------------
    # Score / label helpers
    # ------------------------------------------------------------------

    def _get_score_label(self, score: float) -> str:
        return _score_label(score, self.report_cfg.get("score_labels", {}))

    def _get_latency_label(self, total_time: float) -> str:
        labels = self.report_cfg.get("latency_labels", {})
        if total_time <= labels.get("fast", 3.0):
            return "Fast"
        if total_time <= labels.get("medium", 10.0):
            return "Medium"
        return "Slow"

    def _build_strengths(self, row: dict[str, Any], asset_details: list[dict[str, Any]]) -> list[str]:
        return _build_strengths(row, asset_details)

    def _build_weaknesses(self, row: dict[str, Any]) -> list[str]:
        return _build_weaknesses(row)

    def _build_deployment_recommendation(self, row: dict[str, Any]) -> str:
        return _build_deployment_recommendation(row)

    # ------------------------------------------------------------------
    # Report generation
    # ------------------------------------------------------------------

    def generate_model_report(self, model_id: str) -> str:
        """Generate Markdown report string for one model."""
        df = self.load_leaderboard()
        if df.empty or "model" not in df.columns:
            return f"# Tool Use Review — {model_id}\n\nKeine Daten vorhanden.\n"

        matching = df[df["model"] == model_id]
        if matching.empty:
            return f"# Tool Use Review — {model_id}\n\nModell nicht im Leaderboard gefunden.\n"

        row = matching.iloc[0].to_dict()
        asset_details = self.load_asset_details(model_id)

        display_name = row.get("display_name") or model_id
        date_str = datetime.now().strftime(self.report_cfg.get("date_format", "%Y-%m-%d"))

        p1 = _safe_float(row.get("p1_score", "")) or 0.0
        p2 = _safe_float(row.get("p2_score", "")) or 0.0
        combined = _safe_float(row.get("combined_score", "")) or 0.0
        call1 = _safe_float(row.get("call1_time_s", "")) or 0.0
        mcp_lat = _safe_float(row.get("mcp_latency_s", "")) or 0.0
        call2 = _safe_float(row.get("call2_time_s", "")) or 0.0
        total_t = _safe_float(row.get("total_time_s", "")) or 0.0
        total_tok = _safe_int(row.get("total_tokens", 0))
        cost_str = row.get("cost_usd") or "0.0"
        tool_call_valid = row.get("tool_call_valid", "false")
        attempts = row.get("tool_call_attempts", "1")
        parse_error = row.get("retry_required", "false")
        hallucination = row.get("hallucination_flag", "false")

        lines: list[str] = []
        lines.append(f"# Tool Use Review — {display_name}")
        lines.append(
            f"**Generated:** {date_str} | "
            f"**MCP Mode:** {row.get('mcp_mode', 'n/a')} | "
            f"**Assets Run:** {row.get('assets_run', 'n/a')}",
        )
        lines.append("")

        # Score Overview
        lines.append("## Score Overview")
        lines.append("| Metric | Score | Rating |")
        lines.append("|---|---|---|")
        lines.append(f"| Tool Execution (P1) | {p1:.2f} | {self._get_score_label(p1)} |")
        lines.append(f"| Synthesis Quality (P2) | {p2:.2f} | {self._get_score_label(p2)} |")
        lines.append(f"| **Combined Score** | **{combined:.2f}** | **{self._get_score_label(combined)}** |")
        lines.append("")

        # Performance
        lines.append("## Performance")
        lines.append("| Metric | Value |")
        lines.append("|---|---|")
        lines.append(f"| Tool-Call Time (Ø) | {call1:.2f}s |")
        lines.append(f"| MCP Latency (Ø) | {mcp_lat:.2f}s |")
        lines.append(f"| Synthesis Time (Ø) | {call2:.2f}s |")
        lines.append(f"| **Total Time** | **{total_t:.2f}s** |")
        lines.append(f"| Total Tokens | {total_tok} |")
        lines.append(f"| Estimated Cost | ${cost_str} |")
        lines.append("")

        # Reliability
        lines.append("## Reliability")
        lines.append(f"- **Tool Call Valid:** {tool_call_valid}")
        lines.append(f"- **Parse Errors:** {parse_error} ({attempts} attempts)")
        lines.append(f"- **Hallucination Flag:** {hallucination}")
        lines.append("")

        # Anomaly callouts — must use GitHub Alert syntax for generate_review.py regex pickup
        # Count assets with hard parse-error (tool call never parsed, not just retried)
        parse_error_asset_ids = [
            a["asset_id"] for a in asset_details
            if (a.get("data", {}).get("tool_transcript") or {}).get("status") in ("parse_error", "blocked")
        ]
        tool_call_valid_bool = str(tool_call_valid).lower() == "true"

        if str(hallucination).lower() == "true":
            lines.append("> [!WARNING]")
            lines.append("> **Halluzination erkannt — Hard Fail:** Das Modell hat auf mindestens einem Asset Inhalte")
            lines.append("> generiert, die nicht aus dem abgerufenen Tool-Ergebnis stammen, sondern erfunden wurden")
            lines.append("> (`hallucination_flag: true`). Für content-kritische Produktions-Tasks (Recherche,")
            lines.append("> Dokumentenzusammenfassung, faktenbasierte Berichte) ist dieses Verhalten ein")
            lines.append("> disqualifizierendes Signal. Der Score unterschätzt möglicherweise das Risiko.")
            lines.append("")

        if str(parse_error).lower() == "true":
            if not tool_call_valid_bool and len(parse_error_asset_ids) >= 2:
                lines.append("> [!CAUTION]")
                lines.append("> **Proprietäres Tool-Call-Format:** Das Modell erzeugt statt des CrucibleMark-Custom-JSON-Schemas")
                lines.append("> ein natives, modellspezifisches Tool-Call-Format (z. B. `{\"tool_call\": {\"name\": ...,")
                lines.append("> \"parameters\": ...}}`), das vom MCP-Stack nicht geparst werden kann. Im Benchmark-Kontext")
                lines.append(f"> ist das Modell auf {len(parse_error_asset_ids)}/6 Assets nicht MCP-kompatibel (betroffen:")
                lines.append(f"> {', '.join(parse_error_asset_ids)}). Über die native Modell-API (SDK-Level) ist das Modell")
                lines.append("> vollständig tool-use-fähig — das Problem ist ein Benchmark-Artefakt.")
                lines.append("")
            else:
                lines.append("> [!NOTE]")
                lines.append("> **Retry erforderlich:** Das Modell benötigte auf mindestens einem Asset einen zweiten")
                lines.append("> Versuch, um einen validen Tool-Call im CrucibleMark-Custom-JSON-Schema zu erzeugen")
                lines.append("> (`retry_required: true`). P1 misst das Ergebnis nach erfolgtem Tool-Call — der Retry")
                lines.append("> erhöht Token-Verbrauch und Latenz, beeinflusst aber P1 nicht direkt.")
                lines.append("")

        # Synthesis Gap: strong P1 but very weak P2
        if p1 >= 70.0 and p2 < 35.0:
            _gap = p1 - p2
            lines.append("> [!CAUTION]")
            lines.append(f"> **Synthesis-Gap erkannt ({_gap:.0f} Punkte):** Das Modell führt Tool-Calls zuverlässig")
            lines.append(f"> aus (P1={p1:.1f}), kann die abgerufenen Ergebnisse aber nicht in eine kohärente")
            lines.append(f"> Antwort übersetzen (P2={p2:.1f}). In produktiven Agentic-Workflows reicht ein valider")
            lines.append("> Tool-Call allein nicht aus — die Synthesequalität ist der eigentliche Bottleneck.")
            lines.append("")

        # Judge Fallback: P2 scores are less reliable
        judge_fallback_assets = [
            a["asset_id"] for a in asset_details
            if a.get("data", {}).get("judge_fallback")
        ]
        if judge_fallback_assets:
            lines.append("> [!NOTE]")
            lines.append("> **LLM-Judge nicht verfügbar — P2 aus Regellogik:** Für dieses Modell konnte der")
            lines.append("> LLM-Judge auf mindestens einem Asset nicht erreicht werden. P2-Scores wurden durch")
            lines.append("> die regelbasierte Fallback-Logik ermittelt, die Nuancen in Synthesequalität und")
            lines.append("> Content-Grounding weniger präzise erfasst als ein LLM-Judge.")
            lines.append(f"> Betroffen: {', '.join(judge_fallback_assets)}. P2-Vergleiche mit anderen Modellen")
            lines.append("> sollten mit Vorbehalt interpretiert werden.")
            lines.append("")

        # Asset Breakdown
        asset_by_id = {a["asset_id"]: a for a in asset_details}
        lines.append("## Asset Breakdown")
        lines.append("| Asset | Name | P1 | P2 | Combined | Tool Call | Notes |")
        lines.append("|---|---|---|---|---|---|---|")
        for asset_id, asset_name in _ASSET_NAMES.items():
            a = asset_by_id.get(asset_id)
            if a:
                d = a.get("data", {})
                a_p1 = _safe_float(d.get("p1_score", "")) or 0.0
                a_p2 = _safe_float(d.get("p2_score", "")) or 0.0
                a_combined = _safe_float(d.get("combined_score", "")) or 0.0
                tc = d.get("tool_transcript") or {}
                tc_valid = "✓" if tc.get("status") not in ("parse_error", "blocked", None, "") else "✗"
                _notes_parts = []
                if d.get("hallucination_flag"):
                    _notes_parts.append("⚠ Halluzination")
                if tc.get("status") == "parse_error":
                    _notes_parts.append("✗ Parse-Fehler")
                _cv = (d.get("content_verification") or {}).get("state", "")
                if _cv == "C":
                    _notes_parts.append("✗ Kein Tool-Call")
                elif (d.get("content_verification") or {}).get("tool_result_ignored"):
                    _notes_parts.append("B2: Tool ignoriert")
                notes = ", ".join(_notes_parts)
                lines.append(f"| {asset_id} | {asset_name} | {a_p1:.1f} | {a_p2:.1f} | {a_combined:.1f} | {tc_valid} | {notes} |")
            else:
                lines.append(f"| {asset_id} | {asset_name} | — | — | — | — | Nicht ausgeführt |")
        lines.append("")

        # Tool Call Transcripts
        lines.append("## Tool Call Transcripts")
        lines.append("")
        for asset_id, asset_name in _ASSET_NAMES.items():
            lines.append(f"### {asset_id} — {asset_name}")
            a = asset_by_id.get(asset_id)
            if not a:
                lines.append("_Nicht ausgeführt._")
                lines.append("")
                continue

            d = a.get("data", {})
            transcript = d.get("tool_transcript") or {}
            response_1 = d.get("response_1", "")
            synthesis = a.get("raw_response", "")
            a_p1 = _safe_float(d.get("p1_score", "")) or 0.0
            a_p2 = _safe_float(d.get("p2_score", "")) or 0.0
            a_combined = _safe_float(d.get("combined_score", "")) or 0.0

            lines.append("**Model Tool Call (Response 1):**")
            lines.append("```json")
            lines.append(response_1[:400] if response_1 else "(kein Tool-Call)")
            lines.append("```")
            lines.append("")

            lines.append("**MCP Result:**")
            lines.append(f"- Status: {transcript.get('status', 'n/a')} | Provider: {transcript.get('provider', 'n/a')}")
            results_list = transcript.get("results", [])
            if results_list and isinstance(results_list, list):
                first = results_list[0] if results_list else {}
                source_url = first.get("url", "n/a")
                excerpt = str(first.get("excerpt", first.get("content", "")))[:300]
                lines.append(f"- Source: {source_url}")
                lines.append(f"- Excerpt: _{excerpt}_")
            elif transcript.get("content_excerpt"):
                lines.append(f"- Content: _{str(transcript.get('content_excerpt', ''))[:300]}_")
            elif transcript.get("status") == "error":
                lines.append(f"- Error: {transcript.get('error', 'n/a')}")
            lines.append("")

            if synthesis:
                lines.append("**Model Synthesis (Response 2, gekürzt):**")
                lines.append(f"> {synthesis[:400]}...")
                lines.append("")

            lines.append(f"**Scores:** P1={a_p1:.1f} | P2={a_p2:.1f} | Combined={a_combined:.1f}")
            lines.append("")

        # Assessment
        strengths = self._build_strengths(row, asset_details)
        weaknesses = self._build_weaknesses(row)
        recommendation = self._build_deployment_recommendation(row)

        lines.append("## Assessment")
        lines.append("")
        lines.append("**Strengths:**")
        for s in strengths or ["Keine signifikanten Stärken identifiziert"]:
            lines.append(f"- {s}")
        lines.append("")
        lines.append("**Weaknesses:**")
        for w in weaknesses or ["Keine signifikanten Schwächen identifiziert"]:
            lines.append(f"- {w}")
        lines.append("")
        lines.append(f"**Deployment Recommendation:** {recommendation}")
        lines.append("")

        # Methodology notes — deterministic context annotations for reviewers
        methodology_notes = get_applicable_notes(row)
        if methodology_notes:
            lines.append("## Methodologische Anmerkungen")
            lines.append("")
            lines.append(
                "_Die folgenden Hinweise wurden automatisch aus den Benchmark-Daten abgeleitet._"
                " _Sie erläutern strukturelle Benchmark-Bedingungen und sollen Reviewern_"
                " _helfen, Scores korrekt zu interpretieren._"
            )
            lines.append("")
            for note in methodology_notes:
                lines.append(note.render_markdown())
                lines.append("")

        lines.append("---")
        lines.append("*CrucibleMark Tool Use Module v1.0 — Statischer Report*")

        return "\n".join(lines)

    def generate_fleet_summary(self) -> str:
        """Generate Markdown fleet summary string."""
        df = self.load_leaderboard()
        date_str = datetime.now().strftime(self.report_cfg.get("date_format", "%Y-%m-%d"))
        total_models = len(df)

        lines: list[str] = []
        lines.append("# CrucibleMark Tool Use — Fleet Summary")
        lines.append(f"**Generated:** {date_str} | **Models Evaluated:** {total_models}")
        lines.append("")

        if df.empty:
            lines.append("_Keine Modelle im Leaderboard._")
            return "\n".join(lines)

        # Leaderboard table (sorted by combined_score desc)
        score_labels = self.report_cfg.get("score_labels", {})

        def _tier(row: dict[str, Any]) -> str:
            cs = _safe_float(row.get("combined_score", "")) or 0.0
            return _score_label(cs, score_labels)

        lines.append("## Leaderboard")
        lines.append("| Model | Tier | P1 | P2 | Combined | ToolCall | Time | Mode | Group |")
        lines.append("|---|---|---|---|---|---|---|---|---|")

        sorted_df = df.copy()
        sorted_df["_cs_sort"] = sorted_df["combined_score"].apply(
            lambda v: _safe_float(v) or -1.0,
        )
        sorted_df = sorted_df.sort_values("_cs_sort", ascending=False)

        for _, r in sorted_df.iterrows():
            row = r.to_dict()
            cs = _safe_float(row.get("combined_score", "")) or 0.0
            tier = _tier(row)
            p1_v = row.get("p1_score", "—")
            p2_v = row.get("p2_score", "—")
            tc = row.get("tool_call_valid", "—")
            tt = row.get("total_time_s", "—")
            mode = row.get("mcp_mode", "—")
            grp = row.get("fleet_group", "—")
            disp = row.get("display_name") or row.get("model", "—")
            lines.append(f"| {disp} | {tier} | {p1_v} | {p2_v} | {cs:.2f} | {tc} | {tt} | {mode} | {grp} |")
        lines.append("")

        # Sovereignty Gap
        local_rows = df[df.get("fleet_group", pd.Series()) == "local_sovereign"] if "fleet_group" in df.columns else pd.DataFrame()
        all_combined = [_safe_float(v) for v in df.get("combined_score", pd.Series())]
        all_combined = [v for v in all_combined if v is not None]
        local_combined = [
            _safe_float(v) for v in local_rows.get("combined_score", pd.Series())
        ] if not local_rows.empty else []
        local_combined = [v for v in local_combined if v is not None]

        avg_all = round(sum(all_combined) / len(all_combined), 2) if all_combined else None
        avg_local = round(sum(local_combined) / len(local_combined), 2) if local_combined else None
        gap = round(avg_all - avg_local, 2) if avg_all is not None and avg_local is not None else None

        lines.append("## Sovereignty Gap Analysis")
        lines.append("| Metric | Value |")
        lines.append("|---|---|")
        lines.append(f"| Fleet Avg — Local Sovereign | {avg_local if avg_local is not None else 'n/a'} |")
        lines.append(f"| Fleet Avg — Full Fleet | {avg_all if avg_all is not None else 'n/a'} |")
        lines.append(f"| **Sovereignty Gap** | **{gap if gap is not None else 'n/a'}** |")
        lines.append("")

        if gap is not None:
            if gap < 5:
                interp = "Lokale Modelle erreichen vergleichbare Tool-Use-Kompetenz."
            elif gap <= 15:
                interp = "Moderate Lücke — lokale Modelle für Basis-Tool-Use geeignet."
            else:
                interp = "Signifikante Lücke — kommerzielle Modelle klar überlegen."
            lines.append(f"_{interp}_")
            lines.append("")

        # Performance stats per group
        for grp_label, grp_df in [("Local Sovereign", local_rows), ("All Models", df)]:
            if grp_df.empty:
                continue
            rows_dicts = [r.to_dict() for _, r in grp_df.iterrows()]
            scores_p1 = [_safe_float(r.get("p1_score", "")) for r in rows_dicts]
            scores_p1 = [v for v in scores_p1 if v is not None]
            scores_p2 = [_safe_float(r.get("p2_score", "")) for r in rows_dicts]
            scores_p2 = [v for v in scores_p2 if v is not None]
            scores_cs = [_safe_float(r.get("combined_score", "")) for r in rows_dicts]
            scores_cs = [v for v in scores_cs if v is not None]
            times = [_safe_float(r.get("total_time_s", "")) for r in rows_dicts]
            times = [v for v in times if v is not None]
            tokens = [_safe_int(r.get("total_tokens", 0)) for r in rows_dicts]

            def _stats(lst: list[float]) -> str:
                if not lst:
                    return "n/a | n/a | n/a"
                return f"{sum(lst)/len(lst):.2f} | {min(lst):.2f} | {max(lst):.2f}"

            lines.append(f"## Performance Overview ({grp_label})")
            lines.append("| Metric | Avg | Min | Max |")
            lines.append("|---|---|---|---|")
            lines.append(f"| P1 Score | {_stats(scores_p1)} |")
            lines.append(f"| P2 Score | {_stats(scores_p2)} |")
            lines.append(f"| Combined Score | {_stats(scores_cs)} |")
            lines.append(f"| Total Time (s) | {_stats(times)} |")
            avg_tok = int(sum(tokens) / len(tokens)) if tokens else 0
            lines.append(f"| Total Tokens | {avg_tok} | {min(tokens) if tokens else 0} | {max(tokens) if tokens else 0} |")
            lines.append("")

        # Reliability overview
        total = len(df)
        valid_count = int(df.get("tool_call_valid", pd.Series()).apply(lambda v: str(v).lower() == "true").sum()) if "tool_call_valid" in df.columns else 0
        parse_count = int(df.get("retry_required", pd.Series()).apply(lambda v: str(v).lower() == "true").sum()) if "retry_required" in df.columns else 0
        halluc_count = int(df.get("hallucination_flag", pd.Series()).apply(lambda v: str(v).lower() == "true").sum()) if "hallucination_flag" in df.columns else 0

        lines.append("## Reliability Overview")
        lines.append(f"- Models with valid tool calls: {valid_count}/{total}")
        lines.append(f"- Models requiring MCP-format retry: {parse_count}/{total}")
        lines.append(f"- Models with hallucination flag: {halluc_count}/{total}")
        lines.append("")

        # Methodology notes — fleet-level summary of triggered annotations
        lines.append("## Methodologische Anmerkungen (Fleet)")
        lines.append("")
        fleet_note_counts: dict[str, int] = {}
        for _, r in sorted_df.iterrows():
            for note in get_applicable_notes(r.to_dict()):
                fleet_note_counts[note.tag] = fleet_note_counts.get(note.tag, 0) + 1
        if fleet_note_counts:
            lines.append("| Annotation | Modelle betroffen |")
            lines.append("|---|---|")
            for tag, count in sorted(fleet_note_counts.items(), key=lambda x: -x[1]):
                lines.append(f"| `{tag}` | {count}/{total} |")
        else:
            lines.append("_Keine methodologischen Anmerkungen ausgelöst._")
        lines.append("")

        # Deployment recommendations
        lines.append("## Deployment Recommendations")
        for _, r in sorted_df.iterrows():
            row = r.to_dict()
            disp = row.get("display_name") or row.get("model", "—")
            rec = _build_deployment_recommendation(row)
            lines.append(f"- **{disp}:** {rec}")
        lines.append("")
        lines.append("---")
        lines.append("*CrucibleMark Tool Use Module v1.0*")

        return "\n".join(lines)

    def generate_web_json(self, model_id: str) -> dict[str, Any]:
        """Build tooluse_data.json dict for web export."""
        df = self.load_leaderboard()
        row: dict[str, Any] = {}
        if not df.empty and "model" in df.columns:
            matching = df[df["model"] == model_id]
            if not matching.empty:
                row = matching.iloc[0].to_dict()

        asset_details = self.load_asset_details(model_id)
        date_str = datetime.now().strftime(self.report_cfg.get("date_format", "%Y-%m-%d"))

        combined = _safe_float(row.get("combined_score", "")) or 0.0
        score_labels = self.report_cfg.get("score_labels", {})

        assets_out: list[dict[str, Any]] = []
        for a in asset_details:
            d = a.get("data", {})
            tc = d.get("tool_transcript") or {}
            results_list = tc.get("results", [])
            first_result = results_list[0] if (results_list and isinstance(results_list, list)) else {}
            tc_valid = tc.get("status") not in ("parse_error", "blocked", None, "")
            tool_call_parsed = d.get("tool_call_parsed") or {}
            assets_out.append({
                "id": a.get("asset_id", ""),
                "name": _ASSET_NAMES.get(a.get("asset_id", ""), a.get("asset_id", "")),
                "p1": _safe_float(d.get("p1_score", "")),
                "p2": _safe_float(d.get("p2_score", "")),
                "combined": _safe_float(d.get("combined_score", "")),
                "tool_call_valid": tc_valid,
                "tool_call_json": json.dumps({"tool_call": tool_call_parsed}, ensure_ascii=False) if tool_call_parsed else "",
                "mcp_status": tc.get("status", ""),
                "mcp_provider": tc.get("provider", ""),
                "source_url": first_result.get("url", ""),
                "excerpt": str(first_result.get("excerpt", first_result.get("content", "")))[:300],
                "synthesis_excerpt": a.get("raw_response", "")[:400],
            })

        strengths = _build_strengths(row, asset_details)
        weaknesses = _build_weaknesses(row)
        recommendation = _build_deployment_recommendation(row)

        gap_val = _safe_float(row.get("sovereignty_gap", ""))

        return {
            "model_id": model_id,
            "display_name": row.get("display_name") or model_id,
            "generated": date_str,
            "mcp_mode": row.get("mcp_mode", ""),
            "scores": {
                "p1": _safe_float(row.get("p1_score", "")),
                "p2": _safe_float(row.get("p2_score", "")),
                "combined": combined,
                "rating": _score_label(combined, score_labels),
            },
            "performance": {
                "call1_time_s": _safe_float(row.get("call1_time_s", "")),
                "mcp_latency_s": _safe_float(row.get("mcp_latency_s", "")),
                "call2_time_s": _safe_float(row.get("call2_time_s", "")),
                "total_time_s": _safe_float(row.get("total_time_s", "")),
                "total_tokens": _safe_int(row.get("total_tokens", 0)),
                "cost_usd": _safe_float(row.get("cost_usd", "")) or 0.0,
            },
            "reliability": {
                "tool_call_valid": str(row.get("tool_call_valid", "false")).lower() == "true",
                "tool_call_attempts": _safe_int(row.get("tool_call_attempts", 1)),
                "retry_required": str(row.get("retry_required", "false")).lower() == "true",
                "hallucination_flag": str(row.get("hallucination_flag", "false")).lower() == "true",
            },
            "fleet_group": row.get("fleet_group", ""),
            "sovereignty_gap": gap_val,
            "assets": assets_out,
            "assessment": {
                "strengths": strengths,
                "weaknesses": weaknesses,
                "deployment_recommendation": recommendation,
            },
        }

    # ------------------------------------------------------------------
    # File I/O
    # ------------------------------------------------------------------

    def save_model_report(self, model_id: str) -> Path:
        """Write docs/reviews/<slug>/tooluse_review_<date>.md."""
        content = self.generate_model_report(model_id)
        slug = _slugify(model_id)
        out_dir = self.root / "docs" / "reviews" / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now().strftime("%Y%m%d")
        path = out_dir / f"tooluse_review_{date_str}.md"
        path.write_text(content, encoding="utf-8")
        return path

    def save_fleet_summary(self) -> Path:
        """Write benchmark_scores/reports/tooluse_summary_<date>.md."""
        content = self.generate_fleet_summary()
        out_dir = self.root / "benchmark_scores" / "reports"
        out_dir.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now().strftime("%Y%m%d")
        path = out_dir / f"tooluse_summary_{date_str}.md"
        path.write_text(content, encoding="utf-8")
        return path

    def save_web_json(self, model_id: str) -> Path:
        """Write web_export/models/<slug>/tooluse_data.json."""
        data = self.generate_web_json(model_id)
        slug = _slugify(model_id)
        out_dir = self.root / "web_export" / "models" / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "tooluse_data.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return path


# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------

def _load_config() -> dict[str, Any]:
    config_path = _ROOT / "config" / "tooluse_report_config.yaml"
    try:
        return yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except Exception as exc:  # noqa: BLE001 — yaml/filesystem boundary
        logger.warning("Could not load report config: %s", exc)
        return {}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="CrucibleMark Tool Use Report Generator")
    parser.add_argument("--model", default=None, help="Generate report for a single model ID")
    parser.add_argument("--summary-only", action="store_true", help="Only write fleet summary")
    parser.add_argument("--json-only", action="store_true", help="Only write web JSON files")
    args = parser.parse_args()

    config = _load_config()
    generator = ToolUseReportGenerator(config)

    if args.summary_only:
        path = generator.save_fleet_summary()
        print(f"Fleet Summary: {path}")
        return

    df = generator.load_leaderboard()
    if df.empty:
        print("No tooluse data found in leaderboard.")
        if not args.json_only:
            path = generator.save_fleet_summary()
            print(f"Fleet Summary (empty): {path}")
        return

    models: list[str] = (
        [args.model] if args.model else list(df["model"].dropna().unique())
    )

    for model_id in models:
        if "model" in df.columns and not (df["model"] == model_id).any():
            print(f"  Warning: {model_id} not found in leaderboard — skipping")
            continue

        if not args.json_only:
            path = generator.save_model_report(model_id)
            print(f"  Report: {path}")

        path = generator.save_web_json(model_id)
        print(f"  JSON:   {path}")

    if not args.json_only and not args.model:
        path = generator.save_fleet_summary()
        print(f"Fleet Summary: {path}")


if __name__ == "__main__":
    main()
