"""One-shot migration: converts supports_tool_use from null to "untested" in all model cards.

Tri-State-Migration
===================

Alte Semantik (bi-state mit null-Trick):
  - True       → Tool-Use funktioniert
  - False      → Tool-Use funktioniert nicht
  - null/absent → nicht getestet (vom Code als False interpretiert)

Neue Semantik (tri-state explizit):
  - True         → Tool-Use funktioniert (empirisch verifiziert)
  - False        → Tool-Use funktioniert nicht (empirisch verifiziert)
  - "untested"   → noch kein Tool-Use-Benchmark gelaufen

Regeln:
  - Karten mit ``supports_tool_use: true`` bleiben unverändert.
  - Karten mit ``supports_tool_use: false`` bleiben unverändert.
  - Karten mit ``supports_tool_use: null`` oder ohne Feld → "untested".
  - Karten mit bereits "untested" bleiben unverändert.
  - Das Feld ``tooluse_tested_at`` wird auf Karten entfernt, die "untested"
    werden, weil kein verifizierter Benchmark-Wert vorliegt.

Usage::

    .venv/bin/python scripts/dev/migrate_supports_tool_use_tri_state.py [--dry-run]

Erzeugt einen Backlog in ``docs/MAINTENANCE_LOG.md`` mit der Liste der
nicht-getesteten Modelle.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
CARDS_DIR = ROOT_DIR / "benchmark_scores" / "model_cards"
MAINTENANCE_LOG = ROOT_DIR / "docs" / "MAINTENANCE_LOG.md"
UNTESTED = "untested"


def migrate_card(card_path: Path, dry_run: bool) -> str | None:
    """Wandelt eine einzelne Karte um.

    Returns:
        Den neuen Status (True/False/"untested") bei Änderung, sonst None.
    """
    try:
        data = json.loads(card_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"  [ERR] {card_path.name}: {exc}", file=sys.stderr)
        return None

    if not isinstance(data, dict):
        return None  # _index.json o.ä. überspringen

    current = data.get("supports_tool_use")
    if current is True or current is False or current == UNTESTED:
        return None  # bereits kanonisch

    if current is None:
        data["supports_tool_use"] = UNTESTED
        data.pop("tooluse_tested_at", None)
        if not dry_run:
            card_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        return UNTESTED

    print(
        f"  [WARN] {card_path.name}: unbekannter Wert {current!r} — übersprungen",
        file=sys.stderr,
    )
    return None


def collect_status(cards_dir: Path) -> dict[str, int]:
    """Zählt Karten je Status (True / False / untested)."""
    counts = {"true": 0, "false": 0, "untested": 0, "other": 0}
    for p in sorted(cards_dir.glob("*.json")):
        if p.name.startswith("_"):
            continue  # _index.json ist ein Array, keine Card
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            counts["other"] += 1
            continue
        if not isinstance(d, dict):
            counts["other"] += 1
            continue
        v = d.get("supports_tool_use")
        if v is True:
            counts["true"] += 1
        elif v is False:
            counts["false"] += 1
        elif v == UNTESTED:
            counts["untested"] += 1
        else:
            counts["other"] += 1
    return counts


def write_backlog(cards_dir: Path, dry_run: bool) -> None:
    """Schreibt die Liste der untested-Modelle in docs/MAINTENANCE_LOG.md."""
    untested_slugs: list[tuple[str, str]] = []
    for p in sorted(cards_dir.glob("*.json")):
        if p.name.startswith("_"):
            continue
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(d, dict):
            continue
        if d.get("supports_tool_use") == UNTESTED:
            display = d.get("display_name") or d.get("model_id") or p.stem
            untested_slugs.append((p.stem, display))

    if not untested_slugs:
        print("Keine untested-Modelle — Backlog wird übersprungen.")
        return

    if dry_run:
        print(f"\n[DRY-RUN] Würde {len(untested_slugs)} untested-Modelle in {MAINTENANCE_LOG.name} listen.")
        for slug, display in untested_slugs[:5]:
            print(f"  - {slug}  ({display})")
        if len(untested_slugs) > 5:
            print(f"  ... und {len(untested_slugs) - 5} weitere")
        return

    section = (
        "\n## Tool-Use-Backlog: nicht getestete Modelle\n\n"
        "Diese Modelle sind in der Karte mit `supports_tool_use: \"untested\"` markiert — "
        "der Tool-Use-Benchmark wurde für sie noch nicht ausgeführt. Ein Tool-Use-Narrative-Review "
        "ist erst möglich, nachdem `make benchmark-tooluse PROVIDER=<...>` gelaufen ist.\n\n"
        "| Slug | Display-Name |\n"
        "|---|---|\n"
        + "".join(f"| `{slug}` | {display} |\n" for slug, display in untested_slugs)
    )

    existing = MAINTENANCE_LOG.read_text(encoding="utf-8") if MAINTENANCE_LOG.exists() else ""
    marker = "## Tool-Use-Backlog: nicht getestete Modelle"
    if marker in existing:
        head, _, tail = existing.partition(marker)
        # alles ab dem Marker bis zum nächsten Top-Level-Header (## ...) verwerfen
        out = head.rstrip() + "\n\n" + section.rstrip() + "\n"
        # tail kann weitere Sektionen enthalten, die mit "## " beginnen
        next_section = tail.find("\n## ")
        if next_section != -1:
            out += "\n" + tail[next_section + 1:].lstrip()
    else:
        out = existing.rstrip() + "\n\n" + section

    MAINTENANCE_LOG.write_text(out, encoding="utf-8")
    print(f"  → {MAINTENANCE_LOG.name} aktualisiert ({len(untested_slugs)} Modelle)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Nur anzeigen, nicht schreiben.",
    )
    args = parser.parse_args()

    if not CARDS_DIR.is_dir():
        print(f"Card-Verzeichnis nicht gefunden: {CARDS_DIR}", file=sys.stderr)
        return 1

    before = collect_status(CARDS_DIR)
    print(f"Vor Migration: {before}")

    changed = 0
    for p in sorted(CARDS_DIR.glob("*.json")):
        if p.name.startswith("_"):
            continue
        if migrate_card(p, args.dry_run) is not None:
            changed += 1
            action = "[DRY] " if args.dry_run else ""
            print(f"  {action}[+] {p.name} → untested")

    after = collect_status(CARDS_DIR)
    print(f"\nNach Migration: {after}")
    print(f"Geänderte Karten: {changed}")

    write_backlog(CARDS_DIR, args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
