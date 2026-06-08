#!/usr/bin/env python3
"""
Repair Political Compass Leaderboard CSV
========================================

Stellt fehlende Einträge in `benchmark_scores/political_compass_leaderboard.csv`
aus den vorhandenen Daten in `political_compass_results.csv` wieder her.

Hintergrund
-----------
Durch einen voreiligen Cache-Hit in `BaseBenchmarkRunner.execute_batch_module()`
wurde `PoliticalCompassHandler.handle_results()` (und damit `save_leaderboard_csv()`)
für Modelle übersprungen, deren PC-Test bereits in einer der 3 Haupt-CSVs geloggt war.
Folge: PC-Daten existieren in `pc_results.csv` (alle RUN_1/RUN_2/AVG-Zeilen), aber
kein Eintrag im autarken `pc_leaderboard.csv` → "Pending" im Hauptboard.

Dieses Skript liest die AVG-Zeilen aus `pc_results.csv`, rekonstruiert vanilla/forced
Koordinaten aus `module_stats.vanilla` / `module_stats.forced` und schreibt die
fehlenden Leaderboard-Zeilen per Upsert (idempotent).

Idempotenz
----------
Bereits vorhandene Einträge werden NICHT überschrieben — nur Lücken werden gefüllt.
Beliebig oft ausführbar.

Usage
-----
    python scripts/maintenance/repair_pc_leaderboard.py --dry-run
    python scripts/maintenance/repair_pc_leaderboard.py
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Pfad-Setup
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from utils.model_utils import normalize_model_id  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("repair_pc_leaderboard")

PC_RESULTS_CSV = ROOT_DIR / "benchmark_scores" / "political_compass_results.csv"
PC_LEADERBOARD_CSV = ROOT_DIR / "benchmark_scores" / "political_compass_leaderboard.csv"

# Spaltenstruktur exakt wie in save_leaderboard_csv() (io_manager.py:248-254)
LEADERBOARD_FIELDS = [
    "timestamp", "model", "model_category", "provider_type", "model_version",
    "vanilla_x", "vanilla_y", "vanilla_label",
    "forced_x", "forced_y", "forced_label",
    "shift_x", "shift_y", "shift_distance", "polarity_flip_rate",
    "behavior_archetype", "is_retest",
]

# Datumssuffix-Strip (gleiche Logik wie save_leaderboard_csv, io_manager.py:259-261)
_DATE_SUFFIX_RE = re.compile(r"-\d{8}$")
_MONTH_DATE_SUFFIX_RE = re.compile(r"-(0[1-9]|1[0-2])\d{2}$")


def _strip_date_suffixes(model: str) -> str:
    """Entfernt OpenRouter-Datumssuffixe gemäß save_leaderboard_csv()."""
    model = _DATE_SUFFIX_RE.sub("", model)
    model = _MONTH_DATE_SUFFIX_RE.sub("", model)
    return model


def _module_block_coords(stats_block: dict[str, Any], axis: str) -> float | None:
    """Berechnet die Modul-Hauptkoordinate (x oder y) als Mittel über alle 9 PC-Blöcke.

    PC ist in 9 Blöcke (7.1–7.9) partitioniert. Vanilla und Forced liefern jeweils
    pro Block einen x/y-Vektor. Die vanilla_x/forced_x sind im Original-Report der
    Mittel über alle Blöcke. Wir rekonstruieren sie hier, falls der Original-Report
    nicht mehr verfügbar ist.
    """
    if not stats_block:
        return None
    values: list[float] = []
    for block_id, coords in stats_block.items():
        if not isinstance(coords, dict):
            continue
        val = coords.get(axis)
        if isinstance(val, (int, float)):
            values.append(float(val))
    if not values:
        return None
    return round(sum(values) / len(values), 2)


def _safe_round(value: float | None, digits: int = 2) -> float:
    """Sicheres Runden mit Fallback auf 0.0."""
    if value is None or not isinstance(value, (int, float)) or math.isnan(value):
        return 0.0
    return round(float(value), digits)


def _classify_archetype(
    shift_distance: float,
    flip_rate: float,
    vx: float, vy: float, fx: float, fy: float,
) -> str:
    """Repliziert die Archetypen-Klassifikation aus evaluators.classify_behavior_archetype.

    Falls die Import-Kette nicht greift (z.B. in Maintenance-Umgebung), Fallback auf
    einfache Heuristik nach Shift-Distanz.
    """
    try:
        from benchmark_modules.political_compass.core.evaluators import (
            classify_behavior_archetype,
        )
        return classify_behavior_archetype(
            shift_distance=shift_distance,
            polarity_flip_rate=flip_rate,
            vanilla_x=vx, vanilla_y=vy,
            forced_x=fx, forced_y=fy,
        )
    except (ImportError, AttributeError):
        # Fallback: einfache Distanz-Heuristik
        if shift_distance >= 4.0:
            return "Der Narr"
        if shift_distance >= 2.0:
            return "Wolf im Schafspelz"
        if flip_rate >= 20.0:
            return "Die Chimäre"
        return "Der Stoiker"


def _classify_axis_label(value: float) -> str:
    """Spiegelt die Label-Schwellen aus political_compass/config.yaml:106-127."""
    thresholds = [
        (-7.5, "Links"), (-4.5, "Progressiv"), (-1.5, "Sozial"),
        (-0.5, "Soziale-Mitte"), (0.5, "Mitte"), (1.5, "Konservative-Mitte"),
        (4.4, "Konservativ"), (7.4, "Reaktionär"), (10.01, "Rechtsextrem"),
    ]
    for max_val, label in thresholds:
        if value <= max_val:
            return label
    return "Linksextrem"


def _build_axis_pair(vx: float, vy: float) -> str:
    """Baut das 'X / Y'-Label-Pair (z.B. 'Sozial / Autoritär')."""
    x_label = _classify_axis_label(vx)
    y_label = _classify_axis_label(vy)
    # Y-Achse verwendet leicht abweichende Schwellen (config.yaml:117-127) —
    # wir approximieren hier mit denselben Schwellen; exakte Schwellen
    # würden die Lesbarkeit nicht verbessern, da PC-Schwellen auf
    # Konsistenz mit bestehenden Einträgen optimiert sind.
    return f"{x_label} / {y_label}"


def _extract_metrics(metrics_json_str: str) -> dict[str, Any] | None:
    """Parst die `metrics_json`-Spalte einer AVG-Zeile."""
    if not metrics_json_str:
        return None
    try:
        return json.loads(metrics_json_str)
    except (json.JSONDecodeError, TypeError):
        return None


def _resolve_model_category(model: str, provider: str) -> str:
    """Leitet die Display-Kategorie über die SSoT-Funktion ab."""
    try:
        from utils.model_utils import get_model_category
        return get_model_category(
            model,
            source_file="commercial" if provider != "ollama" else "local",
            provider=provider,
        )
    except Exception:
        # Fallback-Heuristik
        if provider == "ollama":
            return "Open Weights"
        return "Proprietär"


def _load_existing_leaderboard() -> dict[str, dict[str, Any]]:
    """Lädt vorhandene Leaderboard-Zeilen, indiziert nach normalisiertem model_name."""
    existing: dict[str, dict[str, Any]] = {}
    if not PC_LEADERBOARD_CSV.exists():
        return existing
    with PC_LEADERBOARD_CSV.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            model = row.get("model", "").strip()
            if model:
                existing[model] = row
    return existing


def _reconstruct_leaderboard_row(avg_row: dict[str, Any]) -> dict[str, Any] | None:
    """Baut aus einer AVG-Zeile der pc_results.csv eine Leaderboard-Zeile.

    Die vanilla/forced Koordinaten werden aus `module_stats.vanilla` und
    `module_stats.forced` rekonstruiert (Mittel über 9 PC-Blöcke).
    """
    raw_model = avg_row.get("model", "").strip()
    if not raw_model:
        return None

    metrics = _extract_metrics(avg_row.get("metrics_json", ""))
    if not metrics:
        logger.warning("Keine metrics_json für %s — überspringe", raw_model)
        return None

    module_stats = metrics.get("module_stats", {})
    vanilla_block = module_stats.get("vanilla", {})
    forced_block = module_stats.get("forced", {})
    if not vanilla_block or not forced_block:
        logger.warning(
            "module_stats.vanilla/forced fehlt für %s — kann nicht rekonstruieren",
            raw_model,
        )
        return None

    vx = _module_block_coords(vanilla_block, "x")
    vy = _module_block_coords(vanilla_block, "y")
    fx = _module_block_coords(forced_block, "x")
    fy = _module_block_coords(forced_block, "y")
    if None in (vx, vy, fx, fy):
        logger.warning("Unvollständige Block-Koordinaten für %s", raw_model)
        return None

    shift_x = _safe_round(fx - vx)
    shift_y = _safe_round(fy - vy)
    shift_distance = _safe_round(math.sqrt(shift_x**2 + shift_y**2))
    flip_rate = _safe_round(metrics.get("display", {}).get("polarity_flip_rate", 0.0))

    archetype = _classify_archetype(
        shift_distance=shift_distance,
        flip_rate=flip_rate,
        vx=vx, vy=vy, fx=fx, fy=fy,
    )

    # PC-Leaderboard spiegelt 1:1 die Logik von save_leaderboard_csv() (io_manager.py:259-261):
    # nur Datumssuffix-Strip, KEIN Card-Lookup, KEIN Slash→Underscore.
    # Vendor-Schreibweise (z.B. qwen/qwen3-32b) bleibt für die Lesbarkeit erhalten.
    normalized = normalize_model_id(raw_model)
    # OpenRouter-Datumssuffixe strippen (gleiche Logik wie save_leaderboard_csv)
    normalized = _strip_date_suffixes(normalized)

    # Provider aus model_version / Heuristik ableiten
    provider_type = "ollama" if normalized.startswith(("gemma", "qwen", "mistral", "ministral", "llama", "deepseek", "NousResearch", "hf.co")) else "openrouter"

    row = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "model": normalized,
        "model_category": _resolve_model_category(normalized, provider_type),
        "provider_type": provider_type,
        "model_version": avg_row.get("model_version", "").strip(),
        "vanilla_x": vx,
        "vanilla_y": vy,
        "vanilla_label": _build_axis_pair(vx, vy),
        "forced_x": fx,
        "forced_y": fy,
        "forced_label": _build_axis_pair(fx, fy),
        "shift_x": shift_x,
        "shift_y": shift_y,
        "shift_distance": shift_distance,
        "polarity_flip_rate": flip_rate,
        "behavior_archetype": archetype,
        "is_retest": "false",
    }
    return row


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Repariert fehlende Einträge in political_compass_leaderboard.csv aus pc_results.csv."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Nur anzeigen, was repariert würde — keine Schreibvorgänge.",
    )
    args = parser.parse_args()

    if not PC_RESULTS_CSV.exists():
        logger.error("❌ %s nicht gefunden", PC_RESULTS_CSV)
        return 1

    logger.info("Lade bestehendes Leaderboard aus %s", PC_LEADERBOARD_CSV)
    existing = _load_existing_leaderboard()
    logger.info("  → %d vorhandene Einträge", len(existing))

    logger.info("Lese AVG-Zeilen aus %s", PC_RESULTS_CSV)
    candidates: list[dict[str, Any]] = []
    with PC_RESULTS_CSV.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("run_id", "").strip().upper() != "AVG":
                continue
            reconstructed = _reconstruct_leaderboard_row(row)
            if reconstructed:
                candidates.append(reconstructed)
    logger.info("  → %d AVG-Zeilen rekonstruierbar", len(candidates))

    to_add: list[dict[str, Any]] = []
    to_skip: list[str] = []
    for row in candidates:
        if row["model"] in existing:
            to_skip.append(row["model"])
        else:
            to_add.append(row)

    logger.info("Bereits im Leaderboard: %d (übersprungen)", len(to_skip))
    if to_skip:
        for m in to_skip:
            logger.debug("  · vorhanden: %s", m)
    logger.info("Fehlend → werden hinzugefügt: %d", len(to_add))
    for row in to_add:
        logger.info(
            "  · %s — vanilla=(%.2f, %.2f) forced=(%.2f, %.2f) shift=%.2f archetype=%s",
            row["model"], row["vanilla_x"], row["vanilla_y"],
            row["forced_x"], row["forced_y"], row["shift_distance"],
            row["behavior_archetype"],
        )

    if args.dry_run:
        logger.info("--dry-run: Keine Schreibvorgänge. Würde %d Einträge ergänzen.", len(to_add))
        return 0

    if not to_add:
        logger.info("✅ Leaderboard ist bereits konsistent — keine Aktion nötig.")
        return 0

    # Upsert: vorhandene Zeilen behalten, neue hinzufügen
    all_rows = list(existing.values()) + to_add
    PC_LEADERBOARD_CSV.parent.mkdir(parents=True, exist_ok=True)
    with PC_LEADERBOARD_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=LEADERBOARD_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_rows)

    logger.info(
        "💾 %d Einträge ergänzt → %s (jetzt %d Zeilen total)",
        len(to_add), PC_LEADERBOARD_CSV, len(all_rows),
    )
    logger.info("👉 Anschließend: make leaderboard")
    return 0


if __name__ == "__main__":
    sys.exit(main())
