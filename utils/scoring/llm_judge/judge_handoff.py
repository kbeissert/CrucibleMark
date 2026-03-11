"""
LLM Judge Handoff Layer.
Pure data transport between Phase 1 (benchmark execution) and Phase 3 (judge scoring).

Responsibilities:
  - Hold all fields needed for the judge in a typed, immutable-safe container.
  - Freeze response_time_ms so it can never be overwritten after creation.
  - Provide JSON persistence helpers for long overnight runs.

NO imports from judge_runner or judge_prompt_builder — this is a pure data layer.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class PendingJudgeResult:
    """
    Carries all context required for the LLM Judge, created after a benchmark task
    completes (Phase 1) and consumed when the judge runs (Phase 3).

    response_time_ms is frozen: it must never be altered after creation.
    Fields prefixed with ``judge_`` are filled in during Phase 3.
    """

    # --- Identification ---
    task_id: str
    module_id: str

    # --- Task context (frozen after creation) ---
    task_prompt: str
    model_response: str
    golden_standard: str

    # --- Phase-1 results ---
    hybrid_score: float
    response_time_ms: float  # FROZEN – see __setattr__

    # --- Timestamp (ISO 8601) ---
    timestamp_completed: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    # --- Phase-3 results (populated by judge runner) ---
    judge_score: Optional[int] = None
    judge_reasoning: Optional[str] = None
    judge_latency_ms: Optional[float] = None
    judge_parse_success: Optional[bool] = None
    judge_provider_used: Optional[str] = None  # which provider actually ran

    def __post_init__(self) -> None:
        """Store an immutable copy of response_time_ms at construction time."""
        # Use object.__setattr__ to bypass our own __setattr__ guard during init.
        object.__setattr__(self, "_frozen_response_time", self.response_time_ms)

    def __setattr__(self, name: str, value: object) -> None:
        """
        Intercept attribute writes and refuse to overwrite response_time_ms
        after __post_init__ has run (i.e. after _frozen_response_time is set).

        Raises:
            ValueError: If an attempt is made to overwrite response_time_ms.
        """
        if name == "response_time_ms" and hasattr(self, "_frozen_response_time"):
            raise ValueError(
                f"response_time_ms is frozen at {self._frozen_response_time} ms "
                "and cannot be overwritten after creation."
            )
        super().__setattr__(name, value)

    @property
    def frozen_response_time_ms(self) -> float:
        """Read-only access to the originally frozen response time."""
        return self._frozen_response_time  # type: ignore[attr-defined]

    def is_complete(self) -> bool:
        """Return True when Phase-3 judge fields have been populated.

        A parse failure (judge_parse_success=False, judge_score=None) is still
        a completed Phase-3 run — the judge ran but could not extract a score.
        """
        return self.judge_parse_success is not None

    def to_final_result(self) -> Dict[str, Any]:
        """
        Serialise to a flat dict ready for JSON output or CSV merging.

        Phase-3 fields that are still None are included as None so consumers
        can detect an incomplete result rather than receiving a KeyError.
        """
        return {
            "task_id": self.task_id,
            "module_id": self.module_id,
            "task_prompt": self.task_prompt,
            "model_response": self.model_response,
            "golden_standard": self.golden_standard,
            "hybrid_score": self.hybrid_score,
            "response_time_ms": self.response_time_ms,
            "timestamp_completed": self.timestamp_completed,
            "judge_score": self.judge_score,
            "judge_reasoning": self.judge_reasoning,
            "judge_latency_ms": self.judge_latency_ms,
            "judge_parse_success": self.judge_parse_success,
            "judge_provider_used": self.judge_provider_used,
        }


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------

def save_pending(result: PendingJudgeResult, path: Path) -> None:
    """
    Write a PendingJudgeResult to a JSON file.

    Useful as a safety net for long overnight runs: if the process is killed
    after Phase 1 the pending result can be reloaded and re-judged.

    Args:
        result: The pending result to persist.
        path: Destination file path. Parent directories are created if absent.

    Raises:
        OSError: If the file cannot be created or written.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = result.to_final_result()
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.debug("Saved pending judge result: %s → %s", result.task_id, path)


def load_pending(path: Path) -> PendingJudgeResult:
    """
    Restore a PendingJudgeResult from a JSON file written by save_pending().

    Args:
        path: Path to the JSON file produced by save_pending().

    Returns:
        Reconstructed PendingJudgeResult.

    Raises:
        FileNotFoundError: If path does not exist.
        ValueError: If the JSON is missing required fields.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    raw = json.loads(path.read_text(encoding="utf-8"))
    required = {"task_id", "module_id", "task_prompt", "model_response",
                "golden_standard", "hybrid_score", "response_time_ms"}
    missing = required - raw.keys()
    if missing:
        raise ValueError(
            f"Pending result at {path} is missing required fields: {missing}"
        )

    result = PendingJudgeResult(
        task_id=raw["task_id"],
        module_id=raw["module_id"],
        task_prompt=raw["task_prompt"],
        model_response=raw["model_response"],
        golden_standard=raw["golden_standard"],
        hybrid_score=float(raw["hybrid_score"]),
        response_time_ms=float(raw["response_time_ms"]),
        timestamp_completed=raw.get("timestamp_completed", ""),
    )
    # Restore Phase-3 fields if already set
    result.judge_score = raw.get("judge_score")
    result.judge_reasoning = raw.get("judge_reasoning")
    result.judge_latency_ms = raw.get("judge_latency_ms")
    result.judge_parse_success = raw.get("judge_parse_success")
    result.judge_provider_used = raw.get("judge_provider_used")

    logger.debug("Loaded pending judge result: %s ← %s", result.task_id, path)
    return result
