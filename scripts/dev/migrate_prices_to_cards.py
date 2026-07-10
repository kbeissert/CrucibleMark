"""
migrate_prices_to_cards.py
--------------------------
One-time migration: copies pricing from config/cost_limits.yaml → model card JSON files.

Converts input_cost_per_1k / output_cost_per_1k (per 1K tokens) to
input_price_per_1m / output_price_per_1m (per 1M tokens) in each matching card.

-latest/-latest aliases are skipped (no dedicated versioned cards).

Usage:
    .venv/bin/python scripts/dev/migrate_prices_to_cards.py
    .venv/bin/python scripts/dev/migrate_prices_to_cards.py --dry-run
"""

import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from utils.model_utils import _find_card  # noqa: E402

CARD_DIR = ROOT / "benchmark_scores" / "model_cards"
COST_LIMITS = ROOT / "config" / "cost_limits.yaml"

_ALIAS_SUFFIXES = ("-latest", ":latest")

# Regex: Suffix after the base model_id must be digits-only or digit groups separated by dashes.
# Accepts: '20260406', '0127', '4-5-20251001' — Rejects: '1-fast-reasoning' (letters)
import re as _re
_DATE_SUFFIX_RE = _re.compile(r"^\d[\d-]*\d$|^\d+$")


def _is_alias(model_id: str) -> bool:
    return any(model_id.endswith(s) for s in _ALIAS_SUFFIXES)


def _is_date_suffix_variant(card_model_id: str, base_model_id: str) -> bool:
    """True if card_model_id is a date-suffixed variant of base_model_id.

    E.g. 'z-ai/glm-5.1-20260406' is a variant of 'z-ai/glm-5.1'
         'moonshotai/kimi-k2.5-0127' is a variant of 'moonshotai/kimi-k2.5'
    NOT: 'grok-4-1-fast-reasoning' is NOT a variant of 'grok-4' (non-numeric suffix)
    """
    if not card_model_id.startswith(base_model_id):
        return False
    remainder = card_model_id[len(base_model_id):]
    if not remainder.startswith("-"):
        return False
    suffix = remainder[1:]
    return bool(_DATE_SUFFIX_RE.match(suffix))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Migrate pricing from cost_limits.yaml to model cards"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be done without writing"
    )
    args = parser.parse_args()

    with open(COST_LIMITS, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    migrated: list[str] = []
    already_set: list[str] = []
    skipped_alias: list[str] = []
    no_card: list[str] = []

    providers = data.get("providers", {})
    for provider, models in providers.items():
        if not isinstance(models, dict):
            continue
        for model_id, model_data in models.items():
            if not isinstance(model_data, dict):
                continue
            in_price = model_data.get("input_cost_per_1k")
            out_price = model_data.get("output_cost_per_1k")
            if not isinstance(in_price, (int, float)) or not isinstance(out_price, (int, float)):
                continue

            if _is_alias(model_id):
                skipped_alias.append(f"[{provider}] {model_id}")
                continue

            card_path = _find_card(model_id, card_dir=CARD_DIR)
            if not card_path.exists():
                no_card.append(f"[{provider}] {model_id}  (expected: {card_path.name})")
                continue

            with open(card_path, encoding="utf-8") as f:
                card = json.load(f)

            # Validate that the found card actually belongs to this model_id.
            # _find_card() may return a wrong card via glob fallback (e.g. grok-4 → grok-4-1-fast-reasoning.json).
            card_model_id = card.get("model_id")
            if card_model_id != model_id:
                if not _is_date_suffix_variant(card_model_id or "", model_id):
                    no_card.append(
                        f"[{provider}] {model_id}  (card {card_path.name} belongs to '{card_model_id}')"
                    )
                    continue
                # Date-suffixed variant: e.g. cost_limits uses 'z-ai/glm-5.1',
                # but the card has model_id 'z-ai/glm-5.1-20260406'. Valid match.
                variant_note = f" [variant: card model_id={card_model_id}]"
            else:
                variant_note = ""

            if "input_price_per_1m" in card and "output_price_per_1m" in card:
                already_set.append(f"[{provider}] {model_id}")
                continue

            in_per_m = round(float(in_price) * 1000, 6)
            out_per_m = round(float(out_price) * 1000, 6)

            if not args.dry_run:
                card["input_price_per_1m"] = in_per_m
                card["output_price_per_1m"] = out_per_m
                with open(card_path, "w", encoding="utf-8") as f:
                    json.dump(card, f, indent=2, ensure_ascii=False)
                    f.write("\n")

            migrated.append(
                f"[{provider}] {model_id}  →  {card_path.name}"
                f"  (${in_per_m}/M in, ${out_per_m}/M out){variant_note}"
            )

    dry = "  [DRY RUN]" if args.dry_run else ""

    print(f"\n✓  Migriert{dry} ({len(migrated)}):")
    for m in migrated:
        print(f"   {m}")

    print(f"\n⏭  Bereits gesetzt ({len(already_set)}):")
    for m in already_set:
        print(f"   {m}")

    print(f"\n⚠  Alias übersprungen — kein 1:1-Card-Match ({len(skipped_alias)}):")
    for m in skipped_alias:
        print(f"   {m}")

    print(f"\n✗  Kein Card-Match ({len(no_card)}):")
    for m in no_card:
        print(f"   {m}")

    if not args.dry_run and migrated:
        print(f"\n→ {len(migrated)} Cards aktualisiert. Bitte `make leaderboard` ausführen.")


if __name__ == "__main__":
    main()
