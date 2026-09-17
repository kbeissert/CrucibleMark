#!/usr/bin/env python3
"""
Hermes Reasoning Report
=======================

Identifiziert den Denkvorgang des Hermes-Agent-Loops pro Benchmark-Task.

Der Gateway exportiert kein `reasoning`/`reasoning_content` und hebt
`session_reasoning_tokens` nicht ins Response-`usage` — er **persistiert** beides
aber in seiner State-DB. Dieses Skript joined die CrucibleMark-Ergebnisse auf
diese Sessions und weist pro Task aus: Reasoning-Tokens, Reasoning-Zeichen,
Anteil am Output, Loop-Runden (api_call_count), Prompt-Cache und versteckte
Auxiliary-Calls (z. B. title_generation).

Der Join ist ein **Seitenkanal** für Analyse und Reviewer-Kontext. Die Werte
werden bewusst nicht in die Ergebnis-CSV geschrieben — sie beschreiben nicht
das, was die gemessene Schnittstelle geliefert hat.

Usage:
    python scripts/analysis/hermes_reasoning_report.py --model qwen3_8-27b-nvfp4-hermes
    python scripts/analysis/hermes_reasoning_report.py --model ... --format json --out report.json
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# pylint: disable=wrong-import-position
from utils.config_validator import ConfigValidator  # noqa: E402
from utils.model_id_base import is_agentic_track_provider  # noqa: E402

CSV_PATH = ROOT_DIR / "benchmark_scores" / "local_models_benchmark.csv"
# Untergrenze für den Suffix-Join: kürzere Finale wären in anderen Antworten
# enthalten und würden falsch matchen (Mehr-Runden-Loops, siehe match_session).
MIN_SUFFIX_CHARS = 40
# Der Audit-Writer demmt Markdown-Überschriften im Antwortblock (`##` → `###`),
# damit die Abschnittsstruktur der Datei hält. Damit ist die DB-Nachricht nie
# wörtlich im Audit-Text enthalten, sobald eine Antwort Überschriften trägt.
# Der Antwort-Schluss bleibt unverändert → Heuristik über die letzten N Zeichen.
TAIL_MATCH_CHARS = 200
AUDIT_ROOT = ROOT_DIR / "outputs" / "audit_logs"
_TS_FMT = "%Y-%m-%d %H:%M:%S"


@dataclass
class SessionInfo:
    """Eine Hermes-Session mit ihren Reasoning-Spuren aus der State-DB."""

    session_id: str
    started_at: float
    output_tokens: int = 0
    input_tokens: int = 0
    reasoning_tokens: int = 0
    cache_read_tokens: int = 0
    api_calls: int = 0
    reasoning_chars: int = 0
    reasoning_msgs: int = 0
    final_content: str = ""
    aux_calls: int = 0
    aux_tokens: int = 0
    models: set[str] = field(default_factory=set)


def _die(msg: str) -> None:
    print(f"❌ {msg}")
    sys.exit(1)


def _resolve_db_path(db_arg: str | None, provider_cfg: dict[str, Any]) -> Path:
    """State-DB-Pfad: CLI-Argument schlägt provider_config (kein Hardcoding)."""
    raw = db_arg or provider_cfg.get("state_db")
    if not raw:
        _die("Kein state_db gesetzt — provider_config.hermes.state_db oder --db angeben.")
    path = Path(str(raw)).expanduser()
    if not path.exists():
        _die(f"State-DB nicht gefunden: {path}")
    return path


def _provider_cfg(config: dict[str, Any], provider: str) -> dict[str, Any]:
    for section in ("commercial", "local"):
        cfg = (config.get("providers", {}).get(section) or {}).get(provider)
        if isinstance(cfg, dict):
            return cfg
    return {}


def _hermes_model_for(config: dict[str, Any], model: str) -> str:
    """Gemappter Backend-Modellname der Entität (Sessions-Filter in der DB)."""
    for cfg in (config.get("providers", {}).get("commercial") or {}).values():
        if not is_agentic_track_provider(cfg):
            continue
        for entry in cfg.get("models") or []:
            if isinstance(entry, dict) and entry.get("id") == model:
                return str(entry.get("hermes_model") or "")
    return ""


def read_result_rows(model: str, csv_path: Path) -> list[dict[str, Any]]:
    """Ergebniszeilen der Entität, mit Zeitstempel als epoch für den Tiebreak."""
    import csv as _csv

    if not csv_path.exists():
        _die(f"Ergebnis-CSV fehlt: {csv_path}")
    rows: list[dict[str, Any]] = []
    with csv_path.open(encoding="utf-8") as fh:
        for row in _csv.DictReader(fh):
            if row.get("model") != model:
                continue
            rows.append({
                "asset_id": row.get("asset_id", ""),
                "score": float(row.get("percentage") or 0.0),
                "output_tokens": int(float(row.get("output_tokens") or 0)),
                "input_tokens": int(float(row.get("input_tokens") or 0)),
                "response_length": int(float(row.get("response_length") or 0)),
                "execution_time": float(row.get("execution_time") or 0.0),
                "ts": _to_epoch(row.get("timestamp") or ""),
            })
    return rows


def _to_epoch(ts: str) -> float:
    try:
        return datetime.strptime(ts, _TS_FMT).timestamp()
    except ValueError:
        return 0.0


def read_sessions(db_path: Path, hermes_model: str) -> list[SessionInfo]:
    """Liest Sessions + Reasoning-Spuren read-only aus der Hermes-State-DB."""
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        return _collect_sessions(con, hermes_model)
    finally:
        con.close()


def _collect_sessions(con: sqlite3.Connection, hermes_model: str) -> list[SessionInfo]:
    where, params = ("", ())
    if hermes_model:
        where = "WHERE s.model = ?"
        params = (hermes_model,)
    out: list[SessionInfo] = []
    for sid, started in con.execute(
        f"SELECT s.id, s.started_at FROM sessions s {where} ORDER BY s.started_at", params
    ):
        info = SessionInfo(session_id=sid, started_at=float(started or 0.0))
        _apply_usage(con, info)
        _apply_messages(con, info)
        out.append(info)
    return out


def _apply_usage(con: sqlite3.Connection, info: SessionInfo) -> None:
    """Haupt-Loop (task='') und Auxiliary-Calls (task!='') getrennt aufsummieren."""
    for task, calls, tin, tout, cache, reason, model in con.execute(
        "SELECT task, api_call_count, input_tokens, output_tokens, cache_read_tokens,"
        " reasoning_tokens, model FROM session_model_usage WHERE session_id = ?",
        (info.session_id,),
    ):
        info.models.add(str(model))
        if task:
            info.aux_calls += int(calls or 0)
            info.aux_tokens += int(tout or 0)
            continue
        info.api_calls = int(calls or 0)
        info.input_tokens = int(tin or 0)
        info.output_tokens = int(tout or 0)
        info.cache_read_tokens = int(cache or 0)
        info.reasoning_tokens = int(reason or 0)


def _apply_messages(con: sqlite3.Connection, info: SessionInfo) -> None:
    for content, reasoning in con.execute(
        "SELECT content, reasoning_content FROM messages"
        " WHERE session_id = ? AND role = 'assistant' ORDER BY rowid",
        (info.session_id,),
    ):
        text = str(reasoning or "")
        if text.strip():
            info.reasoning_chars += len(text)
            info.reasoning_msgs += 1
        if str(content or "").strip():
            info.final_content = str(content)


def audit_response_text(model: str, asset_id: str) -> str:
    """Verbatim-Antwort aus dem Audit-Log (Abschnitt 2) — primäres Join-Key."""
    path = AUDIT_ROOT / model / f"{asset_id}.md"
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"## 2\. Model Response / Antwort\n(.*?)\n## 3\.", text, re.S)
    return match.group(1).strip() if match else ""


def match_session(
    row: dict[str, Any], sessions: list[SessionInfo], model: str,
) -> tuple[SessionInfo | None, str]:
    """Join: Verbatim-Antworttext, sonst Output-Token-Gleichheit; Tiebreak = Zeitnähe.

    Der Audit-Log-Text ist die **komplette** sichtbare Ausgabe des Loops (der
    Stream führt auch Zwischen-Nachrichten wie „ich prüfe erst …" zusammen),
    die DB enthält nur die finale Assistant-Nachricht. Darum: exakte Gleichheit,
    sonst Suffix-Enthaltensein. Token-Gleichheit ist der Rückfall, wenn ein
    Audit-Log fehlt.
    """
    want_text = audit_response_text(model, row["asset_id"])
    if want_text:
        exact = [s for s in sessions if s.final_content.strip() == want_text]
        if exact:
            return _nearest(exact, row["ts"]), "antwort-text"
        suffix = [s for s in sessions if _suffix_matches(s.final_content, want_text)]
        if suffix:
            return _nearest(suffix, row["ts"]), "antwort-ende"
    by_tokens = [s for s in sessions if s.output_tokens and s.output_tokens == row["output_tokens"]]
    if by_tokens:
        return _nearest(by_tokens, row["ts"]), "output-tokens"
    return None, "—"


def _suffix_matches(db_content: str, audit_text: str) -> bool:
    """Wahr, wenn das Ende der DB-Nachricht im Audit-Text steht (Headings ausgenommen)."""
    body = db_content.strip()
    if len(body) < MIN_SUFFIX_CHARS:
        return False
    tail = body[-TAIL_MATCH_CHARS:] if len(body) > TAIL_MATCH_CHARS else body
    return tail in audit_text


def _nearest(cands: list[SessionInfo], ts: float) -> SessionInfo:
    return min(cands, key=lambda s: abs(s.started_at - ts)) if ts else cands[-1]


def module_of(asset_id: str) -> str:
    if asset_id.startswith("code_quality"):
        return "code_quality"
    if asset_id.startswith("cli"):
        return "cli"
    if asset_id.startswith("reasoning_metacog"):
        return "metacog (Tier 3)"
    if asset_id.startswith("reasoning"):
        return "reasoning T0-T2"
    return asset_id.split("_")[0]


def build_report(
    rows: list[dict[str, Any]], sessions: list[SessionInfo], model: str,
) -> dict[str, Any]:
    """Pro Task den Reasoning-Anteil heben; nach Modul aggregieren."""
    tasks: list[dict[str, Any]] = []
    for row in rows:
        sess, method = match_session(row, sessions, model)
        entry = dict(row)
        entry["module"] = module_of(row["asset_id"])
        entry["join"] = method
        if sess is None:
            entry.update({k: None for k in
                          ("reasoning_tokens", "reasoning_chars", "api_calls", "cache_read")})
        else:
            entry.update({
                "session_id": sess.session_id,
                "reasoning_tokens": sess.reasoning_tokens,
                "reasoning_chars": sess.reasoning_chars,
                "api_calls": sess.api_calls,
                "cache_read": sess.cache_read_tokens,
                "aux_calls": sess.aux_calls,
                "share": (sess.reasoning_tokens / sess.output_tokens) if sess.output_tokens else None,
            })
        tasks.append(entry)
    return {"tasks": tasks, "modules": _aggregate(tasks)}


def _aggregate(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for t in tasks:
        groups.setdefault(t["module"], []).append(t)
    out: dict[str, Any] = {}
    for mod, items in groups.items():
        got = [t for t in items if t.get("reasoning_tokens") is not None]
        out[mod] = {
            "n": len(items),
            "matched": len(got),
            "score": _mean(t["score"] for t in items),
            "output_tokens": _mean(t["output_tokens"] for t in items),
            "reasoning_tokens": _mean(t["reasoning_tokens"] for t in got),
            "reasoning_chars": _mean(t["reasoning_chars"] for t in got),
            "share": _mean(t["share"] for t in got if t.get("share") is not None),
            "api_calls": _mean(t["api_calls"] for t in got),
            "cache_read": _mean(t["cache_read"] for t in got),
        }
    return out


def _mean(values: Any) -> float:
    vals = [v for v in values if v is not None]
    return sum(vals) / len(vals) if vals else 0.0


def render_md(report: dict[str, Any], model: str) -> str:
    lines = [f"# Hermes Reasoning Report — {model}", ""]
    lines += ["| Modul | n | Score | out-Tok | reason-Tok | Anteil | Denkzeichen | Ø Calls | Ø cache_read |",
              "|---|---|---|---|---|---|---|---|---|"]
    for mod, s in sorted(report["modules"].items()):
        lines.append(
            f"| {mod} | {s['n']} ({s['matched']} gematcht) | {s['score']:.1f} | {s['output_tokens']:.0f} "
            f"| {s['reasoning_tokens']:.0f} | {s['share'] * 100:.1f} % | {s['reasoning_chars']:.0f} "
            f"| {s['api_calls']:.1f} | {s['cache_read']:.0f} |"
        )
    lines += ["", "## Pro Task", "",
              "| Asset | Modul | Score | reason-Tok | Denkzeichen | Anteil | Calls | cache_read | Join |",
              "|---|---|---|---|---|---|---|---|---|"]
    for t in report["tasks"]:
        share = "—" if t.get("share") is None else f"{t['share'] * 100:.0f} %"
        rt = "—" if t.get("reasoning_tokens") is None else f"{t['reasoning_tokens']}"
        rc = "—" if t.get("reasoning_chars") is None else f"{t['reasoning_chars']}"
        ca = "—" if t.get("api_calls") is None else f"{t['api_calls']}"
        cr = "—" if t.get("cache_read") is None else f"{t['cache_read']}"
        lines.append(f"| {t['asset_id']} | {t['module']} | {t['score']:.1f} | {rt} | {rc} "
                     f"| {share} | {ca} | {cr} | {t['join']} |")
    unmatched = [t["asset_id"] for t in report["tasks"] if t.get("reasoning_tokens") is None]
    if unmatched:
        lines += ["", f"⚠️ Ohne Session-Treffer: {', '.join(unmatched)}"]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Hermes Reasoning-Report aus der State-DB")
    parser.add_argument("--model", required=True, help="Benchmark-Modell-ID (Agentic-Entität)")
    parser.add_argument("--provider", default="hermes", help="Provider-Key (Default: hermes)")
    parser.add_argument("--db", default=None, help="Pfad zur Hermes-State-DB (Default: provider_config)")
    parser.add_argument("--csv", default=str(CSV_PATH), help="Ergebnis-CSV")
    parser.add_argument("--format", choices=("md", "json"), default="md")
    parser.add_argument("--out", default=None, help="Zieldatei (Default: stdout)")
    args = parser.parse_args()

    config = ConfigValidator().config
    provider_cfg = _provider_cfg(config, args.provider)
    if not is_agentic_track_provider(provider_cfg):
        _die(f"Provider '{args.provider}' ist kein Agentic-Track — Report macht nur für Hermes-Sessions Sinn.")

    db_path = _resolve_db_path(args.db, provider_cfg)
    rows = read_result_rows(args.model, Path(args.csv))
    if not rows:
        _die(f"Keine Ergebniszeilen für '{args.model}' in {args.csv}")
    report = build_report(rows, read_sessions(db_path, _hermes_model_for(config, args.model)), args.model)
    body = (json.dumps(report, ensure_ascii=False, indent=2) if args.format == "json"
            else render_md(report, args.model))
    if args.out:
        Path(args.out).write_text(body, encoding="utf-8")
        print(f"✓ Report geschrieben: {args.out}")
    else:
        print(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
