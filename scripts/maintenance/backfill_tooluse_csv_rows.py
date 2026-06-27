"""Backfill ToolUse Per-Asset-Detailzeilen in Benchmark-CSVs aus Audit-Logs.

Problem (v4.10.12):
    39 Modelle wurden mit einer älteren Runner-Version getestet, die Pfad A
    (``ToolUseExporter.export_result()`` + ``finalize_model()``) nutzte.
    Dieser Pfad schreibt nur in ``tooluse_leaderboard.csv`` (aggregiert),
    nicht in die Benchmark-CSVs (``local/cloud/commercial_models_benchmark.csv``).
    Dadurch fehlen die Per-Asset-Detailzeilen (``tooluse001``–``tooluse006``)
    und der Web-Export zeigt ``tooluse.assets: []``.

Lösung:
    Dieses Script liest die Audit-Logs (``outputs/audit_logs/<model>/tooluse00*.md``),
    extrahiert das ``score_contributions``-Dict (Raw JSON) und schreibt die
    Per-Asset-Zeilen via ``ResultManager.save_results()`` (atomarer Upsert)
    in die Benchmark-CSVs. Danach wird ``aggregate_from_benchmark_csvs()``
    aufgerufen, um das Leaderboard zu re-aggregieren.

Usage:
    python scripts/maintenance/backfill_tooluse_csv_rows.py [--dry-run] [--model ID]
    python scripts/maintenance/backfill_tooluse_csv_rows.py --list  # nur betroffene Modelle listen
"""
from __future__ import annotations

import argparse
import ast
import csv
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.config_validator import ConfigValidator  # noqa: E402
from utils.model_utils import _safe_name, resolve_canonical_model_id  # noqa: E402
from scripts.core.tooluse_exporter import ToolUseExporter  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

_BENCHMARK_CSVS = [
    ROOT / "benchmark_scores" / "local_models_benchmark.csv",
    ROOT / "benchmark_scores" / "cloud_models_benchmark.csv",
    ROOT / "benchmark_scores" / "commercial_models_benchmark.csv",
]

_ASSET_NAMES: dict[str, str] = {
    "tooluse001": "Llama 4 EU License Research (Honeypot)",
    "tooluse002": "HTTP Fetch & Extract",
    "tooluse003": "Tool Failure Handling",
    "tooluse004": "Tool Selection (web_search)",
    "tooluse005": "URL Construction (fetch)",
    "tooluse006": "Multilingual Search & German Synthesis",
}

_ASSET_TIERS: dict[str, int] = {
    "tooluse001": 2,
    "tooluse002": 2,
    "tooluse003": 3,
    "tooluse004": 2,
    "tooluse005": 2,
    "tooluse006": 2,
}

# Regex für Audit-Log-Header
_RE_CREATED = re.compile(r"Erstellt am:\*\*\s*(\d{2}\.\d{2}\.\d{4}),\s*(\d{2}:\d{2}:\d{2})")
_RE_MODEL = re.compile(r"\*\*Model:\*\*\s*(.+)")
_RE_PROVIDER = re.compile(r"\*\*Provider:\*\*\s*(.+)")
_RE_EXEC_TIME = re.compile(r"\*\*Execution Time:\*\*\s*([\d.]+)\s*s")
_RE_TOKENS = re.compile(r"\*\*Tokens Used:\*\*\s*(\d+)")
_RE_COST = re.compile(r"\*\*Cost:\*\*\s*\$([\d.]+)")
_RE_RAW_JSON = re.compile(r"\*\*Raw JSON:\*\*\n```json\n(.*?)\n```", re.DOTALL)


def _find_models_missing_detail_rows() -> list[str]:
    """Findet alle Modelle in tooluse_leaderboard.csv ohne Detailzeilen in Benchmark-CSVs."""
    lb_path = ROOT / "benchmark_scores" / "tooluse_leaderboard.csv"
    if not lb_path.exists():
        return []

    lb_models: set[str] = set()
    with lb_path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            mid = row.get("model", "")
            if mid:
                lb_models.add(resolve_canonical_model_id(mid))

    detail_models: set[str] = set()
    for csv_path in _BENCHMARK_CSVS:
        if not csv_path.exists():
            continue
        with csv_path.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                if str(row.get("asset_id", "")).startswith("tooluse"):
                    mid = row.get("model", "")
                    if mid:
                        detail_models.add(resolve_canonical_model_id(mid))

    return sorted(lb_models - detail_models)


def _parse_audit_log(filepath: Path) -> dict[str, Any] | None:
    """Extrahiert strukturierte Daten aus einem ToolUse-Audit-Log."""
    try:
        content = filepath.read_text(encoding="utf-8")
    except OSError:
        return None

    # Header-Felder
    m_created = _RE_CREATED.search(content)
    m_model = _RE_MODEL.search(content)
    m_provider = _RE_PROVIDER.search(content)
    m_exec = _RE_EXEC_TIME.search(content)
    m_tokens = _RE_TOKENS.search(content)
    m_cost = _RE_COST.search(content)

    # Raw JSON (score_contributions Dict)
    m_raw = _RE_RAW_JSON.search(content)
    if not m_raw:
        log.warning("  Kein Raw JSON Block in %s", filepath.name)
        return None

    try:
        raw_dict = json.loads(m_raw.group(1))
    except json.JSONDecodeError as exc:
        log.warning("  Raw JSON Parse-Fehler in %s: %s", filepath.name, exc)
        return None

    # Timestamp: DD.MM.YYYY, HH:MM:SS → ISO-Format
    timestamp = ""
    if m_created:
        date_str, time_str = m_created.group(1), m_created.group(2)
        d, m, y = date_str.split(".")
        timestamp = f"{y}-{m}-{d} {time_str}+00:00"

    return {
        "asset_id": raw_dict.get("asset_id", filepath.stem),
        "model": m_model.group(1).strip() if m_model else "",
        "provider": m_provider.group(1).strip() if m_provider else "",
        "timestamp": timestamp,
        "execution_time": float(m_exec.group(1)) if m_exec else 0.0,
        "tokens_used": int(m_tokens.group(1)) if m_tokens else 0,
        "cost_usd": float(m_cost.group(1)) if m_cost else 0.0,
        "raw_dict": raw_dict,
        "p1_score": raw_dict.get("p1_score"),
        "p2_score": raw_dict.get("p2_score"),
        "combined_score": raw_dict.get("combined_score"),
        "call1_time_s": raw_dict.get("call1_time_s"),
        "call2_time_s": raw_dict.get("call2_time_s"),
        "total_time_s": raw_dict.get("total_time_s"),
        "call1_tokens": raw_dict.get("call1_tokens"),
        "call2_tokens": raw_dict.get("call2_tokens"),
        "total_tokens": raw_dict.get("total_tokens"),
        "mcp_latency_s": raw_dict.get("mcp_latency_s"),
        "tool_call_attempts": raw_dict.get("tool_call_attempts"),
        "retry_required": raw_dict.get("retry_required"),
        "hallucination_flag": raw_dict.get("hallucination_flag"),
        "tool_call_parsed": raw_dict.get("tool_call_parsed"),
        "tool_transcript": raw_dict.get("tool_transcript"),
        "response_1": raw_dict.get("response_1"),
        "content_verification": raw_dict.get("content_verification"),
        "tool_content_state": raw_dict.get("tool_content_state"),
        "pipeline_diagnostic": raw_dict.get("pipeline_diagnostic"),
        "llm_judge": raw_dict.get("llm_judge"),
    }


def _build_csv_row(parsed: dict[str, Any], model_version: str) -> dict[str, Any]:
    """Baut eine Benchmark-CSV-Zeile aus den geparsten Audit-Log-Daten."""
    aid = parsed["asset_id"]
    combined = parsed.get("combined_score")
    combined_f = float(combined) if combined is not None else 0.0

    # score_contributions als Python-Dict-String (wie unified_runner es schreibt)
    score_contributions = repr(parsed["raw_dict"])

    transcript = parsed.get("tool_transcript") or {}
    status = "success" if transcript.get("status") == "success" else "error"

    row: dict[str, Any] = {
        "asset_id": aid,
        "asset_name": _ASSET_NAMES.get(aid, aid),
        "cost_usd": str(parsed.get("cost_usd", 0.0)),
        "execution_time": str(parsed.get("execution_time", 0.0)),
        "finish_reason": "stop",
        "load_time": "0.0",
        "max_score": "100.0",
        "model": parsed["model"],
        "model_version": model_version,
        "percentage": str(combined_f),
        "provider": parsed["provider"],
        "response_length": str(parsed.get("total_tokens", 0)),
        "run_id": "backfill_v4.10.12",
        "score_contributions": score_contributions,
        "status": status,
        "tier": f"Tier {_ASSET_TIERS.get(aid, 2)}",
        "timestamp": parsed["timestamp"],
        "token_limit_cutoff": "False",
        "token_limit_fallback": "False",
        "token_limit_used": "4096.0",
        "tokens_per_second": "0.0",
        "tokens_used": str(parsed.get("total_tokens", parsed.get("tokens_used", 0))),
        "total_score": str(combined_f),
        # ToolUse Flat-Columns
        "p1_score": str(parsed.get("p1_score", "")) if parsed.get("p1_score") is not None else "",
        "p2_score": str(parsed.get("p2_score", "")) if parsed.get("p2_score") is not None else "",
        "combined_score": str(combined) if combined is not None else "",
        "call1_time_s": str(parsed.get("call1_time_s", "")) if parsed.get("call1_time_s") is not None else "",
        "call2_time_s": str(parsed.get("call2_time_s", "")) if parsed.get("call2_time_s") is not None else "",
        "total_time_s": str(parsed.get("total_time_s", "")) if parsed.get("total_time_s") is not None else "",
        "call1_tokens": str(parsed.get("call1_tokens", "")) if parsed.get("call1_tokens") is not None else "",
        "call2_tokens": str(parsed.get("call2_tokens", "")) if parsed.get("call2_tokens") is not None else "",
        "mcp_latency_s": str(parsed.get("mcp_latency_s", "")) if parsed.get("mcp_latency_s") is not None else "",
        "tool_call_attempts": str(parsed.get("tool_call_attempts", "")) if parsed.get("tool_call_attempts") is not None else "",
        "hallucination_flag": str(parsed.get("hallucination_flag", "")) if parsed.get("hallucination_flag") is not None else "",
        "reasoning_tokens": "",
        "think_content": "",
        "refusal_flag": "",
        "hardware_profile": "",
    }
    return row


def _get_model_version(model_id: str) -> str:
    """Liest model_version aus der Model-Card."""
    card_dir = ROOT / "benchmark_scores" / "model_cards"
    target_canonical = resolve_canonical_model_id(model_id)
    for card_path in sorted(card_dir.glob("*.json")):
        try:
            card = json.loads(card_path.read_text(encoding="utf-8"))
            if not isinstance(card, dict):
                continue
            card_mid = card.get("model_id", "")
            if resolve_canonical_model_id(card_mid) == target_canonical:
                return card.get("model_version") or "unknown"
        except (json.JSONDecodeError, OSError):
            continue
    return "unknown"


def _backfill_model(
    model_id: str,
    result_manager: Any,
    dry_run: bool,
) -> tuple[int, int]:
    """Backfill ein Modell. Returns (written, skipped)."""
    canonical = resolve_canonical_model_id(model_id)
    slug = _safe_name(canonical)
    audit_dir = ROOT / "outputs" / "audit_logs" / slug

    if not audit_dir.exists():
        log.warning("  Audit-Dir fehlt: %s", audit_dir)
        return (0, 0)

    model_version = _get_model_version(canonical)
    written = 0
    skipped = 0

    for aid in ("tooluse001", "tooluse002", "tooluse003", "tooluse004", "tooluse005", "tooluse006"):
        audit_file = audit_dir / f"{aid}.md"
        if not audit_file.exists():
            log.debug("  %s fehlt — überspringe", audit_file.name)
            skipped += 1
            continue

        parsed = _parse_audit_log(audit_file)
        if parsed is None:
            skipped += 1
            continue

        # Model-ID überschreiben mit kanonischer Form (falls Audit-Log abweicht)
        parsed["model"] = model_id

        row = _build_csv_row(parsed, model_version)

        if dry_run:
            log.info("  [DRY-RUN] würde schreiben: %s/%s p1=%s p2=%s combined=%s",
                     model_id, aid, row.get("p1_score"), row.get("p2_score"), row.get("combined_score"))
            written += 1
        else:
            try:
                result_manager.save_results([row])
                log.info("  ✓ %s/%s → p1=%s p2=%s combined=%s",
                         model_id, aid, row.get("p1_score"), row.get("p2_score"), row.get("combined_score"))
                written += 1
            except Exception as exc:
                log.error("  ✗ %s/%s → Fehler: %s", model_id, aid, exc)
                skipped += 1

    return (written, skipped)


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill ToolUse Per-Asset-Detailzeilen aus Audit-Logs")
    parser.add_argument("--dry-run", action="store_true", help="Nur anzeigen, nicht schreiben")
    parser.add_argument("--model", type=str, help="Nur dieses Modell backfillen (model_id)")
    parser.add_argument("--list", action="store_true", help="Nur betroffene Modelle listen")
    args = parser.parse_args()

    if args.list:
        models = _find_models_missing_detail_rows()
        log.info("Modelle mit fehlenden Detailzeilen (%d):", len(models))
        for m in models:
            log.info("  %s", m)
        return

    if args.model:
        target_models = [args.model]
    else:
        target_models = _find_models_missing_detail_rows()

    if not target_models:
        log.info("Keine Modelle mit fehlenden Detailzeilen gefunden — alles OK.")
        return

    log.info("═" * 60)
    log.info("  Backfill ToolUse Detailzeilen — %d Modell(e)", len(target_models))
    log.info("  Dry-Run: %s", "JA" if args.dry_run else "NEIN")
    log.info("═" * 60)

    # ResultManager initialisieren (nimmt ConfigValidator, nicht dict)
    config_validator = ConfigValidator()
    config = config_validator.config
    from utils.result_manager import ResultManager
    result_manager = ResultManager(config_validator)

    total_written = 0
    total_skipped = 0
    success_models: list[str] = []
    failed_models: list[str] = []

    for i, model_id in enumerate(target_models, 1):
        log.info("\n[%d/%d] %s", i, len(target_models), model_id)
        written, skipped = _backfill_model(model_id, result_manager, args.dry_run)
        total_written += written
        total_skipped += skipped
        if written > 0:
            success_models.append(model_id)
        if skipped > 0 and written == 0:
            failed_models.append(model_id)

    log.info("\n" + "═" * 60)
    log.info("  Backfill Complete")
    log.info("  Zeilen geschrieben: %d", total_written)
    log.info("  Zeilen übersprungen: %d", total_skipped)
    log.info("  Modelle erfolgreich: %d", len(success_models))
    if failed_models:
        log.info("  Modelle fehlgeschlagen: %d", len(failed_models))
        for m in failed_models:
            log.info("    - %s", m)
    log.info("═" * 60)

    # Leaderboard re-aggregieren (nur bei echtem Lauf)
    if not args.dry_run and success_models:
        log.info("\n→ Re-Aggregiere tooluse_leaderboard.csv aus Benchmark-CSVs...")
        try:
            exporter = ToolUseExporter(config)
            written = exporter.aggregate_from_benchmark_csvs(target_model_ids=success_models)
            log.info("  ✓ Leaderboard aktualisiert: %d Modell(e)", written)
        except Exception as exc:
            log.error("  ✗ Leaderboard-Update fehlgeschlagen: %s", exc)

    log.info("\nFertig.")


if __name__ == "__main__":
    main()
