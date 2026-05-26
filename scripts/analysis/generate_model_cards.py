#!/usr/bin/env python3
"""
Model Card Template Generator
==============================
Erstellt ein leeres Template für eine neue Model Card.
Alle Felder sind mit Platzhaltern vorbelegt — manuelle Befüllung erforderlich.

Feldstruktur-SSoT: ``utils/card_utils.py`` (``ensure_card()``).

Verwendung:
    python scripts/analysis/generate_model_cards.py --model claude-opus-4-7
    python scripts/analysis/generate_model_cards.py --model qwen3:14b --provider ollama_local
    python scripts/analysis/generate_model_cards.py  # interaktive Eingabe
"""

import json
import logging
import sys
from pathlib import Path

import argparse

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from utils.card_utils import ensure_card
from utils.model_utils import _card_path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

CARDS_DIR = ROOT_DIR / "benchmark_scores" / "model_cards"


def _rebuild_index() -> None:
    cards = []
    for p in sorted(CARDS_DIR.glob("*.json")):
        if p.name == "_index.json":
            continue
        try:
            cards.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception as e:
            logger.warning("Konnte %s nicht lesen: %s", p.name, e)
    index_path = CARDS_DIR / "_index.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(cards, f, ensure_ascii=False, indent=2)
    logger.info("_index.json aktualisiert (%d Karten).", len(cards))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Erstellt ein leeres Model Card Template."
    )
    parser.add_argument("--model", type=str, default=None, help="Model-ID (z.B. claude-opus-4-7)")
    parser.add_argument(
        "--provider",
        type=str,
        default=None,
        help="Provider-Schlüssel für lokale/namespaced Modelle (z.B. ollama_local)",
    )
    parser.add_argument("--force", action="store_true", help="Bestehende Card überschreiben")
    args = parser.parse_args()

    model_id = args.model
    if not model_id:
        model_id = input("Model-ID eingeben (z.B. claude-opus-4-7): ").strip()
    if not model_id:
        logger.error("Keine Model-ID angegeben.")
        sys.exit(1)

    path = _card_path(model_id, args.provider, for_write=True)

    if path.exists() and not args.force:
        logger.error("Card existiert bereits: %s — nutze --force zum Überschreiben.", path.name)
        sys.exit(1)

    # Bei --force: bestehende Card entfernen, damit ensure_card ein frisches Template anlegt
    if args.force and path.exists():
        path.unlink()
        logger.info("Bestehende Card gelöscht (--force): %s", path.name)

    result_path = ensure_card(model_id, card_path=path)
    logger.info("Template erstellt: %s", result_path)
    _rebuild_index()
    print(f"\nTemplate angelegt: {result_path}")
    print("Alle 'TODO'-Felder manuell befüllen, dann card_status auf 'complete' setzen.")


if __name__ == "__main__":
    main()
