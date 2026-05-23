"""Audit log scanning for the review pipeline.

Scans audit markdown files and benchmark CSVs to surface constraint violations,
empty responses, and non-success statuses.
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

_BENCHMARK_CSV_NAMES = (
    "commercial_models_benchmark.csv",
    "cloud_models_benchmark.csv",
    "local_models_benchmark.csv",
)

_WARNING_PATTERN = re.compile(
    r'(?:-\s+)?> \[!WARNING\]\s*\n((?:> [^\n]*\n?)+)',
    re.MULTILINE,
)


def build_constraint_violations_summary(model_dir: Path) -> str:
    """Scan all audit-log .md files for hard constraint violations.

    Recognizes both list-prefixed (- > [!WARNING]) and direct (> [!WARNING]) formats.
    """
    violations: list[tuple[str, str]] = []

    for md_file in sorted(model_dir.rglob("*.md")):
        if md_file.name in ("00_bias_report.md", "pol_comp_report.md"):
            continue
        try:
            content = md_file.read_text(encoding="utf-8")
        except Exception:
            continue

        for match in _WARNING_PATTERN.finditer(content):
            body = re.sub(r"^> ?", "", match.group(1), flags=re.MULTILINE).strip()
            violations.append((md_file.stem, body))

    if not violations:
        return ""

    lines = [f"### Constraint-Violations-Summary ({len(violations)} erkannt)\n"]
    for task_id, text in violations:
        lines.append(f"- **[{task_id}]**: {text}")

    return "\n".join(lines)


def build_empty_response_context(model_name: str) -> str:
    """Find assets with response_length=0 and status=success across all benchmark CSVs."""
    empty_assets: list[tuple[str, str]] = []

    for csv_name in _BENCHMARK_CSV_NAMES:
        csv_path = ROOT_DIR / "benchmark_scores" / csv_name
        if not csv_path.exists():
            continue
        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    if row.get("model") != model_name or row.get("status") != "success":
                        continue
                    asset_id = row.get("asset_id", "unknown")
                    if asset_id.startswith("political_compass"):
                        continue
                    try:
                        rlen = float(row.get("response_length", 1) or 1)
                    except (ValueError, TypeError):
                        continue
                    if rlen == 0.0:
                        module = asset_id.split("_")[0] if "_" in asset_id else asset_id
                        empty_assets.append((asset_id, module))
        except Exception:
            continue

    if not empty_assets:
        return ""

    lines = [f"### Assets ohne sichtbare Antwort ({len(empty_assets)} erkannt)\n"]
    lines.append(
        "Das Modell hat die folgenden Tasks als `status=success` abgeschlossen, "
        "aber keinen sichtbaren Text produziert (`response_length=0`). "
        "Mögliche Ursachen: interner Reasoning-Only-Output, Sicherheitsfilter-Verweigerung (silent), oder API-Silent-Failure.\n"
    )
    for asset_id, module in empty_assets:
        lines.append(f"- **[{asset_id}]** (Modul: {module})")

    return "\n".join(lines)


def build_non_success_context(model_name: str) -> str:
    """Find assets with language_mismatch, truncated, or refusal status."""
    findings: dict[str, list[tuple[str, str]]] = {
        "language_mismatch": [],
        "truncated": [],
        "refusal": [],
    }

    for csv_name in _BENCHMARK_CSV_NAMES:
        csv_path = ROOT_DIR / "benchmark_scores" / csv_name
        if not csv_path.exists():
            continue
        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    if row.get("model") != model_name:
                        continue
                    status = row.get("status", "")
                    if status not in findings:
                        continue
                    asset_id = row.get("asset_id", "unknown")
                    if asset_id.startswith("political_compass"):
                        continue
                    module = asset_id.split("_")[0] if "_" in asset_id else asset_id
                    findings[status].append((asset_id, module))
        except Exception:
            continue

    total = sum(len(v) for v in findings.values())
    if total == 0:
        return ""

    status_labels = {
        "language_mismatch": "Sprachfehler (falsche Antwortsprache)",
        "truncated": "Abgeschnittene Antwort (Token-Limit erreicht)",
        "refusal": "Explizite Verweigerung",
    }

    lines = [f"### Non-Success-Ergebnisse ({total} erkannt)\n"]
    lines.append(
        "Die folgenden Tasks wurden **nicht mit `status=success`** abgeschlossen. "
        "Sie fließen mit 0% oder stark reduzierten Scores in die Gesamtbewertung ein und sind "
        "qualitativ bedeutsam für die Einschätzung des Modells.\n"
    )
    for status_key, label in status_labels.items():
        items = findings[status_key]
        if not items:
            continue
        lines.append(f"**{label}** (`{status_key}`, {len(items)} Asset(s)):")
        for asset_id, module in items:
            lines.append(f"- **[{asset_id}]** (Modul: {module})")
        lines.append("")

    return "\n".join(lines)
