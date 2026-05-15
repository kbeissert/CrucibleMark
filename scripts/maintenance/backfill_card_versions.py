"""
Backfill `model_version` field into all model cards that are missing it.

Uses get_model_version() (Card-First logic is bypassed because the field
doesn't exist yet; the regex/heuristic fallback produces the version).

Run once after this change; future benchmark runs write the field automatically
because generate_model_cards.py will be updated to include it.

Usage:
    python scripts/maintenance/backfill_card_versions.py [--dry-run]
"""
import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from utils.model_utils import get_model_version  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

CARD_DIR = ROOT / "benchmark_scores" / "model_cards"
SKIP_FILES = {"_all_cards.md", "_index.json"}


def _infer_provider(card: dict) -> str:
    """Returns a provider string suitable for get_model_version().

    For local/Ollama models we pass 'ollama' so the hash lookup fires.
    For API-only (commercial) models we pass 'api' to skip the Ollama lookup.
    """
    if card.get("deployment_type") == "api-only":
        return "api"
    if card.get("local_deployment_possible") is True:
        # Ollama or other local deployment — try the hash lookup
        model_id: str = card.get("model_id", "")
        if "/" in model_id:
            return "api"  # namespaced OR/Groq model hosted via API
        return "ollama"
    return "api"


def run(dry_run: bool) -> None:
    cards = sorted(CARD_DIR.glob("*.json"))
    updated = 0
    skipped = 0

    for card_path in cards:
        if card_path.name in SKIP_FILES:
            continue

        try:
            card = json.loads(card_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            log.warning("  SKIP (unlesbar): %s — %s", card_path.name, exc)
            continue

        # Already has a non-empty version → skip
        existing = str(card.get("model_version", "")).strip()
        if existing and existing not in ("unknown", "k.A.", ""):
            skipped += 1
            continue

        model_id: str = card.get("model_id", "").strip()
        if not model_id:
            log.warning("  SKIP (keine model_id): %s", card_path.name)
            continue

        provider = _infer_provider(card)
        version = get_model_version(model_id, provider)

        if not version or version in ("k.A.", "unknown"):
            log.warning("  SKIP (keine Version ermittelbar): %s", card_path.name)
            continue

        log.info("  %s  →  model_version = %s", card_path.name, version)

        if not dry_run:
            card["model_version"] = version
            card_path.write_text(
                json.dumps(card, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        updated += 1

    mode = "[DRY-RUN] " if dry_run else ""
    log.info("\n%sFertig: %d aktualisiert, %d bereits vorhanden.", mode, updated, skipped)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill model_version in all model cards.")
    parser.add_argument("--dry-run", action="store_true", help="Nur anzeigen, nicht schreiben.")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
