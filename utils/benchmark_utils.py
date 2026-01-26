"""
Shared utilities for benchmark runners.
Contains common logic for interactive selection and asset discovery.
"""

import logging
from pathlib import Path
from typing import TypeVar, Dict, Any, Optional
from collections.abc import Callable

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
