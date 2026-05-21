"""
Validates model card JSON files for internal consistency.

Checks:
  1. summary mentions "Open-Weights" but weights_license_tier != "open-weights"
  2. commercial_use_allowed=False but weights_license_tier="open-weights"
     (license restricts commercial use → tier should be restricted-weights)
  3. Required fields present (model_id, display_name, weights_license_tier, license)

Usage:
    python scripts/dev/validate_model_cards.py
    python scripts/dev/validate_model_cards.py --fix-dry-run   (reserved for future auto-fix)
"""

import json
import sys
from pathlib import Path

CARDS_DIR = Path("benchmark_scores/model_cards")
VALID_TIERS = {"open-weights", "restricted-weights", "proprietary"}
REQUIRED_FIELDS = ["model_id", "display_name", "weights_license_tier", "license", "commercial_use_allowed"]

OPEN_WEIGHTS_PHRASES = ["Open-Weights-Modell", "Open Weights Modell", "Open-Weights-Modell", "Open Weights Model"]


def check_card(path: Path, data: dict) -> list[str]:
    issues: list[str] = []
    name = data.get("display_name", data.get("model_id", path.stem))

    # 1. Required fields
    for field in REQUIRED_FIELDS:
        if field not in data:
            issues.append(f"[MISSING FIELD] '{field}' fehlt")

    tier = data.get("weights_license_tier", "")
    summary = data.get("summary", "")
    commercial = data.get("commercial_use_allowed")

    if tier not in VALID_TIERS and tier:
        issues.append(f"[INVALID TIER] '{tier}' ist kein gültiger Wert ({VALID_TIERS})")

    # 2. summary claims Open-Weights but tier disagrees
    if tier != "open-weights" and any(phrase in summary for phrase in OPEN_WEIGHTS_PHRASES):
        issues.append(
            f"[SUMMARY MISMATCH] summary enthält 'Open-Weights'-Begriff, "
            f"aber weights_license_tier='{tier}'"
        )

    # 3. commercial_use_allowed=False with open-weights tier
    # (open-weights tier implies permissive license; false commercial means should be restricted)
    if tier == "open-weights" and commercial is False:
        issues.append(
            "[TIER/COMMERCIAL MISMATCH] weights_license_tier='open-weights' "
            "aber commercial_use_allowed=false — sollte 'restricted-weights' sein"
        )

    return [(f"  {name}: {issue}") for issue in issues]


def main() -> int:
    if not CARDS_DIR.exists():
        print(f"ERROR: {CARDS_DIR} nicht gefunden. Aus dem Projekt-Root ausführen.", file=sys.stderr)
        return 2

    all_issues: list[str] = []
    checked = 0

    for path in sorted(CARDS_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            all_issues.append(f"  {path.name}: [JSON ERROR] {exc}")
            continue

        if not isinstance(data, dict):
            continue  # skip _index.json (list)

        checked += 1
        issues = check_card(path, data)
        if issues:
            all_issues.append(f"\n{path.name}:")
            all_issues.extend(issues)

    if all_issues:
        print(f"Model Card Validation — {checked} Cards geprüft, FEHLER gefunden:\n")
        print("\n".join(all_issues))
        return 1

    print(f"Model Card Validation — {checked} Cards geprüft. Alle OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
