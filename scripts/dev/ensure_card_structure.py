#!/usr/bin/env python3
"""
ensure_card_structure.py
========================
Stellt sicher, dass Model Cards alle strukturellen Pflichtfelder enthalten.

Idempotent: Felder, die bereits gesetzt sind (auch mit Platzhalter-Wert),
werden nicht verändert. Nur wirklich fehlende Felder werden ergänzt.

Verwendung:
    # Einzelne Card
    .venv/bin/python scripts/dev/ensure_card_structure.py --model gpt-5.5

    # Alle bestehenden Cards
    .venv/bin/python scripts/dev/ensure_card_structure.py --all

    # Nur Cards, denen Felder fehlen (kein Schreibzugriff ohne Bedarf)
    .venv/bin/python scripts/dev/ensure_card_structure.py --missing

    # Vorschau ohne Schreiben
    .venv/bin/python scripts/dev/ensure_card_structure.py --all --dry-run
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from utils.card_utils import CARD_FIELD_NAMES, ensure_card  # noqa: E402

CARDS_DIR = ROOT_DIR / "benchmark_scores" / "model_cards"

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _card_has_missing_fields(card_path: Path) -> bool:
    """Gibt True zurück, wenn der Card ein oder mehr Template-Felder fehlen."""
    try:
        data: dict[str, Any] = json.loads(card_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return True
    return any(field not in data for field in CARD_FIELD_NAMES)


def _report_missing(card_path: Path) -> list[str]:
    """Gibt die Liste fehlender Template-Felder zurück."""
    try:
        data: dict[str, Any] = json.loads(card_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return list(CARD_FIELD_NAMES)
    return [f for f in CARD_FIELD_NAMES if f not in data]


def run_for_card(card_path: Path, dry_run: bool) -> bool:
    """Verarbeitet eine einzelne Card-Datei.

    Returns:
        True wenn Änderungen vorgenommen wurden (oder würden bei --dry-run).
    """
    missing = _report_missing(card_path)
    if not missing:
        logger.debug("OK  %s", card_path.name)
        return False

    if dry_run:
        logger.info("DRY %s  (fehlt: %s)", card_path.name, ", ".join(missing))
        return True

    # model_id aus Datei lesen — falls vorhanden; sonst aus Dateiname ableiten
    try:
        data: dict[str, Any] = json.loads(card_path.read_text(encoding="utf-8"))
        model_id: str = data.get("model_id") or ""
    except (json.JSONDecodeError, OSError):
        model_id = ""

    if not model_id:
        # Fallback: Dateiname rücktransformieren (nur für CLI, nicht für Imports)
        stem = card_path.stem
        model_id = stem.replace("_", "/", 1) if "/" not in stem else stem

    ensure_card(model_id)
    logger.info("FIX %s  (+%d Felder: %s)", card_path.name, len(missing), ", ".join(missing))
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Stellt vollständige Feldstruktur in Model Cards sicher."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--model", metavar="MODEL_ID", help="Einzelnes Modell (model_id)")
    group.add_argument("--all", action="store_true", help="Alle Cards in benchmark_scores/model_cards/")
    group.add_argument("--missing", action="store_true", help="Nur Cards mit fehlenden Feldern")
    parser.add_argument("--dry-run", action="store_true", help="Zeigt was geändert würde, ohne zu schreiben")
    args = parser.parse_args()

    changed = 0

    if args.model:
        if args.dry_run:
            # Für --model --dry-run: Card-Pfad schätzen ohne zu schreiben
            from utils.model_utils import _card_path  # noqa: PLC0415
            try:
                p = _card_path(args.model, for_write=True)
            except Exception:  # noqa: BLE001
                logger.error("Kann Pfad für '%s' nicht auflösen.", args.model)
                return 1
            changed += run_for_card(p, dry_run=True)
        else:
            ensure_card(args.model)
            logger.info("FIX %s", args.model)
            changed = 1

    else:
        cards = sorted(CARDS_DIR.glob("*.json"))
        if not cards:
            logger.warning("Keine Cards gefunden in %s", CARDS_DIR)
            return 0

        for card_path in cards:
            if args.missing and not _card_has_missing_fields(card_path):
                continue
            if run_for_card(card_path, dry_run=args.dry_run):
                changed += 1

    action = "würden aktualisiert werden" if args.dry_run else "aktualisiert"
    print(f"\n{changed} Card(s) {action}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
