#!/usr/bin/env python3
"""
Repariert fehlende `supports_tool_use`-Felder in Model Cards.
=================================================================

Liest `tooluse_leaderboard.csv`, prüft ob jede Model Card das Feld
`supports_tool_use` korrekt gesetzt hat (basierend auf vorhandenen
P1-Scores), und korrigiert fehlende oder falsche Werte.

Hintergrund
-----------
Durch eine stille Exception in `tooluse_exporter.py` (jetzt `logger.warning`)
wurde das Card-Update für einige Modelle übersprungen, sodass
`supports_tool_use` in der Card `None` oder `"untested"` blieb, obwohl
der Tooluse-Benchmark erfolgreich lief.

Idempotenz
----------
Bereits korrekt gesetzte Felder werden NICHT überschrieben.
Beliebig oft ausführbar.

Usage
-----
    python scripts/maintenance/repair_tooluse_card_fields.py --dry-run
    python scripts/maintenance/repair_tooluse_card_fields.py
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from pathlib import Path

# Pfad-Setup
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from utils.model_utils import _find_card, resolve_canonical_model_id  # noqa: E402
from datetime import UTC

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("repair_tooluse_card_fields")

TOOLUSE_LEADERBOARD = ROOT_DIR / "benchmark_scores" / "tooluse_leaderboard.csv"


def _load_leaderboard() -> list[dict[str, str]]:
    if not TOOLUSE_LEADERBOARD.exists():
        logger.error("❌ %s nicht gefunden", TOOLUSE_LEADERBOARD)
        return []
    with TOOLUSE_LEADERBOARD.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _load_card(model_id: str) -> dict[str, object] | None:
    try:
        path = _find_card(model_id)
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("Konnte Card für %s nicht laden: %s", model_id, exc)
    return None


def _save_card(model_id: str, card: dict[str, object]) -> bool:
    try:
        path = _find_card(model_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(card, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return True
    except Exception as exc:
        logger.warning("Konnte Card für %s nicht speichern: %s", model_id, exc)
        return False


def _derive_correct_value(p1_str: str) -> tuple[bool, bool]:
    """Returns (has_p1_data, correct_val)."""
    has_p1_data = p1_str not in ("", "nan", "None")
    if has_p1_data:
        try:
            p1_mean = float(p1_str)
        except (ValueError, TypeError):
            p1_mean = 0.0
        return True, p1_mean > 0
    return False, "untested"


def _should_skip_capability_set(current_val) -> bool:
    """Bereits auf True/False gesetzt → ueberspringen."""
    return current_val is True or current_val is False


def _apply_tooluse_update(card: dict, model_id: str, row: dict, has_p1_data: bool) -> None:
    """Schreibt das neue tooluse_runs/{model_id}-Eintrags-Nested-Schema."""
    from datetime import datetime

    correct_val = card["supports_tool_use"]
    now_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    if correct_val is True:
        card["supports_tool_use"] = True
    elif correct_val is False:
        card["supports_tool_use"] = False
    else:
        card["supports_tool_use"] = "untested"

    tooluse_runs = card.get("tooluse_runs")
    if not isinstance(tooluse_runs, dict):
        tooluse_runs = {}
    entry = tooluse_runs.get(model_id) or {}
    entry["tested_at"] = now_iso
    if has_p1_data:
        p1_str = row.get("p1_score", "")
        try:
            entry["score_p1"] = round(float(p1_str), 2)
        except (ValueError, TypeError):
            pass
        p2_str = row.get("p2_score", "")
        if p2_str not in ("", "nan", "None"):
            try:
                entry["score_p2"] = round(float(p2_str), 2)
            except (ValueError, TypeError):
                pass
    tooluse_runs[model_id] = entry
    if tooluse_runs:
        card["tooluse_runs"] = tooluse_runs

    card.pop("tooluse_tested_at", None)
    card.pop("tooluse_score_p1", None)
    card.pop("tooluse_score_p2", None)


def _process_row(row: dict, dry_run: bool) -> str:
    """Returns 'fixed' | 'skipped' | 'missing'."""
    raw_id = row.get("model", "")
    model_id = resolve_canonical_model_id(raw_id)
    if not model_id:
        return "skipped"

    p1_str = row.get("p1_score", "")
    has_p1_data, correct_val = _derive_correct_value(p1_str)

    card = _load_card(model_id)
    if card is None:
        logger.debug("Keine Card für %s", model_id)
        return "missing"

    current_val = card.get("supports_tool_use")
    if _should_skip_capability_set(current_val):
        return "skipped"

    if current_val == correct_val:
        return "skipped"

    logger.info(
        "  · %s: supports_tool_use %s → %s",
        model_id, current_val, correct_val,
    )

    if not dry_run:
        card["supports_tool_use"] = correct_val
        _apply_tooluse_update(card, model_id, row, has_p1_data)
        _save_card(model_id, card)

    return "fixed"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Repariert fehlende supports_tool_use-Felder in Model Cards."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Nur anzeigen, was repariert würde — keine Schreibvorgänge.",
    )
    args = parser.parse_args()

    rows = _load_leaderboard()
    if not rows:
        return 1

    fixed = skipped = missing = 0
    for row in rows:
        outcome = _process_row(row, dry_run=args.dry_run)
        if outcome == "fixed":
            fixed += 1
        elif outcome == "missing":
            missing += 1
        else:
            skipped += 1

    logger.info(
        "Fertig: %d repariert, %d bereits korrekt, %d Cards nicht gefunden",
        fixed, skipped, missing,
    )
    if args.dry_run:
        logger.info("--dry-run: Keine Schreibvorgänge.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
