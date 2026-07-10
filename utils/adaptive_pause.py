"""
Adaptive Pause Calculator for Benchmarks.

Provides intelligent memory recovery pauses between benchmark tests
based on model size, previous task intensity, and benchmark mode.
"""

import time
import gc
from enum import Enum
from typing import Any


class BenchmarkMode(Enum):
    """Benchmark modes defining the pause strategy."""

    DEV = "dev"  # Fast iteration (5-10s pauses)
    PRODUCTION = "prod"  # High accuracy (15-30s pauses) - DEFAULT


class ModelConfig:
    """Model-specific configuration and heuristic detection."""

    # Format: 'model_pattern': (base_ram_gb, context_overhead_factor)
    CONFIGS = {
        "7b": (8, 1.0),
        "8b": (10, 1.1),
        "9b": (12, 1.2),  # Gemma 2 9B
        "10b": (13, 1.2),
        "11b": (14, 1.2),
        "12b": (15, 1.2),  # Gemma 3 12B
        "13b": (16, 1.3),
        "14b": (16, 1.3),
        "32b": (32, 1.5),
        "70b": (64, 2.0),
    }

    @classmethod
    def get_config(cls, model_name: str) -> tuple[int, float]:
        """Detect model size configuration from name."""
        model_lower = model_name.lower()

        # Search for explicit size indicators first
        for pattern, config in cls.CONFIGS.items():
            if pattern in model_lower:
                return config
            # Also check for "-7b", ":7b" notations to be safer
            if f"-{pattern}" in model_lower or f":{pattern}" in model_lower:
                return config

        # Default fallback (conservative assumption: 14B class)
        return (16, 1.3)

    @classmethod
    def get_ram_footprint(cls, model_name: str) -> int:
        """Get estimated RAM footprint in GB."""
        base_ram, _ = cls.get_config(model_name)
        return base_ram

    @classmethod
    def get_overhead_factor(cls, model_name: str) -> float:
        """Get context memory overhead factor."""
        _, overhead = cls.get_config(model_name)
        return overhead


class AdaptivePauseCalculator:
    """
    Calculates and executes optimal pauses for memory recovery (macOS Unified Memory).

    Factors considered:
    1. Benchmark Mode (Dev vs. Prod)
    2. Model Size (RAM Footprint)
    3. Previous Task Execution Time
    4. Previous Task Output Length (Context window impact)
    """

    def __init__(self, model_name: str, mode: BenchmarkMode = BenchmarkMode.PRODUCTION):
        self.model_name = model_name
        self.mode = mode

        # Model-specific properties
        self.model_ram = ModelConfig.get_ram_footprint(model_name)
        self.overhead_factor = ModelConfig.get_overhead_factor(model_name)

        # Determine pause ranges based on Mode and RAM
        if mode == BenchmarkMode.DEV:
            # Dev: 5-10s base for smaller models, scaling up slightly for large ones
            base_min = 5
            self.min_pause = max(
                base_min, int(self.model_ram * 0.4)
            )  # e.g. 14B -> max(5, 6) = 6s
            self.max_pause = max(
                10, int(self.model_ram * 0.8)
            )  # e.g. 14B -> max(10, 12) = 12s
        else:  # PRODUCTION (Default)
            # Prod: 15-30s base, scaling up for large models
            base_min = 15
            self.min_pause = max(
                base_min, int(self.model_ram * 1.0)
            )  # e.g. 14B -> max(15, 16) = 16s
            self.max_pause = max(
                30, int(self.model_ram * 2.0)
            )  # e.g. 14B -> max(30, 32) = 32s

        self.base_pause = (self.min_pause + self.max_pause) // 2

    def calculate(self, previous_test: dict[str, Any] | None) -> int:
        """
        Calculate optimal pause duration in seconds.

        Args:
            previous_test: Dict with keys 'execution_time' (sec) and 'response_length' (chars).
                           If None, returns base_pause (for initial settle).
        """
        if previous_test is None:
            return self.base_pause

        execution_time = previous_test.get("execution_time", 0.0)
        response_length = previous_test.get("response_length", 0)

        # Start with base pause
        pause = float(self.base_pause)

        # Factor 1: Execution Time (relative to baseline)
        # Baseline expectation: ~20s
        if execution_time > 40:
            # Long task -> heavy RAM load -> increase significantly
            pause += (self.max_pause - self.base_pause) * 0.8
        elif execution_time > 30:
            pause += (self.max_pause - self.base_pause) * 0.5
        elif execution_time > 20:
            pause += (self.max_pause - self.base_pause) * 0.2
        elif execution_time < 5:
            # Very fast task -> reduce pause
            pause -= (self.base_pause - self.min_pause) * 0.5
        elif execution_time < 10:
            pause -= (self.base_pause - self.min_pause) * 0.2

        # Factor 2: Response Length (Context Window Impact)
        # Scaled by model specific overhead factor
        # 1000 chars ~= 250-300 tokens
        context_impact = (response_length / 1000.0) * self.overhead_factor

        if context_impact > 5.0:  # Huge output
            pause += (self.max_pause - self.base_pause) * 0.4
        elif context_impact > 2.0:
            pause += (self.max_pause - self.base_pause) * 0.2

        # Clamp between min and max
        final_pause = max(self.min_pause, min(self.max_pause, int(pause)))
        return final_pause

    def _get_reason(self, previous_test: dict[str, Any] | None, pause: int) -> str:
        """Generate a human-readable reason for the updated pause."""
        if previous_test is None:
            return "Initial model settle"

        exec_time = previous_test.get("execution_time", 0)
        resp_len = previous_test.get("response_length", 0)

        if exec_time > 40:
            return f"Heavy task ({exec_time:.0f}s) → Max recovery"
        if resp_len > 4000:
            return f"Large output ({resp_len} chars) → Context cleanup"
        if exec_time < 5:
            return f"Quick task ({exec_time:.0f}s) → Minimal waiting"

        return "Standard recovery"

    def wait(
        self, previous_test: dict[str, Any] | None = None, verbose: bool = True
    ) -> int:
        """
        Calculates and executes the pause.

        Returns:
            The executed pause time in seconds.
        """
        pause = self.calculate(previous_test)

        if verbose:
            reason = self._get_reason(previous_test, pause)
            print(f"   ⏸️  Memory Recovery: {pause}s ({reason})")

        # 1. Python GC
        gc.collect()

        # 2. System Sleep (for OS memory pressure relief)
        time.sleep(pause)

        return pause
