"""Naming Convention Validator — prüft display_name und model_version gegen SSoT-Regeln.

SSoT: memory-bank/reference/data-schema.md

Regeln:
  display_name:
    - Format: {Basismodellname} ({Community-Gruppe ODER Variante})
    - VERBOTEN: Quantisierung (NVFP4, FP8, MXFP4), Deployment (vLLM, GGUF),
                Architektur (Dense, MoE, MTP, DFlash), Seed-OSS, Llama-3.1,
                Provider-Suffixe (via OpenRouter, via Groq)
  model_version:
    - Reine Versionsnummer (z.B. 3.6, 4, 5.4)
    - VERBOTEN: Parameteranzahl (27B, 120B), Quantisierung (FP8, NVFP4, MXFP4),
                Variante (Instruct), Community-Gruppe (Uncensored)
    - AUSNAHME: "Coder" als Variante ist erlaubt (z.B. "3 Coder")

Verwendung:
    python scripts/analysis/validate_naming.py
    python scripts/analysis/validate_naming.py --warn-only
    python scripts/analysis/validate_naming.py --json
    python scripts/analysis/validate_naming.py --card-type model

Exit-Codes:
    0 = alle Cards OK
    1 = Namensverstoesse gefunden
    2 = Programmfehler
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

MODEL_CARDS_DIR = ROOT_DIR / "benchmark_scores" / "model_cards"
VENDOR_CARDS_DIR = ROOT_DIR / "benchmark_scores" / "vendor_cards"

_DISPLAY_NAME_FORBIDDEN_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\bNVFP4\b",
        r"\bMXFP4\b",
        r"\bFP8\b",
        r"\bFP16\b",
        r"\bBF16\b",
        r"\bvLLM\b",
        r"\bGGUF\b",
        r"\bDense\b",
        r"\bMoE\b",
        r"\bMTP\b",
        r"\bDFlash\b",
        r"\bSeed-OSS\b",
        r"\bLlama-3\.1\b",
        r"\bvia OpenRouter\b",
        r"\bvia Groq\b",
        r"\bvia [A-Z][a-z]+\sCloud\b",
    ]
]

_MODEL_VERSION_FORBIDDEN_PATTERNS = [
    (re.compile(r"\d+B\b", re.IGNORECASE), "Parameteranzahl (z.B. 27B, 120B)"),
    (re.compile(r"\bFP8\b", re.IGNORECASE), "Quantisierung FP8"),
    (re.compile(r"\bNVFP4\b", re.IGNORECASE), "Quantisierung NVFP4"),
    (re.compile(r"\bMXFP4\b", re.IGNORECASE), "Quantisierung MXFP4"),
    (re.compile(r"\bInstruct\b", re.IGNORECASE), "Variante Instruct"),
    (re.compile(r"\bUncensored\b", re.IGNORECASE), "Community-Gruppe Uncensored"),
    (re.compile(r"\bA\d+B\b", re.IGNORECASE), "Architektur-Kennung (z.B. A3B, A4B)"),
]

_MODEL_VERSION_ALLOWED = {
    "coder",
    "thinking",
    "chat",
    "preview",
    "beta",
    "alpha",
    "nano",
    "mini",
    "micro",
    "flash",
    "pro",
    "ultra",
    "max",
    "lite",
    "base",
}


@dataclass
class NamingIssue:
    card_file: str
    model_id: str
    field: str
    value: str
    reason: str


@dataclass
class NamingReport:
    total_cards: int = 0
    issues: list[NamingIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.issues) == 0


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def _check_display_name(value: str) -> list[str]:
    reasons: list[str] = []
    for pattern in _DISPLAY_NAME_FORBIDDEN_PATTERNS:
        if pattern.search(value):
            reasons.append(f"Enthaelt verbotenen Begriff: {pattern.pattern}")
    return reasons


def _check_model_version(value: str) -> list[str]:
    reasons: list[str] = []
    for pattern, description in _MODEL_VERSION_FORBIDDEN_PATTERNS:
        if pattern.search(value):
            reasons.append(f"Enthaelt {description}")
    return reasons


def validate_cards(cards_dir: Path) -> NamingReport:
    report = NamingReport()
    if not cards_dir.is_dir():
        return report

    for card_path in sorted(cards_dir.glob("*.json")):
        card = _read_json(card_path)
        if card is None:
            continue

        report.total_cards += 1
        model_id = card.get("model_id", card_path.stem)

        display_name = card.get("display_name")
        if display_name and isinstance(display_name, str):
            for reason in _check_display_name(display_name):
                report.issues.append(NamingIssue(
                    card_file=card_path.name,
                    model_id=model_id,
                    field="display_name",
                    value=display_name,
                    reason=reason,
                ))

        model_version = card.get("model_version")
        if model_version and isinstance(model_version, str):
            for reason in _check_model_version(model_version):
                report.issues.append(NamingIssue(
                    card_file=card_path.name,
                    model_id=model_id,
                    field="model_version",
                    value=model_version,
                    reason=reason,
                ))

    return report


def format_text(report: NamingReport, card_type: str) -> str:
    lines: list[str] = []
    header = f"=== Naming Convention Validator ({card_type}-cards) ==="
    lines.append(header)

    if report.is_valid:
        lines.append(f"Alle {report.total_cards} Cards OK — keine Namensverstoesse.")
    else:
        lines.append(f"{len(report.issues)} Verstoesse in {report.total_cards} Cards:")
        lines.append("")
        for issue in report.issues:
            lines.append(
                f"  [{issue.field}] {issue.model_id} ({issue.card_file})"
            )
            lines.append(f"    Wert:    {issue.value!r}")
            lines.append(f"    Grund:   {issue.reason}")

    return "\n".join(lines)


def format_json(report: NamingReport, card_type: str) -> str:
    return json.dumps(
        {
            "card_type": card_type,
            "total_cards": report.total_cards,
            "total_issues": len(report.issues),
            "valid": report.is_valid,
            "issues": [
                {
                    "card_file": i.card_file,
                    "model_id": i.model_id,
                    "field": i.field,
                    "value": i.value,
                    "reason": i.reason,
                }
                for i in report.issues
            ],
        },
        indent=2,
        ensure_ascii=False,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Naming Convention Validator (display_name, model_version)"
    )
    parser.add_argument(
        "--card-type",
        choices=["model", "vendor", "all"],
        default="model",
        help="Welcher Card-Typ validiert werden soll (default: model)",
    )
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Nur Warnung ausgeben, Exit 0 auch bei Verstoessen",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="JSON-Output statt Text",
    )
    args = parser.parse_args()

    card_types = ["model", "vendor"] if args.card_type == "all" else [args.card_type]
    all_issues: list[NamingIssue] = []
    all_reports: list[tuple[str, NamingReport]] = []

    for ct in card_types:
        cards_dir = MODEL_CARDS_DIR if ct == "model" else VENDOR_CARDS_DIR
        report = validate_cards(cards_dir)
        all_reports.append((ct, report))
        all_issues.extend(report.issues)

    if args.json:
        combined = {}
        for ct, report in all_reports:
            combined[ct] = json.loads(format_json(report, ct))
        print(json.dumps(combined, indent=2, ensure_ascii=False))
    else:
        for ct, report in all_reports:
            print(format_text(report, ct))
            print()

    if all_issues:
        total = len(all_issues)
        if args.warn_only:
            print(f"WARNUNG: {total} Namensverstoesse gefunden (warn-only, Exit 0)")
            return 0
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
