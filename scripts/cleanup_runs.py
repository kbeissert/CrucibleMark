#!/usr/bin/env python3
"""
Cleanup-Script für alte Benchmark-Runs.

Behält die N neuesten Runs und löscht ältere automatisch.
Schützt .gitkeep und latest Symlink.
"""

import argparse
import shutil
import sys
import traceback
from pathlib import Path

# Constants
TIMESTAMP_DIR_LENGTH = 15  # YYYYMMDD_HHMMSS format
KB_SIZE = 1024.0  # Bytes in a kilobyte


def get_run_directories(runs_dir: Path) -> list[Path]:
    """
    Holt alle Run-Verzeichnisse sortiert nach Timestamp (neueste zuerst).

    Args:
        runs_dir: Pfad zum runs/ Verzeichnis

    Returns:
        Liste der Run-Verzeichnisse, sortiert nach Datum (neueste zuerst)
    """
    if not runs_dir.exists():
        return []

    # Alle Verzeichnisse mit Timestamp-Muster YYYYMMDD_HHMMSS
    runs = [
        d for d in runs_dir.iterdir()
        if d.is_dir()
        and d.name.replace('_', '').isdigit()
        and len(d.name) == TIMESTAMP_DIR_LENGTH
    ]

    # Sortiere nach Name (= Timestamp), neueste zuerst
    return sorted(runs, reverse=True)


def format_size(path: Path) -> str:
    """
    Berechnet Größe eines Verzeichnisses.

    Args:
        path: Verzeichnis-Pfad

    Returns:
        Formatierte Größe (z.B. "2.3 MB")
    """
    total_size = sum(
        f.stat().st_size
        for f in path.rglob('*')
        if f.is_file()
    )

    for unit in ['B', 'KB', 'MB', 'GB']:
        if total_size < KB_SIZE:
            return f"{total_size:.1f} {unit}"
        total_size /= KB_SIZE

    return f"{total_size:.1f} TB"


def _delete_runs(run_paths: list[Path]) -> int:
    """Deletes list of run directories and returns count."""
    deleted = 0
    print("\n🗑️  Lösche Runs...")
    for run in run_paths:
        try:
            shutil.rmtree(run)
            print(f"  ✓ Gelöscht: {run.name}")
            deleted += 1
        except (OSError, PermissionError) as e:
            print(f"  ✗ Fehler bei {run.name}: {e}")
    return deleted


def cleanup_runs(
    runs_dir: Path,
    keep: int = 5,
    force: bool = False,
    dry_run: bool = False
) -> int:
    """
    Löscht alte Benchmark-Runs.

    Args:
        runs_dir: Pfad zum runs/ Verzeichnis
        keep: Anzahl der zu behaltenden Runs
        force: Ohne Bestätigung löschen
        dry_run: Nur anzeigen, nicht löschen

    Returns:
        Anzahl der gelöschten Runs
    """
    runs = get_run_directories(runs_dir)

    if not runs:
        print("📂 Keine Benchmark-Runs gefunden")
        return 0

    if len(runs) <= keep:
        print(f"✓ Nur {len(runs)} Run(s) vorhanden, nichts zu löschen")
        print(f"  (Behalte die neuesten {keep} Runs)")
        return 0

    # Runs zum Behalten und Löschen
    keep_runs = runs[:keep]
    delete_runs = runs[keep:]

    # Zeige Zusammenfassung
    print(f"\n{'='*60}")
    print("🗑️  CLEANUP: BENCHMARK-RUNS")
    print(f"{'='*60}")
    print(f"Gesamt: {len(runs)} Runs")
    print(f"Behalten: {keep} neueste Runs")
    print(f"Löschen: {len(delete_runs)} alte Runs")
    print(f"{'='*60}\n")

    # Zeige zu behaltende Runs
    print("✓ Behalten:")
    for run in keep_runs:
        size = format_size(run)
        print(f"  - {run.name} ({size})")

    # Zeige zu löschende Runs
    print("\n✗ Löschen:")
    for run in delete_runs:
        print(f"  - {run.name} ({format_size(run)})")

    # Dry-run beenden
    if dry_run:
        print("\n🔍 Dry-run Modus - keine Dateien wurden gelöscht")
        return 0

    # Bestätigung einholen (außer bei --force)
    if not force:
        response = input("\nFortfahren? [y/N]: ").strip().lower()
        if response not in ['y', 'yes', 'j', 'ja']:
            print("\n✗ Abgebrochen")
            return 0

    # Lösche alte Runs
    deleted_count = _delete_runs(delete_runs)

    print(f"\n{'='*60}")
    print(f"✅ {deleted_count} Run(s) gelöscht")
    print(f"{'='*60}\n")

    return deleted_count


def main():
    """CLI Entry Point."""
    parser = argparse.ArgumentParser(
        description='Cleanup alter Benchmark-Runs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/cleanup_runs.py                    # Interaktiv, behält 5 neueste
  python scripts/cleanup_runs.py --keep 3           # Behält 3 neueste
  python scripts/cleanup_runs.py --force            # Ohne Bestätigung
  python scripts/cleanup_runs.py --dry-run          # Nur anzeigen
  python scripts/cleanup_runs.py --keep 10 --force  # Behält 10, automatisch
        """
    )

    parser.add_argument(
        '--keep',
        type=int,
        default=5,
        help='Anzahl der neuesten Runs, die behalten werden (Standard: 5)'
    )

    parser.add_argument(
        '--force',
        action='store_true',
        help='Ohne Bestätigung löschen'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Nur anzeigen, was gelöscht würde (keine Dateien löschen)'
    )

    parser.add_argument(
        '--runs-dir',
        type=Path,
        default=Path('outputs/runs'),
        help='Pfad zum runs/ Verzeichnis (Standard: outputs/runs)'
    )

    args = parser.parse_args()

    # Validierung
    if args.keep < 1:
        print("❌ Error: --keep muss mindestens 1 sein")
        sys.exit(1)

    if not args.runs_dir.exists():
        print(f"❌ Error: Verzeichnis nicht gefunden: {args.runs_dir}")
        sys.exit(1)

    # Cleanup ausführen
    try:
        cleanup_runs(
            args.runs_dir,
            keep=args.keep,
            force=args.force,
            dry_run=args.dry_run
        )

    except KeyboardInterrupt:
        print("\n\n✗ Abgebrochen durch Benutzer")
        sys.exit(130)

    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"\n❌ Error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
