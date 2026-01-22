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
                error_msg = str(e).lower()
                
                # Check for Rate Limits (HTTP 429)
                is_rate_limit = "429" in error_msg or "rate limit" in error_msg or "too many requests" in error_msg
                
                if attempt == self.max_retries - 1:
                    logger.error("All %d retries failed. Last error: %s", self.max_retries, e)
                    raise

                # Calculate wait time
                if is_rate_limit:
                    # Specific Backoff for Rate Limits: Start high (e.g. 60s) to clear the penalty
                    wait_time = 60 * (attempt + 1)
                    logger.warning("⚠️ Rate Limit detected (attempt %d/%d). Pausing for %ds to cool down...", attempt + 1, self.max_retries, wait_time)
                else:
                    # Standard Exponential Backoff
                    wait_time = 2 ** attempt
                    logger.warning("Retry %d/%d after %ds: %s", attempt + 1, self.max_retries, wait_time, e)
                
                time.sleep(wait_time)

        if last_exception:
            raise last_exception
        raise RuntimeError("All retries failed.")
