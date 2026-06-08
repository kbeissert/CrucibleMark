#!/usr/bin/env python3
"""Provider Card Status-Check (Phase 22).

CLI-Wrapper um ``utils.provider_card_template.get_provider_card_status``.
Ausgabe lesbar (Default) oder als JSON für CI/Cron.

Verwendung:
    python scripts/analysis/provider_card_status.py
    python scripts/analysis/provider_card_status.py --stale-days 60 --json
    make provider-cards-status STALE_DAYS=60 JSON=1
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from utils.provider_card_template import (
    format_provider_card_status,
    get_provider_card_status,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit-Readiness-Report für alle Provider Cards."
    )
    parser.add_argument(
        "--stale-days",
        type=int,
        default=90,
        help="Schwellwert (Tage) für stale-Klassifikation (default: 90).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Report als JSON ausgeben (statt lesbarem CLI-Format).",
    )
    parser.add_argument(
        "--fail-on-unknown",
        action="store_true",
        help="Exit-Code 1 wenn unknown-Cards gefunden (für CI-Gates).",
    )
    parser.add_argument(
        "--fail-on-stale",
        action="store_true",
        help="Exit-Code 1 wenn stale-Cards gefunden (für CI-Gates).",
    )
    args = parser.parse_args()

    report = get_provider_card_status(stale_days=args.stale_days)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_provider_card_status(report))

    # CI-Gates
    if args.fail_on_unknown and report["unknown"] > 0:
        print(f"\n❌ CI-Gate fehlgeschlagen: {report['unknown']} unknown Card(s).", file=sys.stderr)
        return 1
    if args.fail_on_stale and report["stale"] > 0:
        print(f"\n❌ CI-Gate fehlgeschlagen: {report['stale']} stale Card(s).", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
