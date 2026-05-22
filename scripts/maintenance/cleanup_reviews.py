#!/usr/bin/env python3
"""
Cleanup-Skript für alte Reviews in docs/reviews/.

Behält pro Modell-Verzeichnis je nur den neuesten Benchmark-Review
und den neuesten Bias-Review. Ältere Dateien werden gelöscht.

Verwendung:
    python scripts/maintenance/cleanup_reviews.py            # Dry-Run
    python scripts/maintenance/cleanup_reviews.py --delete   # Löschen
    python scripts/maintenance/cleanup_reviews.py --delete --force
"""

import argparse
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
REVIEWS_DIR = ROOT_DIR / "docs" / "reviews"

# Timestamp pattern: YYYYMMDD_HHMMSS
_TS = re.compile(r"(\d{8}_\d{6})")


def _sort_key(path: Path) -> str:
    m = _TS.search(path.name)
    return m.group(1) if m else "00000000_000000"


def find_old_reviews(reviews_dir: Path) -> list[Path]:
    """Returns all review files that should be deleted (non-latest per category)."""
    to_delete: list[Path] = []

    if not reviews_dir.exists():
        return to_delete

    for model_dir in sorted(reviews_dir.iterdir()):
        if not model_dir.is_dir() or model_dir.name in (".gitkeep", ".DS_Store"):
            continue

        bias_files = sorted(model_dir.glob("bias_review_*.md"), key=_sort_key, reverse=True)
        review_files = sorted(
            [f for f in model_dir.glob("review_*.md") if not f.name.startswith("bias_")],
            key=_sort_key,
            reverse=True,
        )

        # Keep [0] (newest), mark rest for deletion
        to_delete.extend(bias_files[1:])
        to_delete.extend(review_files[1:])

    return to_delete


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bereinigt alte Reviews — behält je 1 Benchmark- und 1 Bias-Review pro Modell.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--delete", action="store_true", help="Wirklich löschen (Standard: Dry-Run)")
    parser.add_argument("--force", action="store_true", help="Ohne Bestätigung (nur mit --delete)")
    args = parser.parse_args()

    dry_run = not args.delete

    print("🔍 Suche alte Reviews in docs/reviews/...")
    to_delete = find_old_reviews(REVIEWS_DIR)

    if not to_delete:
        print("✅ Keine alten Reviews gefunden.")
        return

    mode = "[DRY RUN] " if dry_run else ""
    print(f"\n{mode}Zu löschende Reviews ({len(to_delete)}):\n")
    for f in to_delete:
        print(f"  🗑️  {f.relative_to(ROOT_DIR)}")

    if dry_run:
        print("\nℹ️  Dry-Run — nichts gelöscht. Mit --delete ausführen.")
        return

    if not args.force:
        confirm = input(f"\n⚠️  Wirklich {len(to_delete)} Dateien löschen? [y/N]: ").strip().lower()
        if confirm not in ("y", "yes", "j", "ja"):
            print("❌ Abbruch.")
            return

    deleted = errors = 0
    for f in to_delete:
        try:
            f.unlink()
            print(f"   ✅ Gelöscht: {f.relative_to(ROOT_DIR)}")
            deleted += 1
        except OSError as e:
            print(f"   ❌ Fehler bei {f.name}: {e}")
            errors += 1

    print(f"\n{'✅' if errors == 0 else '⚠️'} Fertig: {deleted} gelöscht, {errors} Fehler.")


if __name__ == "__main__":
    main()
