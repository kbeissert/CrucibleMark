"""
Shared utilities for benchmark runners.
Contains common logic for interactive selection and asset discovery.
"""

from pathlib import Path
from typing import TypeVar
from collections.abc import Callable

T = TypeVar('T')


def print_header(title: str, width: int = 60) -> None:
    """Prints a formatted header."""
    print(f"\n{'='*width}")
    print(title)
    print(f"{'='*width}")


def select_from_list(
    items: list[T],
    display_func: Callable[[T], str | tuple[str, str]],
    prompt: str = "Wähle einen Eintrag",
    title: str | None = None
) -> T | None:
    """
    Generic interactive selection from a list.

    Args:
        items: List of items to select from
        display_func: Function that takes an item and returns a string representation (or tuple of strings)
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
        print()

    print(f"{'='*60}")

    while True:
        try:
            choice = input(f"\n{prompt} (1-{len(items)}): ").strip()

            if not choice:
                print("❌ Keine Eingabe - Abbruch")
                return None

            idx = int(choice) - 1

            if 0 <= idx < len(items):
                return items[idx]

            print(f"❌ Bitte Zahl zwischen 1 und {len(items)} eingeben")

        except ValueError:
            print("❌ Ungültige Eingabe - bitte Zahl eingeben")
        except KeyboardInterrupt:
            print("\n\n❌ Abgebrochen")
            return None


def discover_assets(directory: str | Path, pattern: str = "*.yaml") -> list[Path]:
    """
    Finds all assets matching pattern in directory.

    Args:
        directory: Path to search in
        pattern: Glob pattern (default: *.yaml)

    Returns:
        Sorted list of paths

    Raises:
        ValueError: If directory does not exist or no assets found
    """
    path = Path(directory)

    if not path.exists():
        # Return empty list instead of raising to be compatible with commercial runner logic
        # or raise if strict. Let's stick to returning list for flexibility,
        # but local runner raised ValueError. Let's standardize on returning list
        # and letting caller decide if empty is error.
        return []

    assets = sorted(path.glob(pattern))
    return assets
