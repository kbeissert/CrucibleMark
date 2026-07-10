"""
Migration: Normalisiert architecture_tags gemäß card_vocabulary.yaml.

Für alle Model-Cards in benchmark_scores/model_cards/:
  1. Erkennt deprecated Tags und normalisiert sie (Long Context -> Long-Context,
     Coding -> Coder, MoE -> entfernt wenn redundant, etc.)
  2. Ergänzt fehlende input_modalities / output_modalities Defaults
  3. Leitet Modalitäten heuristisch ab aus architecture_tags und anderen Feldern:
       - "Multimodal" in tags   -> input_modalities: ["text", "image"]
       - "Vision-Capable" in tags -> input_modalities: ["text", "image"]
       - "Audio" (in summary/strengths) -> input_modalities: ["text", "image", "audio"]
       - Andernfalls Default: ["text"]

Usage:
  python scripts/dev/migrate_architecture_tags.py --dry-run   # nur Report
  python scripts/dev/migrate_architecture_tags.py              # schreibt Karten
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# sys.path-Fix: scripts/dev/ ist nicht im Standard-Pfad
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from utils.card_utils import (  # noqa: E402
    clear_vocabulary_cache,
    normalize_tags,
)

logger = logging.getLogger(__name__)

CARDS_DIR = Path("benchmark_scores/model_cards")

# Heuristiken für input_modalities basierend auf Tags und Summary
_AUDIO_HINTS = ("Audio", "audio", "Audio-Input", "Audio-Encoder")


def _infer_input_modalities(card: dict, tags: list[str]) -> list[str]:
    """Leitet input_modalities heuristisch aus Tags und Summary ab."""
    modalities: set[str] = {"text"}
    tags_lower = {t.lower() for t in tags}

    # Vision-Heuristik
    if "Multimodal" in tags or "Vision-Capable" in tags or "multimodal" in tags_lower:
        modalities.add("image")

    # Audio-Heuristik (selten, z.B. Gemma 4 12B)
    summary = (card.get("summary") or "") + " " + " ".join(card.get("strengths") or [])
    if any(hint in summary for hint in _AUDIO_HINTS):
        modalities.add("audio")

    # Sortiert für stabile Ausgabe
    return sorted(modalities, key=lambda m: ["text", "image", "audio", "video"].index(m))


def _infer_output_modalities(card: dict) -> list[str]:
    """Aktuell unterstützen alle LLMs nur Text-Output — Default bleibt."""
    # Falls ein Modell mal Bild-Output haben sollte (z.B. eingebetteter
    # Visual-Decoder), kann das später hier ergänzt werden.
    return ["text"]


def migrate_card(path: Path) -> dict[str, object]:
    """Migriert eine einzelne Card. Returns Report-Dict."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"error": f"JSON-Fehler: {exc}"}

    if not isinstance(data, dict):
        return {"skipped": "kein dict"}

    report: dict[str, object] = {"path": path.name, "changes": []}
    changed = False

    # 1. Tag-Normalisierung
    raw_tags = data.get("architecture_tags", [])
    if isinstance(raw_tags, list):
        normalized, migrations = normalize_tags(raw_tags)
        if migrations:
            for old_tag, new_tag, reason in migrations:
                report["changes"].append(f"tag: {old_tag!r} -> {new_tag!r} ({reason})")
            data["architecture_tags"] = normalized
            changed = True

    # 2. input_modalities ergänzen
    if "input_modalities" not in data:
        inferred = _infer_input_modalities(data, data.get("architecture_tags", []))
        data["input_modalities"] = inferred
        report["changes"].append(f"input_modalities hinzugefügt: {inferred}")
        changed = True

    # 3. output_modalities ergänzen
    if "output_modalities" not in data:
        inferred_out = _infer_output_modalities(data)
        data["output_modalities"] = inferred_out
        report["changes"].append(f"output_modalities hinzugefügt: {inferred_out}")
        changed = True

    if changed:
        report["written"] = True
        # Gebe die migrierten Daten zurück, damit main() sie schreiben kann
        # (kein Re-Read von Disk nötig — verhindert, dass un-migrierte Tags
        # versehentlich zurückgeschrieben werden).
        report["data"] = data

    return report


def main(dry_run: bool) -> int:
    clear_vocabulary_cache()

    if not CARDS_DIR.exists():
        print(f"ERROR: {CARDS_DIR} existiert nicht.", file=sys.stderr)
        return 1

    card_files = sorted(p for p in CARDS_DIR.glob("*.json") if p.name != "_index.json")
    print(f"\nMigrate architecture_tags — {len(card_files)} Karten geprüft")
    print(f"{'─' * 70}")
    if dry_run:
        print("DRY RUN — keine Dateien geschrieben\n")
    else:
        print("WRITE — Karten werden aktualisiert\n")

    written = 0
    no_changes = 0
    errors = 0

    for path in card_files:
        report = migrate_card(path)
        if "error" in report:
            print(f"  ✗ {path.name}: {report['error']}")
            errors += 1
            continue
        if "skipped" in report:
            continue
        if report.get("changes"):
            print(f"  ✓ {path.name}:")
            for change in report["changes"]:
                print(f"      - {change}")
            if not dry_run and report.get("written"):
                # Schreibt die in migrate_card() normalisierten Daten — kein
                # Re-Read von Disk (Bug: würde un-migrierte Tags zurückschreiben).
                path.write_text(
                    json.dumps(report["data"], ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                written += 1
        else:
            no_changes += 1

    print(f"\n{'─' * 70}")
    print(f"Zusammenfassung: {written} geschrieben, {no_changes} unverändert, {errors} Fehler")
    print(f"{'─' * 70}\n")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate architecture_tags in Model Cards.")
    parser.add_argument("--dry-run", action="store_true", help="Nur Report, keine Schreibvorgänge.")
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
    sys.exit(main(dry_run=args.dry_run))
