"""
Module containing path and encoding constants for the Political Compass benchmark.

Constants:
    TEMP_DIR: Default temporary directory path.
    DEFAULT_ENCODING: Default encoding for file operations.
    DATE_FORMAT: Default date format for timestamp generation.
"""

from pathlib import Path

TEMP_DIR = Path("outputs/temp")
DEFAULT_ENCODING = "utf-8"
DATE_FORMAT = "%Y%m%d_%H%M%S"
