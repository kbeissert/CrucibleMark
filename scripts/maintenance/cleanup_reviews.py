#!/usr/bin/env python3
"""Cleanup-Skript fuer alte Reviews in ``docs/reviews/``.

Haelt pro Modell-Verzeichnis je nur den neuesten Benchmark-Review,
den neuesten Bias-Review und den neuesten Tool-Use-Review. Aeltere
Dateien werden geloescht.

Seit Phase 27 (Backup-System SSoT-Refactor) wird der Verzeichnisname
durch :func:`utils.model_utils._safe_name` normalisiert, damit
``qwen3.5-35b-a3b-q4`` und ``qwen_qwen3.5-35b-a3b-q4`` als dasselbe
Modell gezaehlt werden.

Verwendung:
    python scripts/maintenance/cleanup_reviews.py            # Dry-Run
    python scripts/maintenance/cleanup_reviews.py --delete   # Loeschen
    python scripts/maintenance/cleanup_reviews.py --delete --force
"""

import argparse
import logging
import re
import sys
from pathlib import Path

# Projekt-Root auf sys.path
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from utils.backup_targets import REVIEWS_KEEP_PER_CATEGORY  # noqa: E402
from utils.model_utils import _safe_name  # noqa: E402

logger = logging.getLogger("cleanup_reviews")

REVIEWS_DIR = _ROOT / "docs" / "reviews"

# Timestamp-Pattern: YYYYMMDD_HHMMSS
_TS = re.compile(r"(\d{8}_\d{6})")


def _sort_key(path: Path) -> str:
    """Sortierschluessel: Timestamp im Dateinamen, oder Default-Wert."""
    m = _TS.search(path.name)
    return m.group(1) if m else "00000000_000000"


def find_old_reviews(reviews_dir: Path) -> list[Path]:
    """Liefert alle Review-Dateien, die geloescht werden sollen (non-latest).

    Pro Modell-Verzeichnis und pro Kategorie (``review_*.md``,
    ``bias_review_*.md``, ``tooluse_narrative_review_*.md``) wird nur
    der neueste Eintrag behalten. Verzeichnisnamen werden via
    :func:`_safe_name` normalisiert, um Schreibweisenvarianten
    zusammenzufuehren.

    Args:
        reviews_dir: Wurzelverzeichnis ``docs/reviews/``.

    Returns:
        Liste der zu loeschenden Pfade.
    """
    to_delete: list[Path] = []

    if not reviews_dir.exists():
        return to_delete

    for model_dir in sorted(reviews_dir.iterdir()):
        if not model_dir.is_dir() or model_dir.name in (".gitkeep", ".DS_Store"):
            continue
        # Phase 27: kanonischer Modell-Key (Robustheit bei Slug-Drift)
        _ = _safe_name(model_dir.name)

        bias_files = sorted(
            model_dir.glob("bias_review_*.md"),
            key=_sort_key,
            reverse=True,
        )
        review_files = sorted(
            [f for f in model_dir.glob("review_*.md") if not f.name.startswith("bias_")],
            key=_sort_key,
            reverse=True,
        )
        tooluse_files = sorted(
            model_dir.glob("tooluse_narrative_review_*.md"),
            key=_sort_key,
            reverse=True,
        )

        # Behalte die neuesten REVIEWS_KEEP_PER_CATEGORY (SSoT), markiere Rest zur Loeschung
        to_delete.extend(bias_files[REVIEWS_KEEP_PER_CATEGORY:])
        to_delete.extend(review_files[REVIEWS_KEEP_PER_CATEGORY:])
        to_delete.extend(tooluse_files[REVIEWS_KEEP_PER_CATEGORY:])

    return to_delete


def main() -> None:
    """CLI-Entry-Point."""
    parser = argparse.ArgumentParser(
        description="Bereinigt alte Reviews — behaelt je 1 Benchmark-, 1 Bias- und 1 Tool-Use-Review pro Modell.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--delete", action="store_true", help="Wirklich loeschen (Standard: Dry-Run)"
    )
    parser.add_argument(
        "--force", action="store_true", help="Ohne Bestaetigung (nur mit --delete)"
    )
    args = parser.parse_args()

    dry_run = not args.delete

    print("🔍 Suche alte Reviews in docs/reviews/...")
    to_delete = find_old_reviews(REVIEWS_DIR)

    if not to_delete:
        print("✅ Keine alten Reviews gefunden.")
        return

    mode = "[DRY RUN] " if dry_run else ""
    print(f"\n{mode}Zu loeschende Reviews ({len(to_delete)}):\n")
    for f in to_delete:
        print(f"  🗑️  {f.relative_to(_ROOT)}")

    if dry_run:
        print("\nℹ️  Dry-Run — nichts geloescht. Mit --delete ausfuehren.")
        return

    if not args.force:
        confirm = input(f"\n⚠️  Wirklich {len(to_delete)} Dateien loeschen? [y/N]: ").strip().lower()
        if confirm not in ("y", "yes", "j", "ja"):
            print("❌ Abbruch.")
            return

    deleted = errors = 0
    for f in to_delete:
        try:
            f.unlink()
            print(f"   ✅ Geloescht: {f.relative_to(_ROOT)}")
            deleted += 1
        except OSError as e:
            print(f"   ❌ Fehler bei {f.name}: {e}")
            errors += 1

    print(f"\n{'✅' if errors == 0 else '⚠️'} Fertig: {deleted} geloescht, {errors} Fehler.")


if __name__ == "__main__":
    main()
