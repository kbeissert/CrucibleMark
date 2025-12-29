"""
Retry Handler Utility
Handles exponential backoff and retry logic for LLM queries.
"""

import time
import logging
from typing import TypeVar, Any
from collections.abc import Callable

# Configure logging
logger = logging.getLogger(__name__)

T = TypeVar('T')

class RetryHandler:
    """
    Handles retry logic with exponential backoff.
    """

    def __init__(self, max_retries: int = 3):
        """
        Initialize RetryHandler.

        Args:
            max_retries: Maximum number of retry attempts.
        """
        self.max_retries = max_retries

    def execute_with_retry(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Execute a function with retry logic.

        Args:
            func: Function to execute.
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.

        Returns:
            Result of the function.

        Raises:
            Exception: If all retries fail.
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt == self.max_retries - 1:
                    logger.error("All %d retries failed. Last error: %s", self.max_retries, e)
                    raise

                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning("Retry %d/%d after %ds: %s", attempt + 1, self.max_retries, wait_time, e)
                time.sleep(wait_time)

        if last_exception:
            raise last_exception
        raise RuntimeError("All retries failed.")
