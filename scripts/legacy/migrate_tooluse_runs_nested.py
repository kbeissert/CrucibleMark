#!/usr/bin/env python3
"""Migration: Card.tooluse_tested_at/_score_p1/_score_p2 (flat) → tooluse_runs.{model_id} (nested).

Hintergrund
-----------
Mit v4.10.16 wird der per-Profil-Run-State (Standard vs. Thinking) unter
``tooluse_runs.{model_id}`` in der Card persistiert statt in flachen
Top-Level-Feldern. Beide Profile derselben Card (via ``card_model_id``-Redirect)
schreiben damit in separate Slots — keine Race Condition mehr.

Was dieses Script tut
---------------------
1. Liest jede Card in ``benchmark_scores/model_cards/``.
2. Erkennt Legacy-Felder ``tooluse_tested_at``, ``tooluse_score_p1``, ``tooluse_score_p2``.
3. Migriert in ``tooluse_runs.{card.model_id}`` (Profil = Basis-ID der Card).
4. Entfernt die Legacy-Felder.
5. Idempotent: bereits migrierte Cards werden nicht erneut angefasst.

Dry-Run
-------
Standard ist ``--apply`` AUS — nur Diagnose-Output. Erst nach explizitem
``--apply`` werden Cards geschrieben.

Usage
-----
    python scripts/dev/migrate_tooluse_runs_nested.py --dry-run
    python scripts/dev/migrate_tooluse_runs_nested.py --apply
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))


CARD_DIR = ROOT_DIR / "benchmark_scores" / "model_cards"
LOG_FMT = "%(asctime)s [%(levelname)s] %(message)s"


def _load_card(card_path: Path) -> dict | None:
    try:
        return json.loads(card_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logging.warning("Card nicht lesbar %s: %s", card_path, exc)
        return None


def _save_card(card_path: Path, data: dict) -> bool:
    try:
        card_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return True
    except OSError as exc:
        logging.warning("Card nicht schreibbar %s: %s", card_path, exc)
        return False


def _needs_migration(card: dict) -> bool:
    """True wenn Card Legacy-Felder oder leere tooluse_runs-Einträge hat.

    Pitfall-Diagnose 2026-07-10: Vorherige Migration-Version erstellte
    ``tooluse_runs.{profile_id}``-Einträge mit ``tested_at: null`` für Cards
    mit ``tooluse_tested_at: null``. Solche Einträge signalisieren fälschlich
    einen Test-Lauf. Cleanup-Pass entfernt sie.
    """
    legacy_present = any(
        k in card for k in ("tooluse_tested_at", "tooluse_score_p1", "tooluse_score_p2")
    )
    empty_entries = _has_empty_run_entries(card)
    return legacy_present or empty_entries


def _has_empty_run_entries(card: dict) -> bool:
    """True wenn tooluse_runs Einträge mit tested_at=null enthält."""
    runs = card.get("tooluse_runs")
    if not isinstance(runs, dict):
        return False
    for entry in runs.values():
        if isinstance(entry, dict) and entry.get("tested_at") is None:
            return True
    return False


def _clean_empty_run_entries(card: dict) -> bool:
    """Entfernt tooluse_runs-Einträge mit tested_at=null. Returns did_clean."""
    runs = card.get("tooluse_runs")
    if not isinstance(runs, dict):
        return False
    did_clean = False
    to_remove = [
        k for k, v in runs.items()
        if isinstance(v, dict) and v.get("tested_at") is None
    ]
    for k in to_remove:
        runs.pop(k)
        did_clean = True
    if not runs:
        card.pop("tooluse_runs", None)
    elif did_clean:
        card["tooluse_runs"] = runs
    return did_clean


def _migrate_card(card: dict, base_id: str) -> tuple[dict, bool]:
    """Migriert Legacy-Felder in tooluse_runs.{base_id}.

    Returns: (mutated_card, did_migrate)
    """
    if not _needs_migration(card):
        return card, False

    tooluse_runs = card.get("tooluse_runs")
    if not isinstance(tooluse_runs, dict):
        tooluse_runs = {}

    # Bestehenden Eintrag respektieren (z.B. wenn schon ein Thinking-Run da ist)
    entry = tooluse_runs.get(base_id) or {}

    # Legacy-Felder übernehmen — NUR wenn Wert nicht None ist. Cards mit
    # ``tooluse_tested_at: null`` waren nie getestet und bekommen keinen
    # ``tooluse_runs``-Eintrag (würde sonst fälschlich "getestet" signalisieren).
    if card.get("tooluse_tested_at") and "tested_at" not in entry:
        entry["tested_at"] = card["tooluse_tested_at"]
    p1_val = card.get("tooluse_score_p1")
    if p1_val is not None and "score_p1" not in entry:
        try:
            entry["score_p1"] = round(float(p1_val), 2)
        except (ValueError, TypeError):
            pass
    p2_val = card.get("tooluse_score_p2")
    if p2_val is not None and "score_p2" not in entry:
        try:
            entry["score_p2"] = round(float(p2_val), 2)
        except (ValueError, TypeError):
            pass

    # Eintrag nur schreiben wenn mindestens tested_at gesetzt ist — sonst
    # wäre der Eintrag leer und würde fälschlich einen Run suggerieren.
    if entry:
        tooluse_runs[base_id] = entry
        card["tooluse_runs"] = tooluse_runs

    # Legacy-Felder entfernen
    card.pop("tooluse_tested_at", None)
    card.pop("tooluse_score_p1", None)
    card.pop("tooluse_score_p2", None)

    # Cleanup: leere tooluse_runs-Einträge (tested_at=null) entfernen
    _clean_empty_run_entries(card)

    return card, True


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Migriert Card-Top-Level-Felder tooluse_tested_at/_score_p1/_score_p2 "
            "in nested tooluse_runs.{model_id}."
        ),
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Schreibt migrierte Cards. Ohne dieses Flag: nur Dry-Run.",
    )
    parser.add_argument(
        "--card-dir",
        type=Path,
        default=CARD_DIR,
        help=f"Card-Verzeichnis (default: {CARD_DIR})",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format=LOG_FMT, datefmt="%H:%M:%S")
    logger = logging.getLogger("migrate_tooluse_runs_nested")

    if not args.card_dir.exists():
        logger.error("Card-Verzeichnis nicht gefunden: %s", args.card_dir)
        return 1

    migrated = 0
    skipped = 0
    failed = 0

    for card_path in sorted(args.card_dir.glob("*.json")):
        card = _load_card(card_path)
        if card is None:
            failed += 1
            continue

        base_id = card.get("model_id")
        if not isinstance(base_id, str) or not base_id:
            # Karte ohne model_id (Draft?) — überspringen
            skipped += 1
            continue

        if not _needs_migration(card):
            skipped += 1
            continue

        _, did_migrate = _migrate_card(card, base_id)
        if not did_migrate:
            skipped += 1
            continue

        # Vor-Migration-Snapshot für Log
        if args.apply:
            ok = _save_card(card_path, card)
            if ok:
                logger.info("  ✓ %s → tooluse_runs.%s", card_path.name, base_id)
                migrated += 1
            else:
                failed += 1
        else:
            logger.info("  [DRY-RUN] %s würde migriert werden", card_path.name)
            migrated += 1

    mode = "APPLY" if args.apply else "DRY-RUN"
    logger.info(
        "%s: %d migriert, %d übersprungen, %d fehlgeschlagen",
        mode, migrated, skipped, failed,
    )
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
