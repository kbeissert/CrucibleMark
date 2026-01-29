"""
Reasoning Logic Benchmark Module.

Comprehensive reasoning testing including logical puzzles, paradoxes, deadlocks,
and metacognitive reasoning quality assessment.
"""

from benchmark_modules.reasoning_logic.test import ReasoningLogicTest
from benchmark_modules.reasoning_logic.core.evaluators import (
    ReasoningEvaluator,
    calculate_rci,
    classify_model,
)

__all__ = [
    "ReasoningLogicTest",
    "ReasoningEvaluator",
    "calculate_rci",
    "classify_model",
]
