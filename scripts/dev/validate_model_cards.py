"""
Validates model card JSON files for internal consistency.

Checks:
  1. summary mentions "Open-Weights" but weights_license_tier != "open-weights"
  2. commercial_use_allowed=False but weights_license_tier="open-weights"
     (license restricts commercial use → tier should be restricted-weights)
  3. Required fields present (model_id, display_name, weights_license_tier, license,
     commercial_use_allowed, use_case_primary)
  4. use_case_primary has a valid controlled-vocabulary value
  5. Vision/Multimodal tags present but use_case_primary != "vision-language" → WARNING

Usage:
    python scripts/dev/validate_model_cards.py
    python scripts/dev/validate_model_cards.py --fix-dry-run   (reserved for future auto-fix)
"""

import json
import sys
from pathlib import Path

CARDS_DIR = Path("benchmark_scores/model_cards")
VALID_TIERS = {"open-weights", "restricted-weights", "proprietary"}
REQUIRED_FIELDS = [
    "model_id",
    "display_name",
    "weights_license_tier",
    "license",
    "commercial_use_allowed",
    "use_case_primary",
    "parameter_architecture",
]
VALID_USE_CASES = {"generalist", "coding", "reasoning", "vision-language", "agentic"}
VALID_PARAM_ARCH = {"dense", "moe", "hybrid"}

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

    # 4. use_case_primary controlled vocabulary
    use_case = data.get("use_case_primary", "")
    if use_case and use_case not in VALID_USE_CASES:
        issues.append(
            f"[INVALID USE_CASE] use_case_primary='{use_case}' "
            f"ist kein gültiger Wert ({sorted(VALID_USE_CASES)})"
        )

    # 5. Vision/Multimodal tags but use_case_primary != "vision-language" (warning only)
    tags = data.get("architecture_tags", [])
    if ("Vision" in tags or "Multimodal" in tags) and use_case and use_case != "vision-language":
        issues.append(
            f"[WARN] architecture_tags enthält Vision/Multimodal, "
            f"aber use_case_primary='{use_case}' (erwartet: 'vision-language' — prüfen ob korrekt)"
        )

    # 6. parameter_architecture controlled vocabulary
    param_arch = data.get("parameter_architecture", "")
    if param_arch and param_arch not in VALID_PARAM_ARCH:
        issues.append(
            f"[INVALID PARAM_ARCH] parameter_architecture='{param_arch}' "
            f"ist kein gültiger Wert ({sorted(VALID_PARAM_ARCH)})"
        )

    # 7. params_active_b only makes sense for moe/hybrid
    params_active = data.get("params_active_b")
    if params_active is not None and param_arch == "dense":
        issues.append(
            "[WARN] params_active_b gesetzt, aber parameter_architecture='dense' "
            "(bei Dense sind total = aktiv — params_active_b kann entfernt werden)"
        )

    # 8. context_window_k and knowledge_cutoff: warn if missing on complete cards
    card_status = data.get("card_status", "")
    if card_status == "complete":
        if data.get("context_window_k") is None:
            issues.append(
                "[WARN] context_window_k fehlt (empfohlen für complete-Cards — "
                "Kontextfenster in Tausend Tokens, z.B. 128 für 128K)"
            )
        if not data.get("knowledge_cutoff"):
            issues.append(
                "[WARN] knowledge_cutoff fehlt (empfohlen für complete-Cards — "
                "Trainings-Cutoff als 'YYYY-MM', z.B. '2025-01')"
            )

    return [(f"  {name}: {issue}") for issue in issues]


def main() -> int:
    if not CARDS_DIR.exists():
        print(f"ERROR: {CARDS_DIR} nicht gefunden. Aus dem Projekt-Root ausführen.", file=sys.stderr)
        return 2

    errors: list[str] = []
    warnings: list[str] = []
    checked = 0

    for path in sorted(CARDS_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"  {path.name}: [JSON ERROR] {exc}")
            continue

        if not isinstance(data, dict):
            continue  # skip _index.json (list)

        checked += 1
        issues = check_card(path, data)
        if issues:
            for issue in issues:
                if "[WARN]" in issue:
                    warnings.append(f"\n{path.name}:\n{issue}")
                else:
                    errors.append(f"\n{path.name}:\n{issue}")

    if errors:
        print(f"Model Card Validation — {checked} Cards geprüft, FEHLER gefunden:\n")
        print("\n".join(errors))
    if warnings:
        print(f"\nWarnungen ({len(warnings)} — kein Fehler, manuelle Prüfung empfohlen):")
        print("\n".join(warnings))
    if not errors and not warnings:
        print(f"Model Card Validation — {checked} Cards geprüft. Alle OK.")
    elif not errors:
        print(f"\nModel Card Validation — {checked} Cards geprüft. Keine Fehler (nur Warnungen).")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
