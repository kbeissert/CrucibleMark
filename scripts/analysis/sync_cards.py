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

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import cast

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from utils.card_sync import CardType, SyncPlan, format_summary, sync_all, apply_sync  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def _resolve_single_card_path(model_id: str, card_type: str) -> Path:
    """Bestimmt den kanonischen Pfad einer einzelnen Card anhand der ID.

    Args:
        model_id: Model-ID (z.B. ``claude-sonnet-4-6``) oder Vendor-ID.
        card_type: ``"model"`` oder ``"vendor"``.

    Returns:
        Pfad zur Card-Datei. Existenz wird vom Aufrufer geprüft.

    Raises:
        SystemExit: Wenn die Card nicht gefunden wird.
    """
    if card_type == "model":
        from utils.model_utils import _find_card  # noqa: PLC0415
        path = _find_card(model_id)
        if not path.exists():
            raise SystemExit(f"❌ Model-Card nicht gefunden: {model_id}")
        return path
    from utils.vendor_card_template import CARDS_DIR, _safe_id  # noqa: PLC0415
    path = CARDS_DIR / f"{_safe_id(model_id)}.json"
    if not path.exists():
        raise SystemExit(f"❌ Vendor-Card nicht gefunden: {model_id}")
    return path


def _collect_sync_plans(args: argparse.Namespace) -> list[SyncPlan]:
    """Sammelt alle Sync-Pläne für die gewählten Card-Typen."""
    if args.model:
        card_type = args.card_type if args.card_type != "all" else "model"
        path = _resolve_single_card_path(args.model, card_type)
        plan = apply_sync(
            path, card_type, dry_run=args.dry_run, yes=args.yes,
        )
        return [plan]
    else:
        card_types = ["model", "vendor"] if args.card_type == "all" else [args.card_type]
        plans = []
        for ct in card_types:
            plans.extend(sync_all(cast(CardType, ct), dry_run=args.dry_run, yes=args.yes))
        return plans


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
        choices=["model", "vendor", "all"],
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
    parser.add_argument(
        "--model",
        type=str,
        help=(
            "Nur diese eine Card synchronisieren (Modell-ID oder Vendor-ID). "
            "Impliziert --card-type=model, falls --card-type=all oder weggelassen."
        ),
    )
    args = parser.parse_args()

    all_plans = _collect_sync_plans(args)

    if args.json:
        import json as _json  # noqa: PLC0415
        report = {
            "dry_run": args.dry_run,
            "yes": args.yes,
            "card_types": (
                [args.card_type if args.card_type != "all" else "model"]
                if args.model
                else (["model", "vendor"] if args.card_type == "all" else [args.card_type])
            ),
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
        sys.exit(1)


if __name__ == "__main__":
    main()
