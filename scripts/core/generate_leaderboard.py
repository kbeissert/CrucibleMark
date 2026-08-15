#!/usr/bin/env python3
"""Leaderboard generation entry point.

This is a thin wrapper around the leaderboard package.
Kept for backward compatibility with existing Makefile/CI scripts.
"""

import sys
from pathlib import Path

# Setup import path to allow imports from root
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Import main function from new package
# pylint: disable=wrong-import-position
from scripts.leaderboard import main  # noqa: E402

if __name__ == "__main__":
    # Disable printing table to terminal to avoid spam
    main(print_table=False)
