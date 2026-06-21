#!/usr/bin/env python3
"""
CSV-Hygiene-Sanitizer fuer CrucibleMark Benchmark-CSVs.

Bereinigt die Haupt-CSV-Dateien (local/cloud/commercial) von strukturellen
und inhaltlichen Korruptionen, die durch verschachtelte Rohtext-Antworten,
falsch-escapte Felder oder Header-Repeats entstehen.

Filter-Regeln
-------------
Eine Zeile wird verworfen, wenn mindestens EINES zutrifft:

1. **Header-Repeat**: ``parts[0] == 'asset_id'`` (Header wurde als Datenzeile
   geschrieben, weil eine vorherige Iteration eine Header-Zeile emittiert hat).
2. **Rohtext-Asset-ID**: ``asset_id`` laenger als 80 Zeichen, enthaelt Markdown-
   Marker (``##``, ``###``, ``---``), oder beginnt mit typischem Romananfang
   ("The ", "For ", "Final:"). Solche Zeilen stammen aus ungenutzend escaped
   LLM-Rohtext-Antworten.
3. **Boolean-Modell**: ``model`` ist "True" / "False" (wurde aus einer
   Bool-Spalte in die model-Spalte verschoben).
4. **Leeres Modell**: ``model`` ist NaN, leerer String oder "unknown" in
   Kombination mit Status != "success".

Verwendung
----------

Dry-Run (default): zaehlt, was rausfliegen wuerde, aendert nichts::

    python scripts/maintenance/sanitize_benchmark_csvs.py

Apply-Modus: macht Backup (.bak-Datei) und schreibt bereinigte CSVs::

    python scripts/maintenance/sanitize_benchmark_csvs.py --apply

Exit-Code: 0 wenn keine Veraenderung noetig, 1 wenn Apply etwas geaendert hat
(nur im --apply Modus; bei Bedarf fuer CI nutzbar).
"""
from __future__ import annotations

import argparse
import csv
import logging
import shutil
import sys
from collections import Counter
from pathlib import Path

# pylint: disable=wrong-import-position
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from scripts.leaderboard.config import (  # noqa: E402
    CLOUD_CSV,
    COMMERCIAL_CSV,
    LOCAL_CSV,
)

logger = logging.getLogger("sanitize_csv")

# Asset-IDs, die echt aussehen, sind typischerweise 8-30 Zeichen (z.B.
# "code_quality_005", "cli_benchmark_007", "tooluse_001").
MAX_VALID_ASSET_ID_LEN = 60

# Romananfaenge, die NICHT als asset_id vorkommen duerfen.
NARRATIVE_PREFIXES = (
    "the ", "for ", "final:", "this ", "these ", "model ", "models ",
    "first,", "second,", "third,", "however,", "moreover,", "therefore,",
    "in summary,", "to summarize,",
)

# Markdown-Marker in der asset_id.
MARKDOWN_MARKERS = ("##", "###", "---", "***", "===", "**", "→")

# Boolean-Strings, die NICHT als model_id vorkommen.
BOOLEAN_MODEL_VALUES = frozenset({"true", "false"})

# Known finish_reason values that should never appear as model names.
FINISH_REASON_VALUES = frozenset({"length", "stop", "content_filter", "tool_calls"})

# Datei-Liste, die bereinigt wird.
TARGET_CSVS = (LOCAL_CSV, CLOUD_CSV, COMMERCIAL_CSV)


def _is_header_repeat(parts: list[str]) -> bool:
    """True wenn die Zeile der CSV-Header ist (sollte nicht als Daten erscheinen)."""
    return bool(parts) and parts[0].strip() == "asset_id"


def _is_narrative_asset_id(asset_id: str) -> bool:
    """True wenn asset_id wie ein Rohtext-Fragment aussieht."""
    aid = asset_id.strip()
    if not aid:
        return True
    if len(aid) > MAX_VALID_ASSET_ID_LEN:
        return True
    lowered = aid.lower()
    if any(lowered.startswith(p) for p in NARRATIVE_PREFIXES):
        return True
    if any(marker in aid for marker in MARKDOWN_MARKERS):
        return True
    return False


def _is_invalid_model(model: str) -> tuple[bool, str]:
    """Prueft ob der model-Wert ein gueltiger Model-Identifier ist.

    Returns:
        (is_invalid, reason) -- reason ist "empty" | "boolean" | "numeric" | "finish_reason" | "unknown"
    """
    m = (model or "").strip()
    if not m or m.lower() in {"nan", "none", "null"}:
        return True, "empty"
    if m.lower() in BOOLEAN_MODEL_VALUES:
        return True, "boolean"
    # Pure-numeric model names (e.g. "65536", "12000", "4") are column-shift artifacts
    # from token limits, max_tokens, or judge sub-scores leaking into the model field.
    if m.replace(".", "").replace("_", "").replace("-", "").isdigit():
        return True, "numeric"
    # Known finish_reason values (e.g. "length", "stop") that shifted into model field.
    if m.lower() in FINISH_REASON_VALUES:
        return True, "finish_reason"
    return False, ""


def _read_csv_with_header(path: Path) -> tuple[list[str], list[list[str]]]:
    """Liest CSV mit Header. Liefert (header, rows).

    Akzeptiert auch strukturell korrupte Zeilen (z.B. mit falscher Spaltenanzahl),
    weil die Zeilen-Laenge nicht der Sanitizer-Trigger ist -- nur der Inhalt.
    """
    rows: list[list[str]] = []
    with path.open(encoding="utf-8") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return [], []
        for parts in reader:
            if parts:
                rows.append(parts)
    return header, rows


def _filter_rows(header: list[str], rows: list[list[str]]) -> tuple[list[list[str]], Counter]:
    """Filtert korrupte Zeilen raus. Liefert (clean_rows, drop_reasons).

    drop_reasons ist ein Counter: {reason: count}.
    """
    asset_id_idx = header.index("asset_id") if "asset_id" in header else 0
    model_idx = header.index("model") if "model" in header else 12
    status_idx = header.index("status") if "status" in header else 23

    clean: list[list[str]] = []
    drop_reasons: Counter = Counter()

    for parts in rows:
        if _is_header_repeat(parts):
            drop_reasons["header_repeat"] += 1
            continue

        asset_id = parts[asset_id_idx] if len(parts) > asset_id_idx else ""
        if _is_narrative_asset_id(asset_id):
            drop_reasons["narrative_asset_id"] += 1
            continue

        model = parts[model_idx] if len(parts) > model_idx else ""
        is_invalid, reason = _is_invalid_model(model)
        if is_invalid:
            status = parts[status_idx] if len(parts) > status_idx else ""
            # Erfolgreiche Runs ohne model sind ein Daten-Bug; verwerfen.
            if status == "success":
                drop_reasons[f"invalid_model_{reason}"] += 1
                continue
            # failed/ aborted ohne model: ebenfalls verwerfen (kein Beitrag).
            drop_reasons[f"invalid_model_{reason}_non_success"] += 1
            continue

        clean.append(parts)

    return clean, drop_reasons


def _write_csv_atomic(path: Path, header: list[str], rows: list[list[str]]) -> None:
    """Schreibt CSV atomar: erst .tmp, dann rename. Verhindert halbe Files."""
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    tmp_path.replace(path)


def _backup_csv(path: Path) -> Path:
    """Erstellt ein .bak-Backup. Ueberschreibt kein bestehendes .bak (idempotent)."""
    backup = path.with_suffix(path.suffix + ".bak")
    if backup.exists():
        return backup
    shutil.copy2(path, backup)
    return backup


def _process_one(csv_path: Path, apply: bool) -> tuple[int, int, Counter]:
    """Bereinigt eine CSV. Liefert (rows_total, rows_kept, drop_reasons).

    Bei apply=False wird die Datei NICHT geschrieben.
    """
    if not csv_path.exists():
        logger.info("  (skip) %s existiert nicht.", csv_path.name)
        return 0, 0, Counter()

    header, rows = _read_csv_with_header(csv_path)
    if not header:
        return 0, 0, Counter()

    clean_rows, drop_reasons = _filter_rows(header, rows)

    total = len(rows)
    kept = len(clean_rows)
    dropped = total - kept

    logger.info("=== %s ===", csv_path.name)
    logger.info("  Header: %d Spalten, Total Rows: %d", len(header), total)
    if drop_reasons:
        for reason, count in sorted(drop_reasons.items(), key=lambda x: -x[1]):
            logger.info("  Drop: %-30s %6d", reason, count)
    logger.info("  Behalten: %d  Verworpen: %d", kept, dropped)

    if apply and dropped > 0:
        backup = _backup_csv(csv_path)
        logger.info("  Backup: %s", backup.name)
        _write_csv_atomic(csv_path, header, clean_rows)
        logger.info("  -> geschrieben: %d Zeilen", kept)

    return total, kept, drop_reasons


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", maxsplit=1)[0])
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Schreibt die bereinigten CSVs (mit .bak-Backup). Ohne --apply nur Dry-Run.",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Aktiviert DEBUG-Logging."
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(message)s",
    )

    if args.apply:
        logger.info("=== APPLY MODE (Backup + Write) ===\n")
    else:
        logger.info("=== DRY-RUN (nur Diagnose) ===\n")

    total_dropped_overall = 0
    for csv_path in TARGET_CSVS:
        total, kept, reasons = _process_one(csv_path, apply=args.apply)
        total_dropped_overall += (total - kept)
        logger.info("")  # spacing

    logger.info("=" * 60)
    if total_dropped_overall == 0:
        logger.info("Keine Korruption gefunden. CSVs sind sauber.")
        return 0
    if args.apply:
        logger.info(
            "Insgesamt %d korrupte Zeilen entfernt. Backups: %s",
            total_dropped_overall,
            ", ".join(p.with_suffix(p.suffix + ".bak").name for p in TARGET_CSVS if p.exists()),
        )
        return 0
    logger.info(
        "%d korrupte Zeilen wuerden entfernt werden. Mit --apply anwenden.",
        total_dropped_overall,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
