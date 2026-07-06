#!/usr/bin/env python3
"""Model Card Generator — erstellt leere Card-Templates zur manuellen Befüllung.

Erzeugt pro Modell-ID eine Model Card, deren Felder gemäß des SSoT-Templates
in ``config/card_template_model.yaml`` (geladen via :mod:`utils.card_template`)
mit Platzhaltern vorbelegt sind. Manuell zu befüllen sind alle ``TODO``-Felder;
danach ``card_status`` auf ``"complete"`` setzen.

Konsumenten der Card-Struktur:
  - :mod:`utils.card_utils.ensure_card` (SSoT-Erzeugung)
  - :mod:`scripts.analysis.validate_cards` (Validierung gegen Template)

Verwendung:
    python scripts/analysis/generate_model_cards.py --model-id claude-opus-4-7
    python scripts/analysis/generate_model_cards.py --model-id qwen3:14b --provider ollama_local
    python scripts/analysis/generate_model_cards.py --interactive
    python scripts/analysis/generate_model_cards.py --card-type model --json

Exit-Codes:
    0 = alle Karten erfolgreich erzeugt oder übersprungen
    1 = mindestens ein Fehler (Card-Erstellung fehlgeschlagen)
    2 = Programmfehler (z.B. unbekannter card_type)

Hinweis: Sync bestehender Karten (fehlende Felder ergänzen, entfernte löschen)
ist nicht Aufgabe dieses Skripts. Dafür ``scripts/analysis/sync_cards.py`` nutzen.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

# Pfad-Hack: dieses Script liegt in scripts/analysis/, das Root ist eine Ebene höher
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from utils.card_template import (  # noqa: E402
    cards_dir,
)
from utils.card_utils import ensure_card  # noqa: E402
from utils.model_utils import _card_path, resolve_canonical_model_id  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Konstanten
# ---------------------------------------------------------------------------
Action = Literal["created", "rebuilt", "skipped", "failed"]
IssueType = Literal["exists", "path_error", "parse_error", "template_missing"]

# Tolerant-Filter für Helper-Dateien (analog validate_cards.py::_is_card_file)
_HELPER_FILENAMES: frozenset[str] = frozenset({"_index.json"})
_HELPER_STEM_BLACKLIST: frozenset[str] = frozenset({"True", "False", "null", "None"})


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class CardCreationIssue:
    """Ein einzelnes Problem bei der Card-Erstellung."""

    issue_type: IssueType
    field: str
    message: str


@dataclass
class CardCreationReport:
    """Aggregierter Report für eine einzelne Card-Erstellung."""

    card_file: str
    card_id: str
    action: Action
    issues: list[CardCreationIssue] = field(default_factory=list)
    is_success: bool = True

    def add_issue(self, issue: CardCreationIssue) -> None:
        self.issues.append(issue)
        # "exists" ist nur eine Warnung (skip), kein Fehler
        if issue.issue_type != "exists":
            self.is_success = False


# ---------------------------------------------------------------------------
# Helper-Funktionen
# ---------------------------------------------------------------------------


def _is_helper_file(path: Path) -> bool:
    """Filtert Helper-Dateien aus, die keine Cards sind.

    - Index-Dateien (``_index.json``)
    - Versehentlich gespeicherte Booleans/None (``True.json``, ``False.json`` …)
    """
    if path.name in _HELPER_FILENAMES:
        return True
    return path.stem in _HELPER_STEM_BLACKLIST


def _read_existing_card(path: Path) -> dict[str, Any] | None:
    """Liest eine bestehende Card-Datei, gibt None bei Parse-Fehler zurück."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Konnte %s nicht lesen: %s", path.name, exc)
        return None
    if not isinstance(data, dict):
        return None
    return data


def _resolve_target_path(
    model_id: str,
    provider: str | None = None,
) -> Path:
    """Bestimmt den kanonischen Card-Pfad via SSoT-Helper.

    Nutzt :func:`utils.model_utils._card_path` (SSoT für Card-Naming inkl.
    ``-latest``-Alias-Auflösung). Bei Fehler (``ValueError`` aus ``_card_path``)
    wird eine ``path_error``-Exception hochgegeben.
    """
    return _card_path(model_id, provider=provider, for_write=True)


def _build_creation_plan(
    target_path: Path,
    force: bool,
) -> Literal["create", "rebuild", "skip"]:
    """Entscheidet, welche Aktion nötig ist.

    Returns:
        ``"create"``: Karte existiert nicht → neu anlegen
        ``"rebuild"``: Karte existiert UND ``force`` ist True → löschen + neu
        ``"skip"``: Karte existiert UND ``force`` ist False → überspringen
    """
    if not target_path.exists():
        return "create"
    if force:
        return "rebuild"
    return "skip"


def _execute_creation(
    model_id: str,
    target_path: Path,
    action: Literal["create", "rebuild"],
) -> None:
    """Führt die Card-Erstellung aus (delegiert an SSoT ``ensure_card``)."""
    if action == "rebuild":
        target_path.unlink()
        logger.info("Bestehende Card gelöscht (--force): %s", target_path.name)

    ensure_card(model_id, card_path=target_path)
    logger.info("Template angelegt: %s", target_path.name)


def _prompt_for_model_id(prompt: str = "Model-ID eingeben (z.B. claude-opus-4-7): ") -> str:
    """Fragt interaktiv nach einer Model-ID. Robust gegen EOF/KeyboardInterrupt."""
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        logger.error("Eingabe abgebrochen.")
        return ""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def create_card(
    model_id: str,
    *,
    provider: str | None = None,
    force: bool = False,
) -> CardCreationReport:
    """Erstellt eine einzelne Model Card.

    Args:
        model_id: Modell-Identifier (Slug). Wird via
            :func:`utils.model_utils.resolve_canonical_model_id` kanonisiert
            (Aliase wie ``claude-haiku-4-5`` → ``claude-haiku-4-5-20251001``
            und ``hf.co``-Präfixe werden aufgelöst).
        provider: Optionaler Provider-Key (z.B. ``ollama_local``,
            ``llamacpp_spark``). Bei gesetztem Wert greift das neue
            ``{base}--{shortcode}``-ID-Schema aus :mod:`utils.card_utils`.
        force: Bestehende Card überschreiben.

    Returns:
        :class:`CardCreationReport` mit ``action`` und ggf. Issues.
    """
    # SSoT: Aliase werden vor der Card-Pfad-Berechnung kanonisiert.
    canonical_id = resolve_canonical_model_id(model_id)
    if not canonical_id:
        report = CardCreationReport(
            card_file="",
            card_id=model_id,
            action="failed",
        )
        report.add_issue(CardCreationIssue(
            issue_type="path_error",
            field="model_id",
            message=f"Konnte model_id '{model_id}' nicht kanonisieren",
        ))
        return report

    try:
        target_path = _resolve_target_path(canonical_id, provider)
    except (ValueError, KeyError) as exc:
        report = CardCreationReport(
            card_file="",
            card_id=canonical_id,
            action="failed",
        )
        report.add_issue(CardCreationIssue(
            issue_type="path_error",
            field="model_id",
            message=f"Pfad-Auflösung fehlgeschlagen: {exc}",
        ))
        return report

    report = CardCreationReport(
        card_file=target_path.name,
        card_id=canonical_id,
        action="skipped",
    )

    plan = _build_creation_plan(target_path, force)

    if plan == "skip":
        report.action = "skipped"
        report.add_issue(CardCreationIssue(
            issue_type="exists",
            field="<file>",
            message=f"Card existiert bereits: {target_path.name} — nutze --force zum Überschreiben.",
        ))
        logger.info("Übersprungen: %s", target_path.name)
        return report

    try:
        _execute_creation(canonical_id, target_path, plan)
    except (OSError, ValueError) as exc:
        report.action = "failed"
        report.add_issue(CardCreationIssue(
            issue_type="parse_error",
            field="<file>",
            message=f"Card-Erstellung fehlgeschlagen: {exc}",
        ))
        logger.error("Fehler bei %s: %s", target_path.name, exc)
        return report

    report.action = "rebuilt" if plan == "rebuild" else "created"
    return report


def create_all(
    card_type: str = "model",
    *,
    force: bool = False,
) -> list[CardCreationReport]:
    """Platzhalter für zukünftige Batch-Erstellung über das YAML-Template.

    Aktuell wird jede Card einzeln via :func:`create_card` erzeugt
    (CLI-Loop). Diese Funktion liefert die konsistente Public-API-Signatur
    analog zu ``validate_all()`` in :mod:`scripts.analysis.validate_cards`.
    """
    # Konsistenz-Check: card_type muss bekannt sein
    try:
        cards_dir(card_type)
    except ValueError as exc:
        raise ValueError(exc) from exc
    return []  # pragma: no cover — Batch-Loop liegt in main()


# ---------------------------------------------------------------------------
# Format-Funktionen
# ---------------------------------------------------------------------------


def format_text_report(
    reports: list[CardCreationReport],
    card_type: str,
) -> str:
    """Formatierter Text-Report für CLI-Ausgabe."""
    created = [r for r in reports if r.action == "created"]
    rebuilt = [r for r in reports if r.action == "rebuilt"]
    skipped = [r for r in reports if r.action == "skipped"]
    failed = [r for r in reports if r.action == "failed"]

    lines: list[str] = []
    lines.append(f"=== Card Creation Report: {card_type.upper()} ===")
    lines.append(f"Total cards:        {len(reports)}")
    lines.append(f"  Created:          {len(created)}")
    lines.append(f"  Rebuilt:          {len(rebuilt)}")
    lines.append(f"  Skipped:          {len(skipped)}")
    lines.append(f"  Failed:           {len(failed)}")

    if failed:
        lines.append("")
        lines.append(f"--- Fehlgeschlagen ({len(failed)}) ---")
        for r in failed:
            lines.append(f"\n  {r.card_file} (id={r.card_id}):")
            for issue in r.issues:
                lines.append(f"    [{issue.issue_type}] {issue.message}")

    return "\n".join(lines)


def format_json_report(
    reports: list[CardCreationReport],
    card_type: str,
) -> str:
    """JSON-Report für CI-Parsing."""
    return json.dumps(
        {
            "card_type": card_type,
            "total": len(reports),
            "created": sum(1 for r in reports if r.action == "created"),
            "rebuilt": sum(1 for r in reports if r.action == "rebuilt"),
            "skipped": sum(1 for r in reports if r.action == "skipped"),
            "failed": sum(1 for r in reports if r.action == "failed"),
            "cards": [
                {
                    "card_file": r.card_file,
                    "card_id": r.card_id,
                    "action": r.action,
                    "is_success": r.is_success,
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


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Erstellt ein leeres Model Card Template (gemäß SSoT-YAML).",
    )
    parser.add_argument(
        "--card-type",
        choices=["model", "vendor", "all"],
        default="model",
        help="Welcher Card-Typ erzeugt werden soll (default: model)",
    )
    parser.add_argument(
        "--model-id",
        type=str,
        default=None,
        help="Model-ID (z.B. claude-opus-4-7). Erforderlich ohne --interactive.",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default=None,
        help="Provider-Key für lokale/namespaced Modelle (z.B. ollama_local).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Bestehende Card überschreiben.",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Model-ID interaktiv erfragen, wenn nicht via --model-id gegeben.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="JSON-Output statt Text.",
    )
    args = parser.parse_args()

    # Provider-Card-Erstellung ist nicht im Scope dieses Skripts
    # (generate_vendor_cards.py hat eigene LLM-basierte Pipeline).
    if args.card_type in {"vendor", "all"}:
        logger.error(
            "Provider-Card-Erstellung wird durch "
            "scripts/analysis/generate_vendor_cards.py abgedeckt. "
            "Dieses Skript ist auf Model Cards spezialisiert.",
        )
        return 2

    model_id = args.model_id
    if not model_id and args.interactive:
        model_id = _prompt_for_model_id()
    if not model_id:
        logger.error(
            "Keine Model-ID angegeben. Nutze --model-id oder --interactive.",
        )
        return 2

    report = create_card(
        model_id=model_id,
        provider=args.provider,
        force=args.force,
    )
    reports = [report]

    # Output
    if args.json:
        print(format_json_report(reports, args.card_type))
    else:
        print(format_text_report(reports, args.card_type))
        if report.is_success:
            print(
                f"\nTemplate angelegt: {report.card_file}\n"
                "Alle 'TODO'-Felder manuell befüllen, "
                "dann card_status auf 'complete' setzen.",
            )

    # Exit-Code-Logik
    if not report.is_success:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
