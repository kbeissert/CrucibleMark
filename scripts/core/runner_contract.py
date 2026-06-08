"""Runner contract helpers for orchestrator <-> worker communication.

Provides a small, stable JSON summary channel that worker scripts can emit
and orchestrators can consume without parsing console output.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# SSoT-Konstante: Pfad zum Leaderboard-Generator, der am Ende jedes
# Benchmark-Scripts (Sub-Worker) ausgeführt wird. Architektur-Regel:
# Jedes Sub-Worker-Script ist für sein eigenes Leaderboard-Update verantwortlich.
# Der Auto-Orchestrator (make benchmark-auto) triggert KEIN zusätzliches
# `make leaderboard` am Ende, weil die Sub-Worker das schon getan haben.
LEADERBOARD_GENERATOR = "scripts/core/generate_leaderboard.py"


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


def update_leaderboard(root_dir: Path | None = None) -> bool:
    """Regeneriert das Benchmark-Leaderboard aus den aktuellen CSVs.

    Wird am Ende jedes Benchmark-Scripts (Sub-Worker) aufgerufen, damit das
    Leaderboard die frischesten Werte spiegelt. Best-Effort: wirft keine
    Exception, damit ein fehlgeschlagenes Leaderboard-Update den Benchmark-
    Run nie abbricht.

    Args:
        root_dir: Projekt-Root (Default: Parent von scripts/core/runner_contract.py).

    Returns:
        True wenn das Leaderboard erfolgreich regeneriert wurde, False sonst.
    """
    cwd = root_dir or Path(__file__).resolve().parents[2]
    try:
        result = subprocess.run(
            [sys.executable, LEADERBOARD_GENERATOR],
            cwd=str(cwd),
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"   [WARN] Leaderboard-Update konnte nicht gestartet werden: {exc}")
        return False

    if result.returncode != 0:
        # Nur die letzten paar Zeilen zeigen, um Spam zu vermeiden
        stderr_tail = (result.stderr or "").strip().splitlines()[-3:]
        print(
            "   [WARN] Leaderboard-Update fehlgeschlagen "
            f"(exit={result.returncode}): {' | '.join(stderr_tail) or 'kein stderr'}"
        )
        return False

    print("   📊 Leaderboard aktualisiert → benchmark_leaderboard.csv")
    return True
