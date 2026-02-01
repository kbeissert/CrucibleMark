#!/usr/bin/env python3
"""
Cleanup-Script für alte Benchmark-Runs.

Behält die N neuesten Runs PRO MODELL und löscht ältere automatisch.
Funktioniert mit JSON-Ergebnisdateien in outputs/runs/
"""

import argparse
import sys
import re
from pathlib import Path
from collections import defaultdict

# Constants
RUNS_DIR = Path("outputs/runs")


def get_benchmark_files(runs_dir: Path) -> dict[str, list[Path]]:
    """
    Finds all benchmark result files and groups them by model.
    Checks for pattern: results_{model}_{timestamp}.json
    
    Returns:
        Dict {model_name: [sorted list of paths (newest first)]}
    """
    if not runs_dir.exists():
        return {}

    pattern = re.compile(r"results_(.+)_(\d{8}_\d{6})\.json")
    grouped_files = defaultdict(list)

    for item in runs_dir.iterdir():
        if item.is_file() and item.suffix == ".json":
            match = pattern.match(item.name)
            if match:
                model_name = match.group(1)
                timestamp_str = match.group(2)
                # Store tuple (timestamp, path) for sorting
                grouped_files[model_name].append((timestamp_str, item))

    # Sort each list by timestamp descending (newest first)
    result = {}
    for model, files in grouped_files.items():
        sorted_files = sorted(files, key=lambda x: x[0], reverse=True)
        # Keep only paths
        result[model] = [f[1] for f in sorted_files]

    return result


def cleanup_runs(
    runs_dir: Path, keep: int = 5, force: bool = False, dry_run: bool = False
) -> int:
    """
    Cleans up old benchmark result files, keeping 'keep' latest per model.
    """
    grouped_runs = get_benchmark_files(runs_dir)

    if not grouped_runs:
        print(f"📂 No benchmark runs found in {runs_dir}")
        return 0

    total_files = sum(len(f) for f in grouped_runs.values())
    print(f"🔍 Found {total_files} benchmark files for {len(grouped_runs)} models.")

    files_to_delete = []

    for model, files in grouped_runs.items():
        if len(files) > keep:
            to_remove = files[keep:]
            print(f"   Model '{model}': Found {len(files)} runs. Marking {len(to_remove)} for deletion (older than top {keep}).")
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


def main():
    parser = argparse.ArgumentParser(
        description="Cleanup outdated benchmark run files.",
        formatter_class=argparse.RawDescriptionHelpFormatter
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
        default=5,
        help="Number of runs to keep PER MODEL (default: 5)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be deleted"
    )
    parser.add_argument(
        "-f", "--force", action="store_true", help="Delete without confirmation"
    )

    args = parser.parse_args()

    # Check path existence
    if not args.path.exists():
        # Create it if it doesn't exist to avoid error
        try:
             args.path.mkdir(parents=True, exist_ok=True)
        except Exception:
             print(f"❌ Error: Directory not found and could not be created: {args.path}")
             sys.exit(1)

    cleanup_runs(args.path, keep=args.keep, force=args.force, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
