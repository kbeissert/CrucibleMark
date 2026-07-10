#!/usr/bin/env python3
"""Quell-CSV-Bereinigung für die 8 Modelle: Tooluse-Zeilen entfernen.

Wichtig: Die 'model'-Spalte ist in den Quell-CSVs NICHT Spalte 0, sondern Spalte 9 (cloud)
bzw. Spalte 10 (commercial). Daher darf der Anker '^(model_id),' NICHT verwendet werden.

Bereinigt aus:
  - cloud_models_benchmark.csv (18 tooluse-Zeilen)
  - commercial_models_benchmark.csv (24 tooluse-Zeilen)
  - local_models_benchmark.csv (0 tooluse-Zeilen)
"""
import csv
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

MODELS = [
    "mistral-large-2512",
    "mistral-small-2603",
    "deepseek/deepseek-v4-pro",
    "nousresearch/hermes-4-405b",
    "gpt-5_5",
    "gemini-3.5-flash",
    "gpt-oss:20b-cloud",
    "nousresearch/hermes-4-70b",
]

# Spalten-Index (0-basiert) für "model" pro CSV
MODEL_COL = {
    "cloud_models_benchmark.csv": 9,       # 10. Spalte (Index 9)
    "commercial_models_benchmark.csv": 10, # 11. Spalte (Index 10)
    "local_models_benchmark.csv": 9,
}

CSVS = [
    "benchmark_scores/cloud_models_benchmark.csv",
    "benchmark_scores/commercial_models_benchmark.csv",
    "benchmark_scores/local_models_benchmark.csv",
]


def sanitize(csv_rel: str) -> None:
    csv_path = ROOT / csv_rel
    bak_path = csv_path.with_suffix(csv_path.suffix + ".bak_pre8")
    if not bak_path.exists():
        shutil.copy2(csv_path, bak_path)
        print(f"  [BAK  ] {bak_path.name} erstellt")
    else:
        print(f"  [BAK  ] {bak_path.name} bereits vorhanden")

    col = MODEL_COL[csv_path.name]
    with csv_path.open(encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)
    header = rows[0]
    data = rows[1:]

    keep = []
    removed = []
    for row in data:
        if len(row) <= col:
            keep.append(row)
            continue
        model_val = row[col].strip()
        # Nur tooluse-Zeilen (asset_id beginnt mit 'tooluse') entfernen
        asset_id = row[0] if row else ""
        if asset_id.startswith("tooluse") and model_val in MODELS:
            removed.append((asset_id, model_val))
        else:
            keep.append(row)

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(header)
        writer.writerows(keep)
    print(f"  [DONE] {csv_path.name}: {len(removed)} tooluse-Zeilen entfernt, {len(keep)} verbleibend")
    if removed:
        models_touched = sorted({m for _, m in removed})
        print(f"        betroffene Modelle: {models_touched}")


def main() -> None:
    print("\n=== Quell-CSV-Bereinigung (8 Modelle) ===")
    for csv_rel in CSVS:
        print(f"\n[{csv_rel}]")
        sanitize(csv_rel)
    print("\nBereinigung abgeschlossen.")


if __name__ == "__main__":
    main()
