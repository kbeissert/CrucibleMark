"""
Utility functions for environment variable management.
"""

import os
from typing import Optional


def get_required_env(key: str, error_msg: Optional[str] = None) -> str:
    """
    Retrieves an environment variable or raises ValueError if missing.

    Args:
        key: The environment variable key.
        error_msg: Custom error message to raise if missing.

    Returns:
        The value of the environment variable.

    Raises:
        ValueError: If the environment variable is not set.
    """
    val = os.getenv(key)
    if not val:
        raise ValueError(error_msg or f"Environment variable {key} not set")
    return val
