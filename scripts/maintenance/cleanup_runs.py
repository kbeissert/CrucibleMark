#!/usr/bin/env python3
"""Cleanup-Skript fuer alte Benchmark-Runs.

Haelt die N neuesten Runs PRO MODELL (kanonische ID via SSoT) und loescht
aeltere automatisch. Funktioniert mit JSON-Ergebnisdateien in
``outputs/runs/``.

Seit Phase 27 (Backup-System SSoT-Refactor) wird die Gruppierung
ueber :func:`scripts.maintenance.cleanup_helpers.canonicalize_run_grouping`
aufgeloest — d.h. ``qwen3.5-35b-q4`` und ``qwen_qwen3.5-35b-q4`` werden
als dasselbe Modell gezaehlt.

Verwendung:
    python scripts/maintenance/cleanup_runs.py                # interaktiv
    python scripts/maintenance/cleanup_runs.py --keep 5      # behalte 5 pro Modell
    python scripts/maintenance/cleanup_runs.py --dry-run     # nur anzeigen
    python scripts/maintenance/cleanup_runs.py --force       # ohne Bestaetigung
"""

import argparse
import logging
import sys
from pathlib import Path

# Projekt-Root auf sys.path
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.maintenance.cleanup_helpers import (  # noqa: E402
    RUN_FILE_RE,
    canonicalize_run_grouping,
)
from utils.backup_targets import RUNS_KEEP_DEFAULT  # noqa: E402

logger = logging.getLogger("cleanup_runs")

#: Default-Pfad fuer Benchmark-Runs
RUNS_DIR = Path("outputs/runs")


def get_benchmark_files(runs_dir: Path) -> dict[str, list[Path]]:
    """Findet alle Benchmark-Ergebnisdateien und gruppiert sie nach Modell.

    Erkennt das Muster ``results_{model}_{timestamp}.json`` und
    gruppiert mit :func:`canonicalize_run_grouping` nach kanonischer
    Model-ID. Innerhalb jeder Gruppe ist die Liste nach mtime absteigend
    sortiert (neueste zuerst).

    Args:
        runs_dir: Wurzelverzeichnis mit ``results_*.json``-Dateien.

    Returns:
        Dict ``{canonical_model_id: [paths newest-first]}``.
    """
    if not runs_dir.exists():
        return {}

    files: list[Path] = [
        p for p in runs_dir.iterdir()
        if p.is_file() and p.suffix == ".json" and RUN_FILE_RE.match(p.name)
    ]
    return canonicalize_run_grouping(files)


def cleanup_runs(
    runs_dir: Path, keep: int = RUNS_KEEP_DEFAULT, force: bool = False, dry_run: bool = False
) -> int:
    """Bereinigt alte Benchmark-Runs, behält die ``keep`` neuesten pro Modell.

    Args:
        runs_dir: Wurzelverzeichnis.
        keep: Anzahl der pro Modell zu behaltenden Runs.
        force: Loeschen ohne Bestaetigung.
        dry_run: Nur anzeigen, nichts loeschen.

    Returns:
        Anzahl der geloeschten (oder zu loeschenden, bei ``dry_run``) Dateien.
    """
    grouped_runs = get_benchmark_files(runs_dir)

    if not grouped_runs:
        print(f"📂 No benchmark runs found in {runs_dir}")
        return 0

    total_files = sum(len(f) for f in grouped_runs.values())
    print(f"🔍 Found {total_files} benchmark files for {len(grouped_runs)} models.")

    files_to_delete: list[Path] = []

    for model, files in grouped_runs.items():
        if len(files) > keep:
            to_remove = files[keep:]
            print(
                f"   Model '{model}': Found {len(files)} runs. Marking {len(to_remove)} for deletion (older than top {keep})."
            )
            files_to_delete.extend(to_remove)

    if not files_to_delete:
        print(f"✅ No cleanup needed. All models have {keep} or fewer runs.")
        return 0

    print(f"\nExample deletion targets ({len(files_to_delete)} total):")
    for f in files_to_delete[:5]:
        print(f"  - {f.name}")
    if len(files_to_delete) > 5:
        print("  ... and others")

    if dry_run:
        print("\n🚫 Dry Run: No files deleted.")
        return len(files_to_delete)

    if not force:
        confirm = input(f"\n⚠️  Really delete {len(files_to_delete)} files? [y/N] ")
        if confirm.lower() not in ["y", "yes"]:
            print("❌ Aborted.")
            return 0

    print("\n🗑️  Deleting files...")
    deleted_count = 0
    for f in files_to_delete:
        try:
            f.unlink()
            print(f"  ✓ Deleted: {f.name}")
            deleted_count += 1
        except OSError as e:
            print(f"  ✗ Error deleting {f.name}: {e}")

    return deleted_count


def main() -> None:
    """CLI-Entry-Point."""
    parser = argparse.ArgumentParser(
        description="Cleanup outdated benchmark run files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=RUNS_DIR,
        help=f"Path to runs directory (default: {RUNS_DIR})",
    )
    parser.add_argument(
        "--keep",
        type=int,
        default=RUNS_KEEP_DEFAULT,
        help=f"Anzahl der zu behaltenden Runs PRO MODELL (default: {RUNS_KEEP_DEFAULT})",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be deleted"
    )
    parser.add_argument(
        "-f", "--force", action="store_true", help="Delete without confirmation"
    )

    args = parser.parse_args()

    # Pfad-Existenz sicherstellen
    if not args.path.exists():
        try:
            args.path.mkdir(parents=True, exist_ok=True)
        except Exception:  # noqa: BLE001
            print(
                f"❌ Error: Directory not found and could not be created: {args.path}"
            )
            sys.exit(1)

    cleanup_runs(args.path, keep=args.keep, force=args.force, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
