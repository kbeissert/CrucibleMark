#!/usr/bin/env python3
"""
sync_cards.py — SSoT-Sync zwischen Card-Template und Karten-Dateien (CLI)
==========================================================================

Synchronisiert JSON-Karten in ``benchmark_scores/{provider,model}_cards/`` mit
dem kanonischen Python-Dict-Template.

Vorwärts (Add):  Template-Feld fehlt in Karte → mit Default ergänzen
Rückwärts (Delete):  Feld in Karte, nicht im Template → nach Bestätigung entfernen

Löschungen erfordern eine Bestätigung pro Karte (gesammelt). Mit ``--yes``
wird die Bestätigung übersprungen.

Verwendung:
    python scripts/analysis/sync_cards.py --card-type provider --dry-run
    python scripts/analysis/sync_cards.py --card-type model --yes
    python scripts/analysis/sync_cards.py --card-type all
"""

import argparse
import logging
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from utils.card_sync import format_summary, sync_all  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Synchronisiert Card-JSON-Dateien mit dem Python-Dict-Template. "
            "Neue Template-Felder werden ergänzt, entfernte Felder werden "
            "nach Bestätigung aus den Karten gelöscht."
        )
    )
    parser.add_argument(
        "--card-type",
        choices=["model", "provider", "all"],
        default="all",
        help="Welcher Card-Typ synchronisiert werden soll (default: all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Nur Vorschau — nichts schreiben",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Lösch-Bestätigung automatisch mit 'ja' beantworten",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output als JSON-Report (für CI-Parsing)",
    )
    args = parser.parse_args()

    card_types = ["model", "provider"] if args.card_type == "all" else [args.card_type]
    all_plans = []
    for ct in card_types:
        plans = sync_all(ct, dry_run=args.dry_run, yes=args.yes)
        all_plans.extend(plans)

    if args.json:
        import json as _json  # noqa: PLC0415
        report = {
            "dry_run": args.dry_run,
            "yes": args.yes,
            "card_types": card_types,
            "plans": [
                {
                    "card": str(p.card_path),
                    "card_type": p.card_type,
                    "adds": p.add_count,
                    "deletes": p.delete_count,
                    "actions": [
                        {"kind": a.kind, "field": a.field, "reason": a.reason}
                        for a in p.actions
                        if a.kind != "keep"
                    ],
                }
                for p in all_plans
            ],
        }
        print(_json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_summary(all_plans))

    # Exit-Code: 1 wenn es Löschungen gab, die nicht durchgeführt wurden
    # (Dry-Run mit Deletes signalisiert: User soll prüfen)
    if args.dry_run and any(p.delete_count > 0 for p in all_plans):
        sys.exit(0)  # dry-run ist immer exit 0; nur Info


if __name__ == "__main__":
    main()
