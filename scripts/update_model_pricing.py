#!/usr/bin/env python3
"""
update_model_pricing.py
-----------------------
Aktualisiert die Preise in den Modellkarten basierend auf recherchierten aktuellen Preisen.
Quelle: OpenAI, Anthropic, Google, Mistral (Stand Juni 2026)

Ausführung:
  python scripts/update_model_pricing.py
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import yaml

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from utils.io_helpers import atomic_write_json  # noqa: E402

logger = logging.getLogger(__name__)

PRICING_CONFIG_PATH = ROOT_DIR / "config" / "model_pricing.yaml"


def load_pricing() -> dict[str, dict[str, float]]:
    """Laedt die Preis-SSoT (config/model_pricing.yaml). Fail-Fast bei Fehlern."""
    try:
        data = yaml.safe_load(PRICING_CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as e:
        logger.error(f"Preis-Config nicht lesbar {PRICING_CONFIG_PATH}: {e}")
        return {}
    pricing = (data or {}).get("model_pricing")
    if not isinstance(pricing, dict) or not pricing:
        logger.error(f"Keine 'model_pricing'-Sektion in {PRICING_CONFIG_PATH}")
        return {}
    return pricing



def load_card(path: Path) -> dict | None:
    """Lädt eine Model Card JSON."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error(f"Fehler beim Laden {path}: {e}")
        return None


def save_card(path: Path, data: dict) -> bool:
    """Speichert eine Model Card JSON atomar (Temp-Datei + os.replace)."""
    try:
        atomic_write_json(path, data, indent=2, ensure_ascii=False)
        return True
    except OSError as e:
        logger.error(f"Fehler beim Speichern {path}: {e}")
        return False


def find_matching_price(model_id: str, pricing: dict[str, dict[str, float]]) -> dict | None:
    """Findet die beste passende Preis-Regel für ein Modell.

    Fix 2026-08-15: Laengster-Prefix-Match statt naivem ``split("-")[0:2]`` —
    bisher matchte z.B. "gpt-4o-mini-2024-07-18" auf "gpt-4o" und schrieb
    den vierfachen Mini-Preis in die Card.
    """
    if model_id in pricing:
        return pricing[model_id]

    # Laengsten bekannten Key als Prefix suchen (z.B.
    # "claude-sonnet-4-6-20260101" -> "claude-sonnet-4-6").
    best_key: str | None = None
    for key in pricing:
        if model_id.startswith(key + "-") and (best_key is None or len(key) > len(best_key)):
            best_key = key
    return pricing[best_key] if best_key else None


def update_pricing(cards_dir: Path, pricing: dict[str, dict[str, float]]) -> tuple[int, int, int]:
    """Aktualisiert Preise in allen Modellkarten.

    Returns:
        (updated_count, skipped_count, error_count)
    """
    updated = 0
    skipped = 0
    errors = 0

    cards = sorted(cards_dir.glob("*.json"))

    for card_path in cards:
        card = load_card(card_path)
        if not card or not isinstance(card, dict):
            errors += 1
            continue

        model_id = card.get("model_id", "")
        if not model_id:
            skipped += 1
            continue

        price_data = find_matching_price(model_id, pricing)
        if not price_data:
            logger.debug(f"⏭️  {model_id}: keine Preisregel gefunden")
            skipped += 1
            continue

        old_input = card.get("input_price_per_1m")
        old_output = card.get("output_price_per_1m")
        new_input = price_data["input"]
        new_output = price_data["output"]

        # Nur aktualisieren wenn sich etwas ändert
        if old_input == new_input and old_output == new_output:
            logger.debug(f"✓ {model_id}: Preise bereits korrekt")
            continue

        card["input_price_per_1m"] = new_input
        card["output_price_per_1m"] = new_output
        card["generated_at"] = datetime.now().isoformat() + "+00:00"

        if save_card(card_path, card):
            logger.info(
                f"✅ {model_id}: ${old_input} → ${new_input} (input), "
                f"${old_output} → ${new_output} (output)"
            )
            updated += 1
        else:
            errors += 1

    return updated, skipped, errors


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    cards_dir = ROOT_DIR / "benchmark_scores" / "model_cards"

    if not cards_dir.exists():
        logger.error(f"Verzeichnis nicht gefunden: {cards_dir}")
        sys.exit(1)

    pricing = load_pricing()
    if not pricing:
        sys.exit(1)

    logger.info("🔄 Aktualisiere Modellkarten-Preise...")
    logger.info(f"📂 Quelle: {cards_dir}")
    logger.info(f"📅 Preisstand: {PRICING_CONFIG_PATH.name} ({len(pricing)} Einträge)\n")

    updated, skipped, errors = update_pricing(cards_dir, pricing)

    logger.info("\n" + "="*60)
    logger.info(f"✅ Aktualisiert:  {updated}")
    logger.info(f"⏭️  Übersprungen:  {skipped}")
    logger.info(f"❌ Fehler:        {errors}")
    logger.info("="*60)

    if updated > 0:
        logger.info(f"\n🎯 {updated} Modellkarten erfolgreich aktualisiert!")
    else:
        logger.info("\n⚠️  Keine Preisänderungen vorgenommen.")

    sys.exit(0 if errors == 0 else 1)
