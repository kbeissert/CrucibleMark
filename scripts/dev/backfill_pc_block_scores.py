#!/usr/bin/env python3
"""
Backfill PC Block-Scores in political_compass_results.csv

Liest alle vorhandenen results_*.json aus outputs/runs/ und extrahiert
die per-Block-Means (7.1–7.9) aus dem debug-Objekt. Schreibt die Daten
als module_stats in den metrics_json-AVG-Eintrag jedes Modells zurück.

Verwendung:
    .venv/bin/python scripts/dev/backfill_pc_block_scores.py
    .venv/bin/python scripts/dev/backfill_pc_block_scores.py --dry-run
"""

import argparse
import csv
import json
import logging
import re
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

RUNS_DIR = Path("outputs/runs")
PC_CSV = Path("benchmark_scores/political_compass_results.csv")


def _extract_timestamp(filename: str) -> str:
    """Extrahiert den Timestamp aus dem Dateinamen (z.B. '20260419_092511')."""
    match = re.search(r"(\d{8}_\d{6})", filename)
    return match.group(1) if match else "00000000_000000"


def _collect_latest_runs() -> dict[str, Path]:
    """Sammelt für jedes Modell die neueste results_*.json Datei."""
    model_files: dict[str, list[tuple[str, Path]]] = {}

    for json_file in RUNS_DIR.glob("results_*.json"):
        try:
            with json_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Überspringe %s: %s", json_file.name, e)
            continue

        # Nur PC-Runs
        if "runs" not in data or "vanilla" not in data.get("runs", {}):
            continue

        model_name = data.get("model", "")
        if not model_name:
            continue

        ts = _extract_timestamp(json_file.name)
        model_files.setdefault(model_name, []).append((ts, json_file))

    # Neueste Datei je Modell auswählen
    return {
        model: sorted(files, key=lambda t: t[0], reverse=True)[0][1]
        for model, files in model_files.items()
    }


def _extract_module_stats(data: dict[str, Any]) -> dict[str, Any]:
    """Extrahiert module_stats aus den vanilla/forced debug-Daten."""
    vanilla_means = (
        data.get("runs", {})
        .get("vanilla", {})
        .get("coordinates", {})
        .get("debug", {})
        .get("mean_by_module", {})
    )
    forced_means = (
        data.get("runs", {})
        .get("forced", {})
        .get("coordinates", {})
        .get("debug", {})
        .get("mean_by_module", {})
    )
    return {"vanilla": vanilla_means, "forced": forced_means}


def _update_csv(
    model_stats: dict[str, dict[str, Any]], dry_run: bool
) -> tuple[int, int]:
    """Schreibt module_stats in die AVG-Zeilen der CSV. Gibt (updated, skipped) zurück."""
    if not PC_CSV.exists():
        logger.error("CSV nicht gefunden: %s", PC_CSV)
        return 0, 0

    rows: list[dict[str, str]] = []
    fieldnames: list[str] = []
    with PC_CSV.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    updated = 0
    skipped = 0

    for row in rows:
        if row.get("run_id") != "AVG":
            continue

        model = row.get("model", "")
        if model not in model_stats:
            skipped += 1
            continue

        new_module_stats = model_stats[model]
        if not new_module_stats.get("vanilla") and not new_module_stats.get("forced"):
            skipped += 1
            continue

        # Bestehende metrics_json parsen und module_stats ergänzen
        existing_str = row.get("metrics_json", "{}")
        try:
            metrics = json.loads(existing_str) if existing_str else {}
        except json.JSONDecodeError:
            metrics = {}

        metrics["module_stats"] = new_module_stats
        row["metrics_json"] = json.dumps(metrics, ensure_ascii=False)
        updated += 1
        logger.info("  ✓ %s — module_stats ergänzt (7.1–7.9)", model)

    if not dry_run:
        with PC_CSV.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        logger.info("CSV gespeichert: %s", PC_CSV)

    return updated, skipped


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill PC block scores in CSV")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Nur simulieren, keine Datei schreiben",
    )
    args = parser.parse_args()

    logger.info("Suche results_*.json in %s ...", RUNS_DIR)
    latest_runs = _collect_latest_runs()
    logger.info("Gefunden: %d PC-Runs (je neuester Run pro Modell)", len(latest_runs))

    # Block-Stats je Modell extrahieren
    model_stats: dict[str, dict[str, Any]] = {}
    for model_name, json_file in sorted(latest_runs.items()):
        try:
            with json_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Fehler beim Lesen von %s: %s", json_file.name, e)
            continue

        stats = _extract_module_stats(data)
        if stats["vanilla"] or stats["forced"]:
            model_stats[model_name] = stats
            logger.debug("  %s: %d Vanilla-Blöcke", model_name, len(stats["vanilla"]))

    logger.info("%d Modelle mit Block-Daten gefunden", len(model_stats))

    if args.dry_run:
        logger.info("[DRY-RUN] Keine Änderungen werden geschrieben.")

    updated, skipped = _update_csv(model_stats, dry_run=args.dry_run)

    logger.info(
        "Fertig: %d AVG-Zeilen aktualisiert, %d übersprungen%s",
        updated,
        skipped,
        " (dry-run)" if args.dry_run else "",
    )


if __name__ == "__main__":
    main()
