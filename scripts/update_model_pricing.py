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
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Recherchierte Preise (USD pro 1 Million Tokens)
# Stand: 10.06.2026
CURRENT_PRICING = {
    # OpenAI — aus OpenAI API Pricing (2026)
    "gpt-5-5": {"input": 5.00, "output": 30.00},
    "gpt-5-5-pro": {"input": 30.00, "output": 180.00},
    "gpt-5-4": {"input": 2.50, "output": 15.00},
    "gpt-5-4-mini": {"input": 0.75, "output": 4.50},
    "gpt-5-4-nano": {"input": 0.20, "output": 1.25},
    "gpt-5-4-pro": {"input": 30.00, "output": 180.00},
    "gpt-5": {"input": 2.50, "output": 15.00},  # Fallback
    "gpt-5-mini": {"input": 0.75, "output": 4.50},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-2024-08-06": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 1.25, "output": 5.00},
    
    # Anthropic — aus Anthropic API Pricing (2026)
    "claude-opus-4-6": {"input": 5.00, "output": 25.00},
    "claude-opus-4-5-20251101": {"input": 5.00, "output": 25.00},
    "claude-opus-4-7": {"input": 5.00, "output": 25.00},
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "claude-sonnet-4-5-20250929": {"input": 3.00, "output": 15.00},
    "claude-haiku-4-5-20251001": {"input": 1.00, "output": 5.00},
    
    # Google Gemini — aus Google AI Pricing (2026)
    "gemini-3-5-flash": {"input": 1.50, "output": 9.00},
    "gemini-3-1-flash-lite-preview": {"input": 0.25, "output": 1.50},
    "gemini-3-1-pro-preview": {"input": 2.00, "output": 12.00},
    "gemini-3-flash-preview": {"input": 0.50, "output": 3.00},
    "gemini-2-5-flash": {"input": 0.30, "output": 2.50},
    "gemini-2-5-pro": {"input": 1.25, "output": 10.00},
    
    # Mistral — aus Mistral API Pricing (2026)
    "mistral-large-2512": {"input": 2.00, "output": 6.00},
    "mistral-large-2411": {"input": 2.00, "output": 6.00},
    "mistral-medium-3-5": {"input": 1.50, "output": 7.50},
    "mistral-small-2603": {"input": 0.10, "output": 0.30},
    "mistral-small-2503": {"input": 0.10, "output": 0.30},
    "magistral-medium-latest": {"input": 1.50, "output": 7.50},
    "magistral-small-latest": {"input": 0.50, "output": 1.50},
    "ministral-3_14b": {"input": 0.20, "output": 0.20},
    "ministral-3_8b": {"input": 0.10, "output": 0.10},
    
    # xAI Grok — aus Grok API
    "grok-3": {"input": 5.00, "output": 15.00},
    "grok-3-mini": {"input": 0.50, "output": 1.50},
}


def load_card(path: Path) -> Optional[Dict]:
    """Lädt eine Model Card JSON."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error(f"Fehler beim Laden {path}: {e}")
        return None


def save_card(path: Path, data: Dict) -> bool:
    """Speichert eine Model Card JSON mit Formatting."""
    try:
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8"
        )
        return True
    except Exception as e:
        logger.error(f"Fehler beim Speichern {path}: {e}")
        return False


def find_matching_price(model_id: str) -> Optional[Dict]:
    """Findet die beste passende Preis-Regel für ein Modell."""
    # Exakter Match
    if model_id in CURRENT_PRICING:
        return CURRENT_PRICING[model_id]
    
    # Vereinfachte Modell-ID probieren (z.B. "gpt-4o-2024-08-06" → "gpt-4o")
    base_id = model_id.split("-")[0:2]
    if len(base_id) >= 2:
        simplified = "-".join(base_id)
        if simplified in CURRENT_PRICING:
            return CURRENT_PRICING[simplified]
    
    return None


def update_pricing(cards_dir: Path) -> tuple[int, int, int]:
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
        
        price_data = find_matching_price(model_id)
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
    cards_dir = Path("benchmark_scores/model_cards")
    
    if not cards_dir.exists():
        logger.error(f"Verzeichnis nicht gefunden: {cards_dir}")
        exit(1)
    
    logger.info("🔄 Aktualisiere Modellkarten-Preise...")
    logger.info(f"📂 Quelle: {cards_dir}")
    logger.info(f"📅 Preisstand: Juni 2026 (OpenAI, Anthropic, Google, Mistral)\n")
    
    updated, skipped, errors = update_pricing(cards_dir)
    
    logger.info("\n" + "="*60)
    logger.info(f"✅ Aktualisiert:  {updated}")
    logger.info(f"⏭️  Übersprungen:  {skipped}")
    logger.info(f"❌ Fehler:        {errors}")
    logger.info("="*60)
    
    if updated > 0:
        logger.info(f"\n🎯 {updated} Modellkarten erfolgreich aktualisiert!")
    else:
        logger.info("\n⚠️  Keine Preisänderungen vorgenommen.")
    
    exit(0 if errors == 0 else 1)
