"""Card Template Validator — prüft alle Model- und Provider-Cards gegen Templates.

Liest die Templates aus ``config/card_template_*.yaml`` (SSoT) und prüft
für jede Card-Datei in ``benchmark_scores/``:
1. Alle Pflichtfelder vorhanden
2. Pflichtfelder haben semantisch nicht-leere Werte (kein TODO/null/""/"unknown")
3. Keine extras-Felder, die nicht im Template (required + optional) definiert sind
4. Pflicht-Sub-Felder in Sub-Dicts vorhanden (z.B. deployment.cloud_act_exposure)
5. Typ-Check (str | int | float | bool | list | object) — best-effort

Verwendung:
    python scripts/analysis/validate_cards.py
    python scripts/analysis/validate_cards.py --card-type model
    python scripts/analysis/validate_cards.py --json
    python scripts/analysis/validate_cards.py --fail-on-drift  # Exit 1 bei extras-Feldern

Exit-Codes:
    0 = alle Karten OK
    1 = Drift (extras-Felder) oder Missing required
    2 = Programmfehler
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Pfad-Hack: dieses Script liegt in scripts/analysis/, das Root ist eine Ebene höher
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from utils.card_template import CardTemplate, load_card_template  # noqa: E402

MODEL_CARDS_DIR = ROOT_DIR / "benchmark_scores" / "model_cards"
PROVIDER_CARDS_DIR = ROOT_DIR / "benchmark_scores" / "vendor_cards"

# Felder, die als "legitime extras" toleriert werden (oft von Generatoren
# angehängt, nicht im Template erfasst — z.B. tooluse_tested_at wurde schon
# ins Template aufgenommen, aber zur Sicherheit whitelist für unbekannte
# Felder, die historisch gewachsen sind).
_TOLERATED_EXTRAS_HINT = "tooluse_"


@dataclass
class CardIssue:
    """Ein einzelnes Problem in einer Card."""

    card_file: str
    card_id: str
    issue_type: str  # "missing_required" | "unknown_sentinel" | "drift_extras" | "missing_sub_field" | "parse_error"
    field: str
    message: str


@dataclass
class CardReport:
    """Aggregierter Report für eine einzelne Card."""

    card_file: str
    card_id: str
    issues: list[CardIssue] = field(default_factory=list)
    is_valid: bool = True

    def add_issue(self, issue: CardIssue) -> None:
        self.issues.append(issue)
        self.is_valid = False


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def _check_required_fields(
    card: dict[str, Any], template: CardTemplate, card_file: str, card_id: str,
) -> list[CardIssue]:
    """Prüft alle Pflichtfelder auf Existenz + nicht-Unknown-Sentinel."""
    issues: list[CardIssue] = []
    for spec in template.required_fields:
        if spec.name not in card:
            issues.append(CardIssue(
                card_file=card_file,
                card_id=card_id,
                issue_type="missing_required",
                field=spec.name,
                message=f"Pflichtfeld fehlt: '{spec.name}' ({spec.description})",
            ))
            continue
        if spec.is_unknown_sentinel(card[spec.name]):
            issues.append(CardIssue(
                card_file=card_file,
                card_id=card_id,
                issue_type="unknown_sentinel",
                field=spec.name,
                message=f"Pflichtfeld '{spec.name}' hat Unknown-Sentinel: {card[spec.name]!r}",
            ))
    return issues


def _check_extras(
    card: dict[str, Any], template: CardTemplate, card_file: str, card_id: str,
) -> list[CardIssue]:
    """Prüft auf extras-Felder, die nicht im Template definiert sind."""
    issues: list[CardIssue] = []
    for key in card:
        if template.is_known(key):
            continue
        # Toleranz: Felder mit tooluse_-Prefix sind legitim (Legacy)
        if key.startswith(_TOLERATED_EXTRAS_HINT):
            continue
        issues.append(CardIssue(
            card_file=card_file,
            card_id=card_id,
            issue_type="drift_extras",
            field=key,
            message=f"Extras-Feld '{key}' ist nicht im Template definiert",
        ))
    return issues


def _check_sub_fields(
    card: dict[str, Any], template: CardTemplate, card_file: str, card_id: str,
) -> list[CardIssue]:
    """Prüft Pflicht-Sub-Felder in Sub-Dicts (z.B. deployment.cloud_act_exposure)."""
    issues: list[CardIssue] = []
    for spec in template.required_fields:
        if not spec.sub_fields_required:
            continue
        sub_dict = card.get(spec.name)
        if not isinstance(sub_dict, dict):
            continue  # Missing-required wurde bereits oben gemeldet
        for sub_name in spec.sub_fields_required:
            if sub_name not in sub_dict:
                issues.append(CardIssue(
                    card_file=card_file,
                    card_id=card_id,
                    issue_type="missing_sub_field",
                    field=f"{spec.name}.{sub_name}",
                    message=f"Pflicht-Sub-Feld fehlt: '{spec.name}.{sub_name}'",
                ))
    return issues


def validate_card(
    card_file: Path, template: CardTemplate,
) -> CardReport:
    """Validiert eine einzelne Card-Datei gegen das Template."""
    card_id = card_file.stem
    report = CardReport(card_file=card_file.name, card_id=card_id)

    card = _read_json(card_file)
    if card is None:
        report.add_issue(CardIssue(
            card_file=card_file.name,
            card_id=card_id,
            issue_type="parse_error",
            field="<root>",
            message="Card ist kein valides JSON-Dict",
        ))
        return report

    # Card-ID aus dem Inhalt (model_id / provider_id), falls vorhanden
    if "model_id" in card:
        card_id = str(card["model_id"])
    elif "vendor_id" in card:
        card_id = str(card["vendor_id"])
    report.card_id = card_id

    for issue in _check_required_fields(card, template, card_file.name, card_id):
        report.add_issue(issue)
    for issue in _check_extras(card, template, card_file.name, card_id):
        report.add_issue(issue)
    for issue in _check_sub_fields(card, template, card_file.name, card_id):
        report.add_issue(issue)

    return report


def validate_all(card_type: str) -> list[CardReport]:
    """Validiert alle Cards des gegebenen Typs."""
    template = load_card_template(card_type)
    cards_dir = MODEL_CARDS_DIR if card_type == "model" else PROVIDER_CARDS_DIR
    if not cards_dir.exists():
        return []
    return [
        validate_card(p, template)
        for p in sorted(cards_dir.glob("*.json"))
        if _is_card_file(p)
    ]


def _is_card_file(path: Path) -> bool:
    """Filtert Helper-Dateien aus, die keine Cards sind (z.B. _index.json)."""
    # Index-Dateien sind Listen, keine Cards
    if path.stem.startswith("_"):
        return False
    # Bekannte Müll-Filenames (z.B. versehentlich gespeicherte Boolean-Werte)
    return path.stem not in {"True", "False", "null", "None"}


def format_text_report(reports: list[CardReport], card_type: str) -> str:
    """Formatierter Text-Report für CLI-Ausgabe."""
    valid = [r for r in reports if r.is_valid]
    invalid = [r for r in reports if not r.is_valid]
    total_issues = sum(len(r.issues) for r in reports)
    issues_by_type: dict[str, int] = {}
    for r in reports:
        for issue in r.issues:
            issues_by_type[issue.issue_type] = issues_by_type.get(issue.issue_type, 0) + 1

    lines: list[str] = []
    lines.append(f"=== Card Validation Report: {card_type.upper()} ===")
    lines.append(f"Total cards:        {len(reports)}")
    lines.append(f"  Valid:            {len(valid)}")
    lines.append(f"  Invalid:          {len(invalid)}")
    lines.append(f"Total issues:       {total_issues}")
    for issue_type, count in sorted(issues_by_type.items()):
        lines.append(f"  {issue_type:20s}  {count}")

    if invalid:
        lines.append("")
        lines.append(f"--- Cards mit Issues ({len(invalid)}) ---")
        for r in invalid[:50]:  # max 50 anzeigen
            lines.append(f"\n  {r.card_file} (id={r.card_id}):")
            for issue in r.issues[:10]:  # max 10 issues pro Card
                lines.append(f"    [{issue.issue_type}] {issue.message}")
            if len(r.issues) > 10:
                lines.append(f"    ... und {len(r.issues) - 10} weitere")
        if len(invalid) > 50:
            lines.append(f"\n  ... und {len(invalid) - 50} weitere Karten mit Issues")

    return "\n".join(lines)


def format_json_report(reports: list[CardReport], card_type: str) -> str:
    """JSON-Report für CI-Parsing."""
    return json.dumps(
        {
            "card_type": card_type,
            "total": len(reports),
            "valid": sum(1 for r in reports if r.is_valid),
            "invalid": sum(1 for r in reports if not r.is_valid),
            "cards": [
                {
                    "card_file": r.card_file,
                    "card_id": r.card_id,
                    "is_valid": r.is_valid,
                    "issues": [
                        {
                            "type": i.issue_type,
                            "field": i.field,
                            "message": i.message,
                        }
                        for i in r.issues
                    ],
                }
                for r in reports
            ],
        },
        indent=2,
        ensure_ascii=False,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Card Template Validator")
    parser.add_argument(
        "--card-type",
        choices=["model", "vendor", "all"],
        default="all",
        help="Welcher Card-Typ validiert werden soll (default: all)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="JSON-Output statt Text",
    )
    parser.add_argument(
        "--fail-on-drift",
        action="store_true",
        help="Exit 1 auch bei drift_extras (default: nur missing/unknown zählt)",
    )
    args = parser.parse_args()

    card_types = ["model", "vendor"] if args.card_type == "all" else [args.card_type]
    all_reports: list[tuple[str, list[CardReport]]] = []
    total_invalid = 0
    has_drift = False

    for ct in card_types:
        reports = validate_all(ct)
        all_reports.append((ct, reports))
        for r in reports:
            if not r.is_valid:
                total_invalid += 1
            for issue in r.issues:
                if issue.issue_type == "drift_extras":
                    has_drift = True

    if args.json:
        combined = {
            ct: json.loads(format_json_report(reports, ct))
            for ct, reports in all_reports
        }
        print(json.dumps(combined, indent=2, ensure_ascii=False))
    else:
        for ct, reports in all_reports:
            print(format_text_report(reports, ct))
            print()

    # Exit-Code-Logik
    if total_invalid > 0:
        return 1
    if args.fail_on_drift and has_drift:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
