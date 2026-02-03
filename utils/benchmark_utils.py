"""
Shared utilities for benchmark runners.
Contains common logic for interactive selection and asset discovery.
"""

import json
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any, Dict, Optional, TypeVar

# pylint: disable=import-error
import yaml

T = TypeVar("T")

logger = logging.getLogger(__name__)


def load_asset_yaml(asset_path: Path) -> Dict[str, Any]:
    """
    Safely loads a YAML asset file.
    Handles single document and multi-document files (returns the metadata one).
    Returns empty dict on failure.
    """
    try:
        with open(asset_path, encoding="utf-8") as f:
            content = f.read()

        # Try single load first
        return yaml.safe_load(content) or {}
    except yaml.YAMLError:
        # Fallback for multi-document files
        try:
            with open(asset_path, encoding="utf-8") as f:
                docs = list(yaml.safe_load_all(f))
            # Find doc with metadata
            return next(
                (d for d in docs if d and isinstance(d, dict) and "metadata" in d),
                docs[0] if docs else {},
            )
        except (OSError, yaml.YAMLError) as e:
            logger.error("Failed to load asset %s: %s", asset_path, e)
            return {}
    except OSError as e:
        logger.error("Failed to read file %s: %s", asset_path, e)
        return {}


def print_header(title: str, width: int = 60) -> None:
    """Prints a formatted header."""
    print(f"\n{'=' * width}")
    print(title)
    print(f"{'=' * width}")


def select_from_list(
    items: list[T],
    display_func: Callable[[T], str | tuple[str, str]],
    prompt: str = "Wähle einen Eintrag",
    title: Optional[str] = None,
) -> Optional[T]:
    """
    Generic interactive selection from a list.

    Args:
        items: List of items to select from
        display_func: Function that takes an item and returns a string representation
                      (or tuple of strings)
        prompt: Prompt text for input
        title: Optional title to print before list

    Returns:
        Selected item or None if aborted
    """
    if not items:
        print("❌ Keine Einträge verfügbar.")
        return None

    if title:
        print_header(title)

    for i, item in enumerate(items, 1):
        display = display_func(item)
        if isinstance(display, tuple):
            for line in display:
                print(f"  {i}. {line}" if line == display[0] else f"     {line}")
        else:
            print(f"  {i}. {display}")

    print("  0. Abbrechen")

    while True:
        try:
            choice = input(f"\n{prompt} (0-{len(items)}): ").strip()
            if choice == "0":
                return None
            idx = int(choice)
            if 1 <= idx <= len(items):
                return items[idx - 1]
            print("⚠️  Ungültige Auswahl.")
        except ValueError:
            print("⚠️  Bitte eine Zahl eingeben.")


def discover_assets(directory: str | Path, pattern: str = "*.yaml") -> list[Path]:
    """
    Finds all assets matching pattern in directory.

    Args:
        directory: Path to search in
        pattern: Glob pattern (default: *.yaml)

    Returns:
        Sorted list of paths
    """
    path = Path(directory)

    if not path.exists():
        return []

    return sorted(list(path.glob(pattern)))


def format_pc_run_data(run_dict: dict, include_extremism: bool = False) -> dict:
    """
    Formatiert Political Compass Run-Daten in standardisiertes Schema.

    Args:
        run_dict: Dict mit keys 'x', 'y', 'x_label', 'y_label'
        include_extremism: Wenn True, füge extremism/sigma hinzu (für AVG)

    Returns:
        Standardisiertes Dict für metadata_json
    """
    x = run_dict.get("x", 0.0)
    y = run_dict.get("y", 0.0)
    x_label = run_dict.get("x_label", "Unbekannt")
    y_label = run_dict.get("y_label", "Unbekannt")

    # Basis-Struktur (für Individual Runs)
    formatted = {
        "coordinates": {"x": x, "y": y, "formatted": f"({x}, {y})"},
        "labels": {"x": x_label, "y": y_label, "archetype": f"{x_label}-{y_label}"},
        "display": {"ideology": f"{x_label} ({x})", "stance": f"{y_label} ({y})"},
    }

    # Erweiterte Struktur (für Aggregate/AVG)
    if include_extremism:
        formatted["extremism"] = run_dict.get(
            "extremism",
            {
                "count": 0,
                "rate": 0.0,
                "status": "✅ Demokratisch",
                "categories": {},
                "details": [],
            },
        )
        formatted["sigma"] = run_dict.get("sigma", {"x": 0.0, "y": 0.0})
        formatted["module_stats"] = run_dict.get("module_stats", {})

    return formatted


def format_political_compass_data(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Formats the raw Political Compass report into a standardized data object.
    Used for consistent JSON structure in results.
    """
    return {
        "coordinates": {
            "x": report["coordinates"]["x"],
            "y": report["coordinates"]["y"],
            "formatted": f"({report['coordinates']['x']}, {report['coordinates']['y']})",
        },
        "labels": {
            "x": report["archetype"].get("x_label", "Unknown"),
            "y": report["archetype"].get("y_label", "Unknown"),
            "archetype": report["archetype"]["label"],
        },
        "display": {
            "ideology": f"{report['archetype'].get('x_label', '?')} ({report['coordinates']['x']})",
            "stance": f"{report['archetype'].get('y_label', '?')} ({report['coordinates']['y']})",
        },
        "extremism": report.get("extremism", {"count": 0, "rate": 0.0}),
    }


def prepare_pc_csv_row(
    model: str,
    report: Dict[str, Any],
    data_object: Dict[str, Any],
    model_version: str = "unknown",
) -> Dict[str, Any]:
    """
    Prepares a dictionary row for the Political Compass CSV.
    """
    return {
        "model": model,
        "model_version": model_version,
        "run_id": "AVG",
        "x_coordinate": report["coordinates"]["x"],
        "y_coordinate": report["coordinates"]["y"],
        "x_label": report["archetype"]["x_label"],
        "y_label": report["archetype"]["y_label"],
        "metrics_json": json.dumps(data_object, ensure_ascii=False),
        "timestamp": report.get("timestamp", ""),
    }
