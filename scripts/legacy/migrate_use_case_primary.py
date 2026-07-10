"""
Migration: Add use_case_primary field to all model cards.

Auto-assigns based on existing architecture_tags / primary_focus.
Priority:
  1. primary_focus == "coding"           → "coding"
  2. tags contains "Vision" or "Multimodal" → "vision-language"
  3. primary_focus == "reasoning"        → "reasoning"  (explicit card override)
  4. tags contains "Agentic-Orchestrator" → "agentic"
  5. tags contains only "Coder" (no "General" tag) → "coding"
  6. tags contains "Thinking" (not "Thinking-Optional") → "reasoning"
  7. fallback                            → "generalist"

Notes:
- "Thinking-Optional" alone → "generalist" (feature, not purpose)
- "Coder" alongside "General" → "generalist" (capable of coding, not specialized)
- "Agentic-Orchestrator" takes priority over "Coder" (more specific purpose)

Usage:
  python scripts/dev/migrate_use_case_primary.py           # apply to all cards
  python scripts/dev/migrate_use_case_primary.py --dry-run  # report only
"""

import argparse
import json
import sys
from pathlib import Path

CARD_DIR = Path("benchmark_scores/model_cards")
VALID_VALUES = {"generalist", "coding", "reasoning", "vision-language", "agentic"}


def _infer_use_case(card: dict) -> tuple[str, str]:
    """Returns (use_case_primary, basis_of_assignment)."""
    primary_focus = card.get("primary_focus", "")
    tags: list[str] = card.get("architecture_tags", [])

    if primary_focus == "coding":
        return "coding", "primary_focus=coding"

    if "Vision" in tags or "Multimodal" in tags:
        return "vision-language", "architecture_tags contains Vision/Multimodal"

    # Explicit card-level reasoning override (e.g. Gemini 2.5 Pro, kimi-k2-thinking)
    if primary_focus == "reasoning":
        return "reasoning", "primary_focus=reasoning"

    if "Agentic-Orchestrator" in tags:
        return "agentic", "architecture_tags contains Agentic-Orchestrator"

    # Only assign coding via Coder tag when "General" is absent (e.g. Codestral, not DeepSeek V3)
    if "Coder" in tags and "General" not in tags:
        return "coding", "architecture_tags Coder (no General tag)"

    # "Thinking" present but NOT "Thinking-Optional" → reasoning
    if "Thinking" in tags and "Thinking-Optional" not in tags:
        return "reasoning", "architecture_tags contains Thinking (fixed CoT)"

    return "generalist", "fallback"


def migrate(dry_run: bool) -> int:
    card_files = sorted(
        p for p in CARD_DIR.glob("*.json")
        if p.name not in ("_index.json",) and not p.name.startswith("_all_cards")
    )

    already_set: list[tuple[str, str]] = []
    to_assign: list[tuple[str, str, str]] = []  # (filename, use_case, basis)
    errors: list[str] = []

    for path in card_files:
        try:
            with path.open(encoding="utf-8") as f:
                card = json.load(f)
        except json.JSONDecodeError as e:
            errors.append(f"{path.name}: JSON error — {e}")
            continue

        existing = card.get("use_case_primary")
        if existing is not None:
            already_set.append((path.name, existing))
            continue

        use_case, basis = _infer_use_case(card)
        to_assign.append((path, use_case, basis))

    # Report
    col_w = 45
    print(f"\n{'─' * 80}")
    print(f"  CrucibleMark — migrate_use_case_primary  {'[DRY RUN]' if dry_run else '[APPLYING]'}")
    print(f"{'─' * 80}")
    print(f"\n  Already set ({len(already_set)} cards — skipped):")
    for name, val in already_set:
        print(f"    ✓  {name:<{col_w}}  {val}")

    print(f"\n  To assign ({len(to_assign)} cards):")
    for path, use_case, basis in to_assign:
        print(f"    →  {path.name:<{col_w}}  {use_case:<20}  [{basis}]")

    if errors:
        print(f"\n  Errors ({len(errors)}):")
        for e in errors:
            print(f"    ✗  {e}")

    print(f"\n{'─' * 80}")
    print(f"  Summary: {len(already_set)} already set, {len(to_assign)} to assign, {len(errors)} errors")
    print(f"{'─' * 80}\n")

    if dry_run:
        print("  Dry run — no files written.\n")
        return 0 if not errors else 1

    # Apply
    written = 0
    for path, use_case, _ in to_assign:
        with path.open(encoding="utf-8") as f:
            card = json.load(f)
        card["use_case_primary"] = use_case
        with path.open("w", encoding="utf-8") as f:
            json.dump(card, f, ensure_ascii=False, indent=2)
            f.write("\n")
        written += 1

    print(f"  Written {written} cards.\n")
    return 0 if not errors else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate use_case_primary into model cards.")
    parser.add_argument("--dry-run", action="store_true", help="Report only, no file writes.")
    args = parser.parse_args()

    # Run from project root
    if not CARD_DIR.exists():
        print(f"ERROR: {CARD_DIR} not found. Run from project root.", file=sys.stderr)
        sys.exit(1)

    sys.exit(migrate(dry_run=args.dry_run))
