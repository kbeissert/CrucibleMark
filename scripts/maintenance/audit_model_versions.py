#!/usr/bin/env python3
"""Audit-Script: identifiziert Cards, deren ``model_version`` Quant/Format-Info enthält.

Hintergrund (Phase 48)
----------------------
Das Feld ``model_version`` soll reine Versions-/Datums-Infos tragen
(z.B. ``"3.5"``, ``"4.0"``, ``"20251001"``). Bei vielen Bestandskarten
sind jedoch Quantisierungs-Tokens wie ``Q4_K_XL``, ``FP8``, ``GGUF`` ins
Feld eingeschlichen — eine Vermischung von Version und Engine-Format.

Dieses Script ist read-only und verändert keine Daten. Es liefert einen
Report, der als Grundlage für eine kontrollierte Migration dient.

Wichtig (Continuity-Constraint)
--------------------------------
``model_version`` ist in ``utils/scoring/llm_judge/.../score_calculator.py``
ein ``groupby``-Key. Ein Massen-Rewrite würde historische Benchmarks
auseinanderreißen. Eine Migration muss daher gezielt je Card passieren,
idealerweise mit Hash-Detection gleicher Benchmarks vor/nach — das ist
nicht trivial und bleibt daher ein manueller Follow-up.

Verwendung
----------
    .venv/bin/python scripts/maintenance/audit_model_versions.py
    .venv/bin/python scripts/maintenance/audit_model_versions.py --json

Exit-Code ist immer 0 (Audit, kein Hard-Fail) — Findings werden auf stdout
gemeldet.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Pfad-Setup — Repo-Root
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from utils.model_utils import model_version_has_quant_pollution  # noqa: E402

CARD_DIR = _REPO_ROOT / "benchmark_scores" / "model_cards"


def scan_cards(card_dir: Path = CARD_DIR) -> list[dict[str, str]]:
    """Liest alle Cards und meldet die mit model_version-Quant-Pollution."""
    findings: list[dict[str, str]] = []
    if not card_dir.exists():
        return findings

    for card_path in sorted(card_dir.glob("*.json")):
        try:
            data = json.loads(card_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            print(f"⚠️  Konnte {card_path.name} nicht lesen: {exc}", file=sys.stderr)
            continue

        version = data.get("model_version")
        if model_version_has_quant_pollution(version):
            findings.append(
                {
                    "card_file": card_path.name,
                    "model_id": data.get("model_id", ""),
                    "model_version_raw": str(version) if version else "",
                    "quantization_format_existing": data.get("quantization_format") or "",
                    "hardware_platform_existing": data.get("hardware_platform") or "",
                    "inference_engine_existing": data.get("inference_engine") or "",
                }
            )
    return findings


def print_report(findings: list[dict[str, str]]) -> None:
    if not findings:
        print("✅ Keine model_version-Quant-Pollution gefunden.")
        return
    print(f"⚠️  {len(findings)} Cards mit Quant/Format-Token im model_version:")
    print(f"{'card_file':40s}  {'model_id':35s}  model_version")
    print("-" * 110)
    for f in findings:
        ver = f["model_version_raw"][:50]
        print(f"{f['card_file']:40s}  {f['model_id']:35s}  {ver}")
    print()
    print("Hinweis: Diese Karten brauchen eine kontrollierte Migration, weil")
    print("model_version ein Leaderboard-Groupby-Key ist (Continuity")
    print("historischer Benchmarks darf nicht stillschweigend gebrochen werden).")
    print("Vorgehensweise:")
    print("  1. quantization_format in der Card auf den reinen Quant/Format")
    print("     setzen (z.B. 'Q4_K_XL', 'FP8').")
    print("  2. model_version auf die reine Versionsangabe kürzen")
    print("     (z.B. '4' statt '4 (Q4_K_XL GGUF)').")
    print("  3. Migration pro Card durchführen mit Hash-Detection gleicher")
    print("     Benchmarks vor/nach (siehe scripts/maintenance/migrate_model_versions.py).")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json", action="store_true", help="Output findings as JSON instead of table"
    )
    parser.add_argument(
        "--card-dir", type=Path, default=CARD_DIR, help="Card-Verzeichnis (Default: benchmark_scores/model_cards)"
    )
    args = parser.parse_args()

    findings = scan_cards(args.card_dir)

    if args.json:
        print(json.dumps(findings, indent=2, ensure_ascii=False))
    else:
        print_report(findings)

    return 0  # Audit, kein Hard-Fail


if __name__ == "__main__":
    sys.exit(main())
