#!/usr/bin/env python3
"""
Prune Orphaned Reports
======================
Löscht Ausgabeverzeichnisse in outputs/audit_logs und outputs/comparisons,
die zu keinem aktuell konfigurierten oder im Leaderboard aktiven Modell mehr
gehören (z.B. nach einem Modell-Reset oder einer Konfigurationsbereinigung).

Standardmäßig Dry-Run. Mit --delete wird nach Bestätigung gelöscht.

Verwendung:
    python scripts/maintenance/prune_orphaned_reports.py            # Dry-Run
    python scripts/maintenance/prune_orphaned_reports.py --delete   # Löschen
    python scripts/maintenance/prune_orphaned_reports.py --delete --force  # Ohne Bestätigung
"""

import argparse
import csv
import shutil
import sys
from pathlib import Path

import yaml

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def _norm(s: str) -> str:
    """Normalisiert Model-ID oder Verzeichnisname zum Vergleich.
    Konvention: ':' und '/' → '_', Rest bleibt (Punkte, Bindestriche)."""
    return s.replace("/", "_").replace(":", "_").lower()


def load_known_model_ids() -> set[str]:
    """Gibt alle bekannten Modell-IDs zurück (statische Config + Leaderboard)."""
    known: set[str] = set()

    config_path = ROOT_DIR / "benchmark_config.yaml"
    try:
        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)
        for section in config.get("providers", {}).values():
            for provider_cfg in section.values():
                if isinstance(provider_cfg, dict):
                    for m in provider_cfg.get("models", []):
                        if "id" in m:
                            known.add(m["id"])
    except Exception as e:
        print(f"⚠️  benchmark_config.yaml konnte nicht gelesen werden: {e}")

    leaderboard_csv = ROOT_DIR / "benchmark_scores" / "benchmark_leaderboard.csv"
    if leaderboard_csv.exists():
        try:
            with open(leaderboard_csv, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    mid = row.get("Model Name", "").strip()
                    if mid:
                        known.add(mid)
        except Exception as e:
            print(f"⚠️  benchmark_leaderboard.csv konnte nicht gelesen werden: {e}")

    return known


def find_orphaned_dirs(known_ids: set[str]) -> list[Path]:
    known_norms = {_norm(mid) for mid in known_ids}
    orphaned: list[Path] = []
    for category in ["audit_logs", "comparisons"]:
        base = ROOT_DIR / "outputs" / category
        if not base.exists():
            continue
        for d in sorted(base.iterdir()):
            if not d.is_dir() or d.name in (".gitkeep", ".DS_Store"):
                continue
            if _norm(d.name) not in known_norms:
                orphaned.append(d)
    return orphaned


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Findet und löscht verwaiste Report-Verzeichnisse.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Wirklich löschen (Standard: Dry-Run)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Ohne Bestätigung löschen (nur mit --delete wirksam)",
    )
    args = parser.parse_args()

    dry_run = not args.delete

    print("🔍 Lade bekannte Modell-IDs aus Config und Leaderboard...")
    known_ids = load_known_model_ids()
    print(f"   → {len(known_ids)} bekannte Modelle\n")

    orphaned = find_orphaned_dirs(known_ids)

    if not orphaned:
        print("✅ Keine verwaisten Report-Verzeichnisse gefunden.")
        return

    mode_label = "[DRY RUN] " if dry_run else ""
    print(f"{mode_label}Gefundene verwaiste Verzeichnisse:\n")
    for d in orphaned:
        size_kb = sum(f.stat().st_size for f in d.rglob("*") if f.is_file()) // 1024
        print(f"  🗑️  {d.relative_to(ROOT_DIR)}  ({size_kb} KB)")

    print(f"\nGesamt: {len(orphaned)} Verzeichnisse\n")

    if dry_run:
        print("ℹ️  Dry-Run — nichts wurde gelöscht. Mit --delete ausführen zum Löschen.")
        return

    if not args.force:
        confirm = input("⚠️  Wirklich alle löschen? [y/N]: ").strip().lower()
        if confirm not in ("y", "yes", "j", "ja"):
            print("❌ Abbruch.")
            return

    deleted = 0
    errors = 0
    for d in orphaned:
        try:
            shutil.rmtree(d)
            print(f"   ✅ Gelöscht: {d.relative_to(ROOT_DIR)}")
            deleted += 1
        except OSError as e:
            print(f"   ❌ Fehler bei {d.name}: {e}")
            errors += 1

    print(f"\n{'✅' if errors == 0 else '⚠️'} Fertig: {deleted} gelöscht, {errors} Fehler.")


if __name__ == "__main__":
    main()
