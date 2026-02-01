#!/usr/bin/env python3
# ruff: noqa: E402
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
from scripts.leaderboard import main

if __name__ == "__main__":
    main()