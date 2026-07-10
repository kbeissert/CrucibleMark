"""
One-time migration: replaces k.A./unknown/empty model_version entries in benchmark CSVs
by re-running get_model_version() with the correct provider context.
"""
import csv
import shutil
import sys
from pathlib import Path

# Ensure project root is in path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from utils.model_utils import get_model_version  # noqa: E402

STALE = {"k.A.", "", "unknown"}
CSVS = [
    ROOT / "benchmark_scores/commercial_models_benchmark.csv",
    ROOT / "benchmark_scores/cloud_models_benchmark.csv",
    ROOT / "benchmark_scores/local_models_benchmark.csv",
]


def migrate() -> None:
    for p in CSVS:
        if not p.exists():
            print(f"  SKIP (nicht vorhanden): {p.name}")
            continue

        with open(p, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames: list[str] = list(reader.fieldnames or [])
            rows = list(reader)

        if not rows:
            print(f"  SKIP (leer): {p.name}")
            continue

        changed = 0
        for r in rows:
            model = r.get("model", "").strip()
            provider = (r.get("provider", "") or "ollama").strip()
            ver = r.get("model_version", "")
            if model and ver in STALE:
                new_ver = get_model_version(model, provider)
                if new_ver != ver:
                    print(f"  {p.name}: {model!r} ({provider}): {ver!r} -> {new_ver!r}")
                    r["model_version"] = new_ver
                    changed += 1

        if changed:
            backup = Path(str(p) + ".bak")
            shutil.copy2(p, backup)
            with open(p, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            print(f"  -> {p.name}: {changed} Zeilen aktualisiert (Backup: {backup.name})")
        else:
            print(f"  -> {p.name}: keine Änderungen nötig")


if __name__ == "__main__":
    migrate()
    print("\nFertig.")
