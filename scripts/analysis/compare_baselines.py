#!/usr/bin/env python3
"""
Benchmark Baseline Comparator
=============================

Compares two benchmark result JSON files to detect regression or deviation.
Useful for:
1. Differential Testing (Commercial vs Local)
2. Regression Testing (New Code vs Old Code)
3. Consistency Checks

Usage:
    python scripts/compare_baselines.py --ref path/to/ref.json --test path/to/test.json
"""

import sys
import json
import argparse
from typing import Any
import math
from pathlib import Path

# Setup path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# pylint: disable=wrong-import-position
from utils.constants import Colors  # noqa: E402


def load_json(path: str) -> Any:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"{Colors.FAIL}Error loading {path}: {e}{Colors.ENDC}")
        sys.exit(1)


def compare_political_compass(
    ref: dict[str, Any], test: dict[str, Any], threshold: float
):
    """Specific comparison logic for Political Compass results."""
    print(f"\n{Colors.HEADER}🧭 Political Compass Comparison{Colors.ENDC}")

    ref_coords = ref.get("coordinates", {})
    test_coords = test.get("coordinates", {})

    ref_x = ref_coords.get("x", 0.0)
    ref_y = ref_coords.get("y", 0.0)

    test_x = test_coords.get("x", 0.0)
    test_y = test_coords.get("y", 0.0)

    delta_x = test_x - ref_x
    delta_y = test_y - ref_y

    # Calculate Euclidean distance shift
    shift = math.sqrt(delta_x**2 + delta_y**2)

    print(f"{'Metric':<10} {'Reference':<10} {'Test':<10} {'Delta':<10}")
    print("-" * 45)
    print(f"{'Axis X':<10} {ref_x:>10.2f} {test_x:>10.2f} {delta_x:>10.2f}")
    print(f"{'Axis Y':<10} {ref_y:>10.2f} {test_y:>10.2f} {delta_y:>10.2f}")
    print("-" * 45)

    color = Colors.GREEN if shift < 2.0 else Colors.WARNING
    if shift > 4.0:
        color = Colors.FAIL

    print(
        f"Total Shift (Euclidean): {color}{shift:.2f}{Colors.ENDC} (Threshold: 2.0/4.0)"
    )

    # Compare Archetypes
    ref_arch = ref.get("archetype", {}).get("label", "Unknown")
    test_arch = test.get("archetype", {}).get("label", "Unknown")

    if ref_arch != test_arch:
        print(
            f"\n{Colors.WARNING}⚠️  Archetype changed: {ref_arch} -> {test_arch}{Colors.ENDC}"
        )
    else:
        print(f"\n{Colors.GREEN}✅ Archetype stable: {ref_arch}{Colors.ENDC}")


def compare_standard_benchmark(
    ref: list[dict[str, Any]], test: list[dict[str, Any]], threshold: float
):
    """Compares standard list-based benchmark results."""
    print(f"\n{Colors.HEADER}📊 Score Comparison{Colors.ENDC}")

    # Index by Asset ID
    ref_map = {item.get("id", item.get("asset_id", "unknown")): item for item in ref}
    test_map = {item.get("id", item.get("asset_id", "unknown")): item for item in test}

    common_ids = set(ref_map.keys()) & set(test_map.keys())
    missing_ids = set(ref_map.keys()) - set(test_map.keys())
    # new_ids = set(test_map.keys()) - set(ref_map.keys())

    print(f"{'Asset ID':<30} {'Ref %':<8} {'Test %':<8} {'Delta':<8} {'Status'}")
    print("-" * 75)

    warnings = 0
    total_delta = 0.0

    for aid in sorted(common_ids):
        r_item = ref_map[aid]
        t_item = test_map[aid]

        r_score = r_item.get("percentage", r_item.get("score", 0) * 100)
        t_score = t_item.get("percentage", t_item.get("score", 0) * 100)

        delta = t_score - r_score
        total_delta += abs(delta)

        status = "OK"
        color = Colors.ENDC

        if abs(delta) > (threshold * 100):
            status = "DEV ⚠️"
            color = Colors.WARNING
            warnings += 1

        if abs(delta) > 50:  # Massive swing
            status = "DIFF ❗"
            color = Colors.FAIL

        print(
            f"{aid[:30]:<30} {r_score:>8.1f} {t_score:>8.1f} {delta:>+8.1f} {color}{status}{Colors.ENDC}"
        )

    if missing_ids:
        print(
            f"\n{Colors.WARNING}Missing in Test ({len(missing_ids)}): {', '.join(list(missing_ids)[:5])}...{Colors.ENDC}"
        )

    avg_delta = total_delta / len(common_ids) if common_ids else 0
    print("-" * 75)
    print(f"Average Absolute Deviation: {avg_delta:.1f}%")

    if warnings > 0:
        print(
            f"\n{Colors.WARNING}⚠️  Found {warnings} significant deviations (> {threshold * 100}%){Colors.ENDC}"
        )
    else:
        print(f"\n{Colors.GREEN}✅ Results correspond to baseline.{Colors.ENDC}")


def _select_runs_from_files(files: list[Path], TerminalUI) -> tuple[str, str]:
    """Manueller Modus: zwei Dateien direkt aus der Liste wählen."""
    print(f"\n{Colors.CYAN}--- SCHRITT 1: Referenz-Datei ---{Colors.ENDC}")
    ref_file = TerminalUI.select_from_list(files, lambda x: x.name, prompt="Wähle Referenz-Datei:")
    if not ref_file:
        sys.exit(0)

    print(f"\n{Colors.CYAN}--- SCHRITT 2: Test-Datei ---{Colors.ENDC}")
    test_file = TerminalUI.select_from_list(files, lambda x: x.name, prompt="Wähle Test-Datei:")
    if not test_file:
        sys.exit(0)

    return str(ref_file), str(test_file)


def _select_interne_vergleich(model_list, models_to_files, TerminalUI) -> tuple[str, str]:
    selected_model = TerminalUI.select_from_list(
        model_list,
        lambda x: f"{x} ({len(models_to_files[x])} Läufe vorhanden)",
        prompt="Wähle das Modell:",
        title="Modell-Auswahl"
    )
    if not selected_model:
        sys.exit(0)

    runs = models_to_files[selected_model]
    if len(runs) < 2:
        print(f"{Colors.WARNING}Nicht genug Läufe für {selected_model} (Mindestens 2 benötigt).{Colors.ENDC}")
        sys.exit(1)

    print(f"\n{Colors.CYAN}--- SCHRITT 1: Referenz (Zumeist der ältere Lauf) ---{Colors.ENDC}")
    ref_file = TerminalUI.select_from_list(runs, lambda x: x.name, prompt="Wähle Referenz-Lauf (Basis):")
    if not ref_file:
        sys.exit(0)

    print(f"\n{Colors.CYAN}--- SCHRITT 2: Test (Zumeist der neuere Lauf) ---{Colors.ENDC}")
    test_file = TerminalUI.select_from_list(runs, lambda x: x.name, prompt="Wähle Test-Lauf (Neuer Wert):")
    if not test_file:
        sys.exit(0)

    return str(ref_file), str(test_file)


def _select_modell_vergleich(model_list, models_to_files, TerminalUI) -> tuple[str, str]:
    print(f"\n{Colors.CYAN}--- SCHRITT 1: Referenz-Modell (Zumeist das bekannte/kommerzielle Modell) ---{Colors.ENDC}")
    ref_model = TerminalUI.select_from_list(model_list, lambda x: x, prompt="Wähle Referenz-Modell:")
    if not ref_model:
        sys.exit(0)

    print(f"\n{Colors.CYAN}--- SCHRITT 2: Test-Modell (Zumeist das neue/lokale Modell) ---{Colors.ENDC}")
    test_model = TerminalUI.select_from_list(model_list, lambda x: x, prompt="Wähle Test-Modell:")
    if not test_model:
        sys.exit(0)

    ref_file = models_to_files[ref_model][0]
    test_file = models_to_files[test_model][0]

    print(f"\n{Colors.HEADER}Ausgewählte Dateien:{Colors.ENDC}")
    print(f"Referenz ({ref_model}): {ref_file.name}")
    print(f"Test ({test_model}):     {test_file.name}\n")

    return str(ref_file), str(test_file)


def _discover_run_files() -> tuple[list[Path], dict[str, list[Path]]]:
    """Liest outputs/runs/results_*.json und gruppiert nach Modell-Slug."""
    import re

    runs_dir = ROOT_DIR / "outputs" / "runs"
    if not runs_dir.exists():
        print(f"{Colors.FAIL}Directory {runs_dir} not found.{Colors.ENDC}")
        sys.exit(1)

    files = list(runs_dir.glob("results_*.json"))
    files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    if not files:
        print(f"{Colors.FAIL}Keine Benchmark-Ergebnisse in {runs_dir} gefunden.{Colors.ENDC}")
        sys.exit(1)

    pattern = re.compile(r"results_(.*)_(\d{8}_\d{6})\.json")
    models_to_files: dict[str, list[Path]] = {}
    for f in files:
        match = pattern.match(f.name)
        if match:
            model_name = match.group(1)
            models_to_files.setdefault(model_name, []).append(f)
    return files, models_to_files


def interactive_selection() -> tuple[str, str]:
    """Provides an interactive CLI to select reference and test result files."""
    from utils.benchmark_ui import TerminalUI

    files, models_to_files = _discover_run_files()

    modes = [
        ("Interner Vergleich", "Gleiches Modell - 2 verschiedene Läufe vergleichen"),
        ("Modell-Vergleich", "Zwei verschiedene Modelle (jeweils letzter Lauf) vergleichen"),
        ("Manuelle Auswahl", "Alle Dateien direkt als Liste anzeigen")
    ]

    selected_mode = TerminalUI.select_from_list(
        modes,
        lambda m: m,
        prompt="Was möchtest du vergleichen?",
        title="Vergleichs-Modus wählen"
    )

    if not selected_mode:
        print("Abbruch.")
        sys.exit(0)

    mode_name = selected_mode[0]

    if mode_name == "Interner Vergleich":
        model_list = sorted(list(models_to_files.keys()))
        return _select_interne_vergleich(model_list, models_to_files, TerminalUI)
    elif mode_name == "Modell-Vergleich":
        model_list = sorted(list(models_to_files.keys()))
        return _select_modell_vergleich(model_list, models_to_files, TerminalUI)
    return _select_runs_from_files(files, TerminalUI)


def main():
    parser = argparse.ArgumentParser(description="Compare Benchmark Results")
    parser.add_argument("--ref", required=False, help="Reference JSON file")
    parser.add_argument("--test", required=False, help="Test JSON file")
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.15,
        help="Warning threshold (e.g. 0.15 for 15 percent)",
    )

    args = parser.parse_args()

    ref_path = args.ref
    test_path = args.test

    if not ref_path or not test_path:
        print(f"{Colors.HEADER}Interaktiver Baseline Comparator{Colors.ENDC}")
        print("Starte Dateiauswahl (Nutzung via Kommandozeile mit --ref und --test weiterhin möglich)...\n")
        ref_path, test_path = interactive_selection()

    ref_data = load_json(ref_path)
    test_data = load_json(test_path)

    # Detect Type
    is_pol_compass = isinstance(ref_data, dict) and "coordinates" in ref_data

    if is_pol_compass:
        compare_political_compass(ref_data, test_data, args.threshold)
    elif isinstance(ref_data, list):
        compare_standard_benchmark(ref_data, test_data, args.threshold)
    else:
        print(f"{Colors.FAIL}Unknown Result Format.{Colors.ENDC}")
        sys.exit(1)


if __name__ == "__main__":
    main()
