#!/usr/bin/env python3
"""
Model Card Template Generator
==============================
Erstellt ein leeres Template für eine neue Model Card.
Alle Felder sind mit Platzhaltern vorbelegt — manuelle Befüllung erforderlich.

Verwendung:
    python scripts/analysis/generate_model_cards.py --model claude-opus-4-7
    python scripts/analysis/generate_model_cards.py --model qwen3:14b --provider ollama_local
    python scripts/analysis/generate_model_cards.py  # interaktive Eingabe
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from utils.model_utils import _card_path, get_model_size_class

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

CARDS_DIR = ROOT_DIR / "benchmark_scores" / "model_cards"


def _build_template(model_id: str) -> dict:
    return {
        "model_id": model_id,
        "display_name": "TODO",
        "developer": "TODO",
        "origin_country": "TODO",
        "developer_jurisdiction": "TODO",
        "deployment_type": "TODO",
        "local_deployment_possible": None,
        "weights_provenance_risk": "TODO",
        "weights_provenance_risk_rationale": "TODO",
        "model_family": "TODO",
        "vendor": "TODO",
        "primary_focus": "TODO",
        "use_case_primary": "generalist",
        "parameter_architecture": "dense",
        "params_total_b": None,
        "params_active_b": None,
        "context_window_k": None,
        "knowledge_cutoff": None,
        "summary": "TODO",
        "strengths": ["TODO"],
        "known_limitations": ["TODO"],
        "judge_context_hint": "TODO",
        "architecture_tags": ["General"],
        "supports_tool_use": None,
        "license": "TODO",
        "license_url": None,
        "commercial_use_allowed": None,
        "weights_license_tier": "TODO",
        "model_version": None,
        "input_price_per_1m": None,
        "output_price_per_1m": None,
        "unknown": False,
        "card_status": "draft",
        "size_class": get_model_size_class(model_id),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


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

    CARDS_DIR.mkdir(parents=True, exist_ok=True)
    card = _build_template(model_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(card, f, ensure_ascii=False, indent=2)

    logger.info("Template erstellt: %s", path)
    _rebuild_index()
    print(f"\nTemplate angelegt: {path}")
    print("Alle 'TODO'-Felder manuell befüllen, dann card_status auf 'complete' setzen.")


if __name__ == "__main__":
    main()
