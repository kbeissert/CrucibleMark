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
  6. architecture_tags gegen Registry-Whitelist (SSoT: config/card_vocabulary.yaml)
     - unbekannte Tags → WARN (Wildwuchs verhindern)
     - deprecated Tags → WARN mit Migrations-Hinweis (konsolidieren)
  7. Top-Level-Field-Whitelist (SSoT: config/card_template_model.yaml)
     - in complete-Cards: unbekannte Felder → WARN (Wildwuchs-Schutz)
     - in draft/minimal: toleriert (experimentelle Felder erlaubt)
  8. weights_provenance_risk Auto-Validierung
     - proprietary + origin_country=(USA|China) → Risk ≥ "medium"
     - open-weights + origin_country=(USA|China) + deployment_type=cloud-only → Risk ≥ "medium"
     (Hintergrund: CLOUD Act/Cyber Security Law ermöglichen Datenzugriff)

Tag-Whitelist kommt aus config/card_vocabulary.yaml via utils.card_utils.
Damit können Auto-Generatoren dieselbe SSoT nutzen wie die Validierung.

Usage:
    python scripts/dev/validate_model_cards.py
    python scripts/dev/validate_model_cards.py --fix-dry-run   (reserved for future auto-fix)
"""

import json
import logging
import sys
from pathlib import Path

# Logger für manuelle Konsistenz-Prüfungen (z.B. CI-Output)
logger = logging.getLogger(__name__)

# sys.path-Fix: Skript liegt in scripts/dev/ — utils/ ist parallel dazu
# (nicht in scripts/dev/). Bei direktem Aufruf (python scripts/dev/validate_...)
# muss utils/ explizit zum Pfad hinzugefügt werden, sonst schlägt der
# `from utils.card_utils import ...`-Import fehlt.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

CARDS_DIR = Path("benchmark_scores/model_cards")

# Whitelists werden NICHT mehr hier hardcoded — sie kommen aus der
# Taxonomie-SSoT (config/classification_taxonomy.json) via utils.card_utils.
# Das verhindert Drift zwischen Card-Generierung, Validierung und Runtime-Mapping.
# Siehe utils/card_utils.py:load_taxonomy() / get_valid_values().
_REQUIRED_FIELDS = [
    "model_id",
    "display_name",
    "weights_license_tier",
    "license",
    "commercial_use_allowed",
    "use_case_primary",
    "parameter_architecture",
]


def _get_valid_values(section: str) -> frozenset[str]:
    """Lazy-Loader für Taxonomie-Whitelist. Import hier lokal, um Import-Zyklen zu vermeiden."""
    try:
        from utils.card_utils import get_valid_values
        return get_valid_values(section)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Konnte Taxonomie-Section '%s' nicht laden: %s", section, exc)
        return frozenset()


def _get_template_field_names() -> frozenset[str]:
    """Lazy-Loader für die Vereinigung aller Template-Feldnamen (required + optional).

    SSoT: config/card_template_model.yaml. Verwendet für die Top-Level-Field-Whitelist
    in Karten, damit Wildwuchs in complete-Cards erkannt wird.
    """
    try:
        import yaml
        template_path = Path("config/card_template_model.yaml")
        if not template_path.exists():
            return frozenset()
        data = yaml.safe_load(template_path.read_text(encoding="utf-8"))
        names: set[str] = set()
        for section in ("required_fields", "optional_fields"):
            for entry in data.get(section, []) or []:
                if isinstance(entry, dict) and "name" in entry:
                    names.add(entry["name"])
        return frozenset(names)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Konnte Template-Feldnamen nicht laden: %s", exc)
        return frozenset()


def _get_tag_registry() -> tuple[frozenset[str], dict[str, str | None]]:
    """Lazy-Loader für Tag-Registry aus config/card_vocabulary.yaml.

    Returns:
        (known_tags, deprecated_normalizations) — known_tags vereinigt reserved,
        informational und deprecated Slugs. deprecated_normalizations mappt
        alten Slug → normalisierter Slug (None = entfernen).
    """
    try:
        from utils.card_utils import get_all_known_tags, get_deprecated_normalizations
        return get_all_known_tags(), get_deprecated_normalizations()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Konnte Tag-Registry nicht laden: %s", exc)
        return frozenset(), {}


OPEN_WEIGHTS_PHRASES = ["Open-Weights-Modell", "Open Weights Modell", "Open-Weights-Modell", "Open Weights Model"]


def _check_missing_required_fields(data: dict, issues: list[str]) -> None:
    for field in _REQUIRED_FIELDS:
        if field not in data:
            issues.append(f"[MISSING FIELD] '{field}' fehlt")


def _check_tier_consistency(data: dict, issues: list[str], valid_tiers: frozenset) -> str:
    tier = data.get("weights_license_tier", "")
    if tier and tier not in valid_tiers:
        issues.append(f"[INVALID TIER] '{tier}' ist kein gültiger Wert ({sorted(valid_tiers)})")
    summary = data.get("summary", "")
    commercial = data.get("commercial_use_allowed")

    if tier != "open-weights" and any(phrase in summary for phrase in OPEN_WEIGHTS_PHRASES):
        issues.append(
            f"[SUMMARY MISMATCH] summary enthält 'Open-Weights'-Begriff, "
            f"aber weights_license_tier='{tier}'"
        )

    if tier == "open-weights" and commercial is False:
        issues.append(
            "[TIER/COMMERCIAL MISMATCH] weights_license_tier='open-weights' "
            "aber commercial_use_allowed=false — sollte 'restricted-weights' sein"
        )
    return tier


def _check_use_case_and_vision(data: dict, issues: list[str], valid_use_cases: frozenset) -> tuple[str, list[str]]:
    use_case = data.get("use_case_primary", "")
    if use_case and use_case not in valid_use_cases:
        issues.append(
            f"[INVALID USE_CASE] use_case_primary='{use_case}' "
            f"ist kein gültiger Wert ({sorted(valid_use_cases)})"
        )

    tags = data.get("architecture_tags", [])
    has_primary_vision = ("Vision" in tags or "Multimodal" in tags) and "Vision-Capable" not in tags
    if has_primary_vision and use_case and use_case != "vision-language":
        issues.append(
            f"[WARN] architecture_tags enthält Vision/Multimodal, "
            f"aber use_case_primary='{use_case}' (erwartet: 'vision-language' — prüfen ob korrekt)"
        )
    return use_case, tags


def _check_param_arch(data: dict, issues: list[str], valid_param_arch: frozenset) -> str:
    param_arch = data.get("parameter_architecture", "")
    if param_arch and param_arch not in valid_param_arch:
        issues.append(
            f"[INVALID PARAM_ARCH] parameter_architecture='{param_arch}' "
            f"ist kein gültiger Wert ({sorted(valid_param_arch)})"
        )

    params_active = data.get("params_active_b")
    if params_active is not None and param_arch == "dense":
        issues.append(
            "[WARN] params_active_b gesetzt, aber parameter_architecture='dense' "
            "(bei Dense sind total = aktiv — params_active_b kann entfernt werden)"
        )
    return param_arch


def _check_complete_card_warnings(data: dict, issues: list[str]) -> str:
    card_status = data.get("card_status", "")
    if card_status != "complete":
        return card_status
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
    return card_status


def _check_tag_whitelist(tags: list, issues: list[str]) -> None:
    known_tags, deprecated_norm = _get_tag_registry()
    if not known_tags or not tags:
        return
    for tag in tags:
        if tag in known_tags:
            continue
        if tag in deprecated_norm:
            replacement = deprecated_norm[tag]
            if replacement is None:
                hint = "soll entfernt werden"
            else:
                hint = f"soll zu '{replacement}' migriert werden"
            issues.append(
                f"[WARN] architecture_tags enthält deprecated Tag '{tag}' — {hint}. "
                f"Registry: config/card_vocabulary.yaml (Migration: scripts/dev/migrate_architecture_tags.py)"
            )
        else:
            issues.append(
                f"[WARN] architecture_tags enthält unbekannten Tag '{tag}' — "
                f"nicht in config/card_vocabulary.yaml. "
                f"Falls gewollt: in reserved_tags/informational_tags aufnehmen, "
                f"sonst entfernen."
            )


def _check_provenance_risk(data: dict, tier: str, issues: list[str]) -> None:
    provenance_risk = data.get("weights_provenance_risk", "")
    origin_country = data.get("origin_country", "")
    deployment_type = data.get("deployment_type", "")

    if not provenance_risk or not origin_country:
        return

    if tier == "proprietary" and origin_country in ("USA", "China") and provenance_risk == "low":
        issues.append(
            f"[PROVENANCE RISK] weights_provenance_risk='low' unzulässig für "
            f"proprietary Model aus {origin_country} (CLOUD Act/CSL-Exposition → mindestens 'medium')"
        )

    if tier == "open-weights" and origin_country in ("USA", "China") and deployment_type == "cloud-only" and provenance_risk == "low":
        issues.append(
            f"[PROVENANCE RISK] weights_provenance_risk='low' unzulässig für "
            f"cloud-only Model aus {origin_country} (CLOUD Act/CSL-Exposition → mindestens 'medium')"
        )


def _check_unknown_top_level_fields(data: dict, card_status: str, issues: list[str]) -> None:
    known_fields = _get_template_field_names()
    if not known_fields:
        return
    for field_name in data:
        if field_name in known_fields:
            continue
        if card_status == "complete":
            issues.append(
                f"[WARN] unbekanntes Top-Level-Feld '{field_name}' in complete-Card. "
                f"Nicht in config/card_template_model.yaml definiert. "
                f"Falls gewollt: in optional_fields/required_fields aufnehmen, "
                f"sonst aus der Card entfernen."
            )


def check_card(path: Path, data: dict) -> list[str]:
    issues: list[str] = []
    name = data.get("display_name", data.get("model_id", path.stem))

    valid_tiers = _get_valid_values("weights_license_tier")
    valid_use_cases = _get_valid_values("use_case")
    valid_param_arch = _get_valid_values("parameter_architecture")

    _check_missing_required_fields(data, issues)
    tier = _check_tier_consistency(data, issues, valid_tiers)
    _use_case, tags = _check_use_case_and_vision(data, issues, valid_use_cases)
    _param_arch = _check_param_arch(data, issues, valid_param_arch)
    card_status = _check_complete_card_warnings(data, issues)
    _check_tag_whitelist(tags, issues)
    _check_provenance_risk(data, tier, issues)
    _check_unknown_top_level_fields(data, card_status, issues)

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
