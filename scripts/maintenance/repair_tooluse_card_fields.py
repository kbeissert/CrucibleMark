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

    fixed = 0
    skipped = 0
    missing = 0

    for row in rows:
        raw_id = row.get("model", "")
        model_id = resolve_canonical_model_id(raw_id)
        if not model_id:
            continue

        p1_str = row.get("p1_score", "")
        has_p1_data = p1_str not in ("", "nan", "None")

        card = _load_card(model_id)
        if card is None:
            missing += 1
            logger.debug("Keine Card für %s", model_id)
            continue

        current_val = card.get("supports_tool_use")
        # v4.10.16: Pro-Profil-Check statt flach. Wenn bereits ein Eintrag in
        # tooluse_runs.{model_id} existiert (Standard-Profil oder Single-Profil),
        # ist die Card bereits aktuell — überspringen.
        runs = card.get("tooluse_runs") or {}
        run_entry = runs.get(model_id) if isinstance(runs, dict) else None
        tested_at = (run_entry or {}).get("tested_at") if isinstance(run_entry, dict) else None

        # v4.10.16+: Capability-Flag respektieren. ``supports_tool_use`` ist eine
        # manuelle/auto-generierte Capability-Aussage über das Modell. Nur reparieren,
        # wenn aktueller Wert null/"untested" (kein Claim gesetzt). Bei True/False
        # überspringen — der Test-Indikator ist tooluse_runs.{profile_id}.tested_at,
        # und das Pass/Fail-Signal lebt im Leaderboard.
        if current_val is True or current_val is False:
            skipped += 1
            continue

        # Bestimmen: hat das Modell P1-Daten?
        if has_p1_data:
            try:
                p1_mean = float(p1_str)
            except (ValueError, TypeError):
                p1_mean = 0.0
            correct_val = p1_mean > 0
        else:
            correct_val = "untested"

        # Überschreiben nur wenn aktueller Wert null/untested ist und correct_val abweicht
        if current_val == correct_val:
            skipped += 1
            continue

        logger.info(
            "  · %s: supports_tool_use %s → %s",
            model_id, current_val, correct_val,
        )

        if not args.dry_run:
            from datetime import datetime, timezone

            now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            if correct_val is True:
                card["supports_tool_use"] = True
            elif correct_val is False:
                card["supports_tool_use"] = False
            else:
                card["supports_tool_use"] = "untested"

            # v4.10.16: Nested-Write in tooluse_runs.{model_id}.
            tooluse_runs = card.get("tooluse_runs")
            if not isinstance(tooluse_runs, dict):
                tooluse_runs = {}
            entry = tooluse_runs.get(model_id) or {}
            entry["tested_at"] = now_iso
            if has_p1_data:
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

            # Legacy-Felder entfernen — Migration auf nested-Schema.
            card.pop("tooluse_tested_at", None)
            card.pop("tooluse_score_p1", None)
            card.pop("tooluse_score_p2", None)

            _save_card(model_id, card)

        fixed += 1

    logger.info(
        "Fertig: %d repariert, %d bereits korrekt, %d Cards nicht gefunden",
        fixed, skipped, missing,
    )
    if args.dry_run:
        logger.info("--dry-run: Keine Schreibvorgänge.")
    return 0


if __name__ == "__main__":
    sys.exit(main())