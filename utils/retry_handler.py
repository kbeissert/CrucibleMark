"""
Retry Handler Utility
Handles exponential backoff and retry logic for LLM queries.
"""

import time
import logging
from typing import Callable, TypeVar, Any

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
                    logger.error(f"All {self.max_retries} retries failed. Last error: {e}")
                    raise
                
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(f"Retry {attempt + 1}/{self.max_retries} after {wait_time}s: {e}")
                time.sleep(wait_time)
                
        if last_exception:
            raise last_exception
        raise Exception("All retries failed.")
