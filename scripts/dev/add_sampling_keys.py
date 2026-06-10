"""
Fügt die 7 Sampling-Default-Felder (v4.7.2) zu allen Model Cards hinzu.

Hintergrund: Sampling-Parameter (top_p, top_k, repetition_penalty, frequency_penalty,
presence_penalty, seed, stop_sequences) sind neu im Template. Wert 'null' bedeutet,
der Pipeline-Default greift — keine Migration von Werten nötig, nur die Schlüssel
müssen da sein, damit Asset-Pipeline/Probe sie optional lesen kann.

Idempotent: bestehende Werte werden nicht überschrieben. Fügt nur fehlende Schlüssel
mit null hinzu.

Usage:
    python scripts/dev/add_sampling_keys.py              # echte Migration
    python scripts/dev/add_sampling_keys.py --dry-run    # nur Bericht
"""

import json
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

CARDS_DIR = Path("benchmark_scores/model_cards")

# Diese Felder müssen in jeder Model Card vorhanden sein (mit null, falls unset).
# SSoT: config/card_template_model.yaml > optional_fields (since v4.7.2).
SAMPLING_DEFAULTS = [
    "top_p",
    "top_k",
    "repetition_penalty",
    "frequency_penalty",
    "presence_penalty",
    "seed",
    "stop_sequences",
]


def migrate_card(path: Path, dry_run: bool = False) -> tuple[bool, list[str]]:
    """Fügt fehlende Sampling-Keys mit null hinzu.

    Returns:
        (changed, added_keys) — changed=True wenn etwas geschrieben wurde.
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return False, [f"JSON-Fehler: {exc}"]

    if not isinstance(data, dict):
        return False, ["kein Dict (vermutlich _index.json)"]

    added: list[str] = []
    for key in SAMPLING_DEFAULTS:
        if key not in data:
            data[key] = None
            added.append(key)

    if added and not dry_run:
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    return bool(added), added


def main() -> int:
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("DRY-RUN: keine Änderungen geschrieben.\n")

    if not CARDS_DIR.exists():
        print(f"ERROR: {CARDS_DIR} nicht gefunden.", file=sys.stderr)
        return 2

    total_changed = 0
    total_unchanged = 0
    total_errors = 0

    for path in sorted(CARDS_DIR.glob("*.json")):
        changed, info = migrate_card(path, dry_run=dry_run)
        if info and "JSON-Fehler" in str(info[0]):
            print(f"  ✗ {path.name}: {info[0]}")
            total_errors += 1
            continue
        if not isinstance(info, list) or (info and "kein Dict" in str(info[0])):
            continue
        if changed:
            verb = "würde hinzufügen" if dry_run else "hinzugefügt"
            print(f"  ✓ {path.name}: {verb}: {', '.join(info)}")
            total_changed += 1
        else:
            total_unchanged += 1

    print("\n" + "─" * 70)
    if dry_run:
        print(f"DRY-RUN Zusammenfassung: {total_changed} Karten würden aktualisiert, "
              f"{total_unchanged} unverändert, {total_errors} Fehler")
    else:
        print(f"Zusammenfassung: {total_changed} geschrieben, "
              f"{total_unchanged} unverändert, {total_errors} Fehler")
    print("─" * 70)

    return 0 if total_errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
