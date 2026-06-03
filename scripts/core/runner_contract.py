"""Runner contract helpers for orchestrator <-> worker communication.

Provides a small, stable JSON summary channel that worker scripts can emit
and orchestrators can consume without parsing console output.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def write_run_summary(summary_path: str | None, payload: dict[str, Any]) -> None:
    """Write a structured run summary JSON if a target path is provided.

    The function is intentionally best-effort and never raises to keep worker
    scripts resilient in constrained environments.
    """
    if not summary_path:
        return

    target = Path(summary_path)
    target.parent.mkdir(parents=True, exist_ok=True)

    envelope: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "schema": "crucible.runner_summary.v1",
    }
    envelope.update(payload)

    try:
        target.write_text(json.dumps(envelope, indent=2, ensure_ascii=False), encoding="utf-8")
    except OSError:
        # Best-effort: do not fail the benchmark run on summary write issues.
        return
