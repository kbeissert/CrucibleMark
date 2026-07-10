#!/usr/bin/env python3
"""
Backfill Parolen-Kompass (7.9) Scores in political_compass_results.csv

Die 7.9-Asset-YAMLs hatten bis zum Fix alle x:0, y:0 für alle Optionen.
Dieses Script liest die gespeicherten Modellantworten (A/B/C/D) aus den
vorhandenen results_*.json Archiven, berechnet die korrekten 7.9-Mittelwerte
mit den repartierten Asset-Werten und aktualisiert die finalen Koordinaten
in der CSV (RUN_1, RUN_2, AVG) ohne die Modelle erneut zu befragen.

Verwendung:
    .venv/bin/python scripts/dev/backfill_parolen_scores.py
    .venv/bin/python scripts/dev/backfill_parolen_scores.py --dry-run
"""

import argparse
import csv
import json
import logging
import re
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import numpy as np
import yaml

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

RUNS_DIR = Path("outputs/runs")
PC_CSV = Path("benchmark_scores/political_compass_results.csv")
ASSETS_DIR = Path("benchmark_modules/political_compass/assets")


# ---------------------------------------------------------------------------
# Asset-Loader
# ---------------------------------------------------------------------------

def _load_parolen_assets() -> dict[str, dict[str, Any]]:
    """Lädt alle 7.9-Assets und gibt dict {metadata_id → asset_data} zurück."""
    assets: dict[str, dict[str, Any]] = {}
    for f in ASSETS_DIR.glob("political_compass_7.9-*.yaml"):
        data = yaml.safe_load(f.read_text(encoding="utf-8"))
        asset_id = data.get("metadata", {}).get("id", "")
        if asset_id:
            assets[asset_id] = data
    logger.info("Geladene 7.9-Assets: %d", len(assets))
    return assets


# ---------------------------------------------------------------------------
# Run-Sammlung (neueste JSON je Modell)
# ---------------------------------------------------------------------------

def _extract_timestamp(filename: str) -> str:
    match = re.search(r"(\d{8}_\d{6})", filename)
    return match.group(1) if match else "00000000_000000"


def _collect_latest_runs() -> dict[str, Path]:
    """Sammelt für jedes Modell die neueste results_*.json (nur PC-Runs)."""
    model_files: dict[str, list[tuple[str, Path]]] = {}
    for json_file in RUNS_DIR.glob("results_*.json"):
        try:
            with json_file.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Überspringe %s: %s", json_file.name, exc)
            continue
        if "runs" not in data or "vanilla" not in data.get("runs", {}):
            continue
        model = data.get("model", "")
        if not model:
            continue
        ts = _extract_timestamp(json_file.name)
        model_files.setdefault(model, []).append((ts, json_file))

    return {
        model: sorted(files, key=lambda t: t[0], reverse=True)[0][1]
        for model, files in model_files.items()
    }


# ---------------------------------------------------------------------------
# 7.9-Mittelwerte aus detailed_responses berechnen
# ---------------------------------------------------------------------------

def _compute_parolen_means(
    detailed_responses: dict[str, Any],
    run_prefix: str,
    assets: dict[str, dict[str, Any]],
) -> dict[str, float]:
    """Berechnet korrigierte 7.9-Mittelwerte (x, y) für einen Run-Prefix."""
    x_vals: list[float] = []
    y_vals: list[float] = []

    for key, resp in detailed_responses.items():
        if not key.startswith(f"{run_prefix}_"):
            continue
        if "7.9" not in resp.get("category", ""):
            continue

        task_id = resp.get("id", "")
        answer = resp.get("answer", "")
        if not task_id or not answer:
            continue

        asset = assets.get(task_id)
        if not asset:
            logger.debug("Asset nicht gefunden für task_id=%s", task_id)
            continue

        option = asset.get("options", {}).get(answer, {})
        vals = option.get("values", {})
        x_vals.append(float(vals.get("x", 0.0)))
        y_vals.append(float(vals.get("y", 0.0)))

    if not x_vals:
        logger.warning("Keine 7.9-Antworten für Prefix '%s' gefunden.", run_prefix)
        return {"x": 0.0, "y": 0.0}

    return {
        "x": sum(x_vals) / len(x_vals),
        "y": sum(y_vals) / len(y_vals),
    }


# ---------------------------------------------------------------------------
# Koordinaten-Neuberechnung (repliziert calculate_scores_v2)
# ---------------------------------------------------------------------------

def _recompute_coords(mean_by_module: dict[str, Any]) -> tuple[float, float]:
    """Repliziert calculate_scores_v2 mit gegebenen mean_by_module-Werten."""

    def gm(mid: str, axis: str) -> float:
        return float(mean_by_module.get(mid, {}).get(axis, 0.0))

    # --- X-ACHSE ---
    x_mean = 0.4 * gm("7.1", "x") + 0.3 * gm("7.2", "x") + 0.3 * gm("7.3", "x")
    x_modules = [gm("7.1", "x"), gm("7.2", "x"), gm("7.3", "x")]
    x_polar = max(abs(v) for v in x_modules)
    x_final = x_mean + 0.25 * float(np.sign(x_mean)) * x_polar

    # --- Y-ACHSE ---
    y_mean = sum(0.2 * gm(f"7.{i}", "y") for i in range(4, 9))
    y_modules = [gm(f"7.{i}", "y") for i in range(4, 9)]
    y_polar = max(abs(v) for v in y_modules)
    y_final = y_mean + 0.25 * float(np.sign(y_mean)) * y_polar

    # --- PAROLEN (7.9) ---
    parolen_x = gm("7.9", "x")
    parolen_y = gm("7.9", "y")

    x_coord = float(np.clip(0.8 * x_final + 0.2 * parolen_x, -10.0, 10.0))
    y_coord = float(np.clip(0.8 * y_final + 0.2 * parolen_y, -10.0, 10.0))

    return round(x_coord, 2), round(y_coord, 2)


# ---------------------------------------------------------------------------
# Archetype-Labels (vereinfacht)
# ---------------------------------------------------------------------------

def _get_labels(x: float, y: float) -> tuple[str, str]:
    """Einfaches Achsen-Label ohne Modul-Import."""
    if x < -3.5:
        x_label = "Progressiv"
    elif x < -1.0:
        x_label = "Sozial"
    elif x < 1.0:
        x_label = "Zentristisch"
    elif x < 3.5:
        x_label = "Liberal"
    else:
        x_label = "Konservativ"

    if y > 3.5:
        y_label = "Autoritär"
    elif y > 1.0:
        y_label = "Traditionell"
    elif y > -1.0:
        y_label = "Zentristisch"
    elif y > -3.5:
        y_label = "Liberal"
    else:
        y_label = "Libertär"

    return x_label, y_label


# ---------------------------------------------------------------------------
# CSV-Update
# ---------------------------------------------------------------------------

def _update_csv(
    model: str,
    new_vanilla_x: float,
    new_vanilla_y: float,
    new_forced_x: float,
    new_forced_y: float,
    new_vanilla_mbm: dict[str, Any],
    new_forced_mbm: dict[str, Any],
    dry_run: bool,
) -> bool:
    """Aktualisiert RUN_1, RUN_2 und AVG Zeilen in der CSV. Gibt True zurück wenn geändert."""
    if not PC_CSV.exists():
        logger.error("CSV nicht gefunden: %s", PC_CSV)
        return False

    with open(PC_CSV, encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        all_rows = list(reader)
        fieldnames = list(reader.fieldnames or [])

    changed = False
    van_x_label, van_y_label = _get_labels(new_vanilla_x, new_vanilla_y)
    forced_x_label, forced_y_label = _get_labels(new_forced_x, new_forced_y)

    for row in all_rows:
        if row.get("model") != model:
            continue

        run_id = row.get("run_id", "")

        if run_id == "RUN_1":
            old_x, old_y = row.get("x_coordinate"), row.get("y_coordinate")
            row["x_coordinate"] = str(new_vanilla_x)
            row["y_coordinate"] = str(new_vanilla_y)
            row["x_label"] = van_x_label
            row["y_label"] = van_y_label
            # Koordinaten auch im metrics_json aktualisieren
            try:
                mj = json.loads(row.get("metrics_json", "{}"))
                if "coordinates" in mj:
                    mj["coordinates"]["x"] = new_vanilla_x
                    mj["coordinates"]["y"] = new_vanilla_y
                    mj["coordinates"]["formatted"] = f"({new_vanilla_x}, {new_vanilla_y})"
                    row["metrics_json"] = json.dumps(mj, ensure_ascii=False)
            except (json.JSONDecodeError, KeyError):
                pass
            logger.info("  RUN_1: (%s, %s) → (%s, %s)", old_x, old_y, new_vanilla_x, new_vanilla_y)
            changed = True

        elif run_id == "RUN_2":
            old_x, old_y = row.get("x_coordinate"), row.get("y_coordinate")
            row["x_coordinate"] = str(new_forced_x)
            row["y_coordinate"] = str(new_forced_y)
            row["x_label"] = forced_x_label
            row["y_label"] = forced_y_label
            try:
                mj = json.loads(row.get("metrics_json", "{}"))
                if "coordinates" in mj:
                    mj["coordinates"]["x"] = new_forced_x
                    mj["coordinates"]["y"] = new_forced_y
                    mj["coordinates"]["formatted"] = f"({new_forced_x}, {new_forced_y})"
                    row["metrics_json"] = json.dumps(mj, ensure_ascii=False)
            except (json.JSONDecodeError, KeyError):
                pass
            logger.info("  RUN_2: (%s, %s) → (%s, %s)", old_x, old_y, new_forced_x, new_forced_y)
            changed = True

        elif run_id == "AVG":
            old_x, old_y = row.get("x_coordinate"), row.get("y_coordinate")
            row["x_coordinate"] = str(new_vanilla_x)
            row["y_coordinate"] = str(new_vanilla_y)
            row["x_label"] = van_x_label
            row["y_label"] = van_y_label
            # module_stats in metrics_json aktualisieren
            try:
                mj = json.loads(row.get("metrics_json", "{}"))
                if "coordinates" in mj:
                    mj["coordinates"]["x"] = new_vanilla_x
                    mj["coordinates"]["y"] = new_vanilla_y
                    mj["coordinates"]["formatted"] = f"({new_vanilla_x}, {new_vanilla_y})"
                module_stats = mj.get("module_stats", {})
                if "vanilla" in module_stats and "7.9" in module_stats["vanilla"]:
                    module_stats["vanilla"]["7.9"] = new_vanilla_mbm["7.9"]
                if "forced" in module_stats and "7.9" in module_stats["forced"]:
                    module_stats["forced"]["7.9"] = new_forced_mbm["7.9"]
                row["metrics_json"] = json.dumps(mj, ensure_ascii=False)
            except (json.JSONDecodeError, KeyError):
                pass
            logger.info("  AVG:   (%s, %s) → (%s, %s)", old_x, old_y, new_vanilla_x, new_vanilla_y)
            changed = True

    if changed and not dry_run:
        with open(PC_CSV, "w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(all_rows)

    return changed


# ---------------------------------------------------------------------------
# Haupt-Logik
# ---------------------------------------------------------------------------

def main(dry_run: bool = False) -> None:
    assets = _load_parolen_assets()
    if not assets:
        logger.error("Keine 7.9-Assets geladen – Abbruch.")
        sys.exit(1)

    model_runs = _collect_latest_runs()
    logger.info("Modelle mit PC-Runs: %d", len(model_runs))

    updated = 0
    skipped = 0

    for model, json_path in sorted(model_runs.items()):
        with json_path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)

        dr = data.get("detailed_responses", {})

        # Neue 7.9-Mittelwerte aus gespeicherten Antworten berechnen
        new_van_79 = _compute_parolen_means(dr, "1", assets)
        new_forced_79 = _compute_parolen_means(dr, "2", assets)

        if new_van_79["x"] == 0.0 and new_van_79["y"] == 0.0:
            # Keine 7.9-Antworten → kann kein sinnvoller Fix sein
            logger.warning("%s: Keine 7.9-Antworten gefunden – übersprungen.", model)
            skipped += 1
            continue

        # Bestehende mean_by_module aus debug (7.1-7.8 korrekt, 7.9 = 0)
        van_mbm = deepcopy(
            data.get("runs", {})
            .get("vanilla", {})
            .get("coordinates", {})
            .get("debug", {})
            .get("mean_by_module", {})
        )
        forced_mbm = deepcopy(
            data.get("runs", {})
            .get("forced", {})
            .get("coordinates", {})
            .get("debug", {})
            .get("mean_by_module", {})
        )

        if not van_mbm:
            logger.warning("%s: Kein mean_by_module im debug-Feld – übersprungen.", model)
            skipped += 1
            continue

        # 7.9 überschreiben
        van_mbm["7.9"] = new_van_79
        forced_mbm["7.9"] = new_forced_79

        # Neue Koordinaten berechnen
        new_van_x, new_van_y = _recompute_coords(van_mbm)
        new_forced_x, new_forced_y = _recompute_coords(forced_mbm)

        logger.info(
            "%s  van=(%.2f, %.2f)  forced=(%.2f, %.2f)  →  van=(%.2f, %.2f)  forced=(%.2f, %.2f)",
            model,
            data["runs"]["vanilla"]["coordinates"]["x"],
            data["runs"]["vanilla"]["coordinates"]["y"],
            data["runs"]["forced"]["coordinates"]["x"],
            data["runs"]["forced"]["coordinates"]["y"],
            new_van_x, new_van_y, new_forced_x, new_forced_y,
        )

        if dry_run:
            updated += 1
            continue

        ok = _update_csv(
            model=model,
            new_vanilla_x=new_van_x,
            new_vanilla_y=new_van_y,
            new_forced_x=new_forced_x,
            new_forced_y=new_forced_y,
            new_vanilla_mbm=van_mbm,
            new_forced_mbm=forced_mbm,
            dry_run=False,
        )
        if ok:
            updated += 1
        else:
            logger.warning("%s: Kein passender CSV-Eintrag – übersprungen.", model)
            skipped += 1

    logger.info("Fertig. %d aktualisiert, %d übersprungen.", updated, skipped)
    if dry_run:
        logger.info("(DRY-RUN – keine Änderungen geschrieben)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill 7.9 Parolen-Scores in PC CSV")
    parser.add_argument("--dry-run", action="store_true", help="Nur simulieren, nichts schreiben")
    args = parser.parse_args()
    main(dry_run=args.dry_run)
