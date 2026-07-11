#!/usr/bin/env python3
"""ID-Varianten-Audit für CrucibleMark.

Inventarisiert alle unterschiedlichen Schreibweisen von ``model_id`` über
Configs, Card-Files und Leaderboard-CSVs, gruppiert sie nach kanonischer
``_safe_name``-Form und erzeugt einen Markdown-Report.

Nicht-destruktiv. Schreibt nur nach ``outputs/audits/``.

Verwendung
----------
    python scripts/maintenance/audit_id_variants.py
    python scripts/maintenance/audit_id_variants.py --output outputs/audits/custom.md
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, UTC
from pathlib import Path

import pandas as pd

from utils.config_validator import ConfigValidator  # noqa: E402

# Sicherstellen, dass das Projekt-Root im Pfad ist.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_PROJECT_ROOT))

from utils.model_utils import _safe_name  # noqa: E402

# ID-Spalten, die in den jeweiligen CSV-Dateien vorkommen.
CSV_ID_COLUMNS: dict[str, list[str]] = {
    "benchmark_leaderboard.csv": ["Model ID"],
    "local_models_benchmark.csv": ["model", "model_id"],
    "cloud_models_benchmark.csv": ["model", "model_id"],
    "commercial_models_benchmark.csv": ["model", "model_id"],
    "political_compass_leaderboard.csv": ["model", "model_id"],
    "political_compass_results.csv": ["model", "model_id"],
    "tooluse_leaderboard.csv": ["model", "model_id"],
}

# Provider-Config lebt in config/provider_config.yaml, Benchmark-Config im Root.
# ConfigValidator merged beide automatisch (SSoT, ersetzt direkten yaml.safe_load).
BENCHMARK_CONFIG_PATH = _PROJECT_ROOT / "benchmark_config.yaml"
CARD_DIR = _PROJECT_ROOT / "benchmark_scores" / "model_cards"
SCORES_DIR = _PROJECT_ROOT / "benchmark_scores"


def _collect_config_ids() -> list[str]:
    """Sammelt alle model_id-Eintraege aus den Provider-Configs.

    Nutzt ConfigValidator als SSoT zum Laden + Mergen von benchmark_config.yaml
    und config/provider_config.yaml (inkl. Thinking-Profile-Expansion und
    Duplicate-ID-Checks).
    """
    if not BENCHMARK_CONFIG_PATH.exists():
        return []
    try:
        cfg = ConfigValidator(str(BENCHMARK_CONFIG_PATH)).config
    except Exception:
        return []
    providers = cfg.get("providers", {})
    if not isinstance(providers, dict):
        return []
    ids: list[str] = []
    # Struktur: providers.<kategorie>.<vendor>.models[].id
    # (kategorie in {commercial, cloud, local, …})
    for _category_name, category_cfg in providers.items():
        if not isinstance(category_cfg, dict):
            continue
        for _vendor_name, vendor_cfg in category_cfg.items():
            if not isinstance(vendor_cfg, dict):
                continue
            for model in vendor_cfg.get("models", []) or []:
                if isinstance(model, dict) and isinstance(model.get("id"), str):
                    ids.append(model["id"])
    return ids


def _collect_card_ids() -> list[str]:
    """Sammelt alle model_id-Felder aus den Card-JSON-Dateien."""
    if not CARD_DIR.exists():
        return []
    ids: list[str] = []
    for card_path in sorted(CARD_DIR.glob("*.json")):
        try:
            data = json.loads(card_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict):
            mid = data.get("model_id")
            if isinstance(mid, str) and mid:
                ids.append(mid)
    return ids


# Heuristik: Roh-Werte, die wie Modell-IDs aussehen, muessen mindestens
# einen Buchstaben enthalten UND typische Modell-Namensmuster (Bindestrich,
# Doppelpunkt, Slash oder Punkt in einer Versionsnummer) tragen. Sonst
# handelt es sich um numerische Felder (z. B. token-Werte, scores, max-Werte).
import re  # noqa: E402

_MODEL_ID_HEURISTIC = re.compile(r"[A-Za-z]")
# Mindestens eines dieser Trennzeichen (typisch fuer Modellnamen):
_MODEL_ID_SEPARATORS = re.compile(r"[-:/._]")


def _looks_like_model_id(value: str) -> bool:
    """Prueft, ob ein Roh-Wert wie eine Model-ID aussieht.

    Filtert numerische Felder (z. B. ``12000``, ``8192``, ``True``) heraus,
    die durch die breite Spaltensuche in den CSVs mit erfasst werden.
    """
    if not value or len(value) < 2 or len(value) > 200:
        return False
    if not _MODEL_ID_HEURISTIC.search(value):
        return False
    return _MODEL_ID_SEPARATORS.search(value)


def _collect_csv_ids() -> list[tuple[str, str]]:
    """Sammelt alle model_id-Werte aus den Leaderboard-CSVs.

    Returns
    -------
    Liste von (csv_filename, id_wert)-Tupeln.
    """
    collected: list[tuple[str, str]] = []
    for filename, id_cols in CSV_ID_COLUMNS.items():
        csv_path = SCORES_DIR / filename
        if not csv_path.exists():
            continue
        try:
            df = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
        except Exception:  # noqa: BLE001
            continue
        for col in id_cols:
            if col not in df.columns:
                continue
            for value in df[col].dropna():
                v = str(value).strip()
                if _looks_like_model_id(v):
                    collected.append((filename, v))
    return collected


def _group_by_canonical(ids_with_source: list[tuple[str, str]]) -> dict[str, dict[str, set[str]]]:
    """Gruppiert alle ID-Vorkommen nach kanonischer _safe_name-Form.

    Returns
    -------
    Dict: canonical_id -> {"sources": {source_name, ...}, "variants": {raw_id, ...}}
    """
    grouped: dict[str, dict[str, set[str]]] = defaultdict(
        lambda: {"sources": set(), "variants": set()}
    )
    for source, raw in ids_with_source:
        if not raw:
            continue
        canonical = _safe_name(raw)
        grouped[canonical]["sources"].add(source)
        grouped[canonical]["variants"].add(raw)
    return dict(grouped)


def _render_report(
    config_ids: list[str],
    card_ids: list[str],
    csv_collected: list[tuple[str, str]],
    grouped: dict[str, dict[str, set[str]]],
) -> str:
    """Erzeugt den Markdown-Report."""
    lines: list[str] = []
    lines.append("# ID-Varianten-Audit (CrucibleMark)\n")
    lines.append(
        f"_Erstellt: {datetime.now(tz=UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}_\n"
    )
    lines.append(
        "_Quelle: `scripts/maintenance/audit_id_variants.py`_\n"
    )
    lines.append("")

    # Summary
    total_unique_raw = {raw for _, raw in csv_collected} | set(config_ids) | set(card_ids)
    total_canonical = len(grouped)
    drift_cases = {
        c: info for c, info in grouped.items() if len(info["variants"]) > 1
    }
    lines.append("## Summary\n")
    lines.append(f"- **Eindeutige kanonische IDs**: {total_canonical}")
    lines.append(f"- **Eindeutige Roh-IDs (alle Quellen)**: {len(total_unique_raw)}")
    lines.append(f"- **Drift-Faelle (mehrere Roh-Formen pro Kanon-ID)**: {len(drift_cases)}")
    lines.append("")

    # Quellen
    lines.append("## Quellen-Aufschluesselung\n")
    cfg_count = len(config_ids)
    card_count = len(card_ids)
    csv_count = len(csv_collected)
    lines.append(f"- `benchmark_config.yaml` (incl. provider_config merge): {cfg_count} model_id-Eintraege")
    lines.append(f"- `benchmark_scores/model_cards/*.json`: {card_count} model_id-Felder")
    lines.append(f"- Leaderboard-CSVs: {csv_count} Zellen (Filme x Spalten)")
    lines.append("")

    # Drift-Detail
    if drift_cases:
        lines.append("## Drift-Faelle (mehrere Schreibweisen pro Kanon-ID)\n")
        for canonical in sorted(drift_cases):
            info = drift_cases[canonical]
            variants = sorted(info["variants"])
            sources = sorted(info["sources"])
            lines.append(f"### `{canonical}`\n")
            lines.append(f"- **Varianten gefunden**: {len(variants)}")
            for v in variants:
                marker = " (== Kanon)" if v == canonical else ""
                lines.append(f"    - `{v}`{marker}")
            lines.append(f"- **Quellen**: {', '.join(f'`{s}`' for s in sources)}")
            lines.append("")
    else:
        lines.append("## Drift-Faelle\n")
        lines.append("_Keine — alle Roh-IDs sind bereits kanonisch._\n")

    # Vollstaendige Liste
    lines.append("## Vollstaendige kanonische ID-Liste\n")
    lines.append("| Kanonische ID | Varianten | Quellen |")
    lines.append("|---|---|---|")
    for canonical in sorted(grouped):
        info = grouped[canonical]
        variants = ", ".join(f"`{v}`" for v in sorted(info["variants"]))
        sources = ", ".join(f"`{s}`" for s in sorted(info["sources"]))
        lines.append(f"| `{canonical}` | {variants} | {sources} |")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="ID-Varianten-Audit")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Pfad fuer den Report (Default: outputs/audits/id_variants_<timestamp>.md)",
    )
    args = parser.parse_args()

    config_ids = _collect_config_ids()
    card_ids = _collect_card_ids()
    csv_collected = _collect_csv_ids()

    all_pairs: list[tuple[str, str]] = (
        [("benchmark_config.yaml", x) for x in config_ids]
        + [("model_cards/*.json", x) for x in card_ids]
        + csv_collected
    )
    grouped = _group_by_canonical(all_pairs)

    report = _render_report(config_ids, card_ids, csv_collected, grouped)

    if args.output is None:
        audits_dir = _PROJECT_ROOT / "outputs" / "audits"
        audits_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S")
        out_path = audits_dir / f"id_variants_{ts}.md"
    else:
        out_path = args.output
        out_path.parent.mkdir(parents=True, exist_ok=True)

    out_path.write_text(report, encoding="utf-8")
    print(f"Report geschrieben: {out_path}")
    print(f"Drift-Faelle: {sum(1 for v in grouped.values() if len(v['variants']) > 1)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
